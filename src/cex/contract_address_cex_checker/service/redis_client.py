"""
Redis client for storing and retrieving exchange data.
"""
import json
import time
from typing import Dict, List, Optional, Set
import redis

from .config import REDIS_CONFIG
from .exchanges.base import CoinEntry
from . import canonical
from src.logger_handler.logger import get_logger


logger = get_logger("cex-Contracts.redis_client")

_EVM_HEX = set("0123456789abcdefABCDEF")


def _normalize_address(addr: str) -> str:
    """EVM addresses are case-insensitive hex (`0x` + 40 hex chars) — lowercase
    them so different casings collide on the same index entry. Solana base58
    and other non-EVM formats are case-sensitive: preserve them verbatim."""
    if len(addr) == 42 and addr.startswith("0x") and all(c in _EVM_HEX for c in addr[2:]):
        return addr.lower()
    return addr


class RedisClient:
    """Redis operations for cex data storage and lookup."""

    def __init__(self):
        self.client = redis.Redis(
            host=REDIS_CONFIG.host,
            port=REDIS_CONFIG.port,
            db=REDIS_CONFIG.db,
            password=REDIS_CONFIG.password,
            decode_responses=True
        )

    def store_exchange_data(self, exchange_name: str, entries: List[CoinEntry]) -> None:
        """Store raw exchange data as idl."""
        key = REDIS_CONFIG.exchange_data_key.format(exchange=exchange_name)
        data = [e.to_dict() for e in entries]
        self.client.set(key, json.dumps(data))

        # Update timestamp
        ts_key = REDIS_CONFIG.last_update_key.format(exchange=exchange_name)
        self.client.set(ts_key, str(int(time.time())))

    def load_exchange_data(self, exchange_name: str) -> Optional[List[CoinEntry]]:
        """Load an exchange's LAST-GOOD raw data (from a prior successful cycle).

        Used as a fallback when the current cycle's fetch failed, so one transient
        failure (bad key, rate-limit) doesn't drop the whole exchange from the
        index. Returns None if no cached data exists yet."""
        key = REDIS_CONFIG.exchange_data_key.format(exchange=exchange_name)
        raw = self.client.get(key)
        if not raw:
            return None
        try:
            return [CoinEntry(**d) for d in json.loads(raw)]
        except (ValueError, TypeError) as e:
            logger.warning("Could not parse cached data for %s: %s", exchange_name, e)
            return None

    def _load_market_symbols(self, exchange_name: str) -> Set[str]:
        """Return the set of tradable symbols for an exchange — the FIELD names of
        its ``spot-market-data:{exchange}`` hash (e.g. {"SOLUSDT","BTCUSDT"}).

        This is the authoritative "what does this exchange actually trade" universe,
        populated by the market-data service. Used to validate that a resolved base
        is really tradable before it enters the index. Returns an empty set if the
        hash is missing (exchange's market data not yet populated)."""
        try:
            keys = self.client.hkeys(f"spot-market-data:{exchange_name}")
            # drop the metadata field(s) like "_version"
            return {k for k in keys if not k.startswith("_")}
        except Exception as e:
            logger.warning("Could not load market symbols for %s: %s", exchange_name, e)
            return set()

    def rebuild_contract_index(
        self,
        all_exchange_data: Dict[str, List[CoinEntry]],
        backfill_exchanges: Optional[Set[str]] = None,
        min_witnesses: int = 2,
        price_match: bool = True,
        price_match_max_deviation: float = 0.15,
        price_match_stream_max_age: int = 300,
    ) -> None:
        """
        Rebuild the contract address index from all exchange data.

        Index shape:  ``{network}:{canonical_address}``  ->  ``{exchange: base_symbol}``
        where ``base_symbol`` is the TRADABLE base (validated against the exchange's
        ``spot-market-data`` universe), so the engine can build
        ``stream:orderbook:{exchange}:spot:{base}{QUOTE}`` directly.

        Network + address are canonicalized (see ``canonical.py``):
        - the 5 SoulScan chains (eth/base/arbitrum/bsc/solana) get canonical keys;
          other networks are kept under an ``x-<slug>`` key so coverage isn't lost;
        - EVM native+wrapped collapse to ``{chain}:0x000…000``; Solana native SOL to
          ``solana:<WSOL mint>``.

        Two phases:
        - **Phase 1** (address-bearing exchanges): build the address-keyed index and
          a witness map ``(net, COIN) -> {key -> set(exchange)}``.
        - **Phase 2** (``backfill_exchanges`` — exchanges that expose no contract
          address, e.g. LBank): attach each tradable token to the SINGLE address that
          other exchanges resolved for ``(canonical_network, wallet-coin)``, but ONLY
          when ``>= min_witnesses`` independent exchanges agree on that address.
          Back-fill never creates a key; ambiguous (>1 address) and below-threshold
          matches are skipped and logged.

        Uses a temporary key + atomic rename for zero-downtime updates.

        Safety (PRC-01): if a rebuild produced NO entries at all (every fetch failed),
        the swap is SKIPPED and the previous index kept — stale-but-present beats
        blanking lookups. Logged at WARNING so a total failure is visible.
        """
        backfill = backfill_exchanges or set()
        temp_key = f"{REDIS_CONFIG.contract_index_key}:temp"

        index: Dict[str, Dict[str, str]] = {}
        # (net, COIN) -> {index_key -> set(exchange)}: which exchanges resolved a
        # given (chain, wallet-coin) to which address(es) — the back-fill witnesses.
        coin_to_keys: Dict[tuple, Dict[str, Set[str]]] = {}
        counts: Dict[str, Dict[str, int]] = {}

        def _register(net: str, coin_upper: str, key: str, exchange: str) -> None:
            coin_to_keys.setdefault((net, coin_upper), {}).setdefault(key, set()).add(exchange)

        # ---- Phase 1: address-bearing exchanges build the index + witness map ----
        # Back-fill exchanges are EXCLUDED here (load-bearing): their entries carry no
        # address, and an address-less EVM entry would otherwise resolve to the chain
        # native sentinel and poison the native key.
        for exchange_name, entries in all_exchange_data.items():
            if exchange_name in backfill:
                continue
            market_symbols = self._load_market_symbols(exchange_name)
            with_addr = 0          # entries that yielded a canonical address
            tradable = 0           # entries that also resolved to a tradable base
            for entry in entries:
                resolved = canonical.resolve_entry(entry.network, entry.contract_address, entry.coin)
                if not resolved:
                    continue  # no usable (network, address) to key on
                net, addr = resolved
                with_addr += 1

                # Resolve the tradable base from this exchange's market universe.
                # If market data is absent for the exchange, fall back to the raw
                # coin so we don't lose the whole exchange to an empty hash.
                if market_symbols:
                    base = canonical.resolve_tradable_base(market_symbols, entry.coin)
                    if not base:
                        continue  # listed in wallet config but not actually tradable
                else:
                    base = entry.coin.upper()
                tradable += 1

                key = canonical.make_index_key(net, addr)
                index.setdefault(key, {})[exchange_name] = base
                _register(net, entry.coin.upper(), key, exchange_name)
                # Native keys: also register under the chain's native+wrapped symbols
                # so a back-fill source naming the native (e.g. SOL) matches even when
                # the only native producer filed it as wallet-coin WSOL/WETH/WBNB.
                if addr in (canonical.EVM_NATIVE_ADDRESS, canonical.WSOL_MINT):
                    for sym in canonical.native_symbols(net):
                        _register(net, sym, key, exchange_name)
            counts[exchange_name] = {
                "fetched": len(entries), "with_address": with_addr, "tradable": tradable,
            }

        # ---- Phase 2: back-fill-only exchanges attach to existing addresses ----
        for exchange_name in backfill:
            entries = all_exchange_data.get(exchange_name)
            if not entries:
                continue
            market_symbols = self._load_market_symbols(exchange_name)
            if not market_symbols:
                # No tradable universe to validate against — refuse to guess bases
                # (raw-coin attachment would point the engine at non-existent streams).
                logger.warning(
                    "Back-fill skipped for %s: no spot-market-data (cannot validate "
                    "tradable bases). %d entries unused this cycle.",
                    exchange_name, len(entries),
                )
                counts[exchange_name] = {
                    "fetched": len(entries), "attached": 0, "no_market_data": 1,
                }
                continue
            attached = unmatched = ambiguous = low_witness = not_tradable = 0
            x_chains: Set[str] = set()
            for entry in entries:
                net = canonical.canonical_network(entry.network)
                if net.startswith("x-"):
                    x_chains.add(entry.network)
                base = canonical.resolve_tradable_base(market_symbols, entry.coin)
                if not base:
                    not_tradable += 1
                    continue
                m = coin_to_keys.get((net, entry.coin.upper()))
                if not m:
                    unmatched += 1
                    continue
                if len(m) > 1:
                    ambiguous += 1
                    logger.debug(
                        "Back-fill %s %s/%s ambiguous: %d addresses %s — skipped",
                        exchange_name, entry.coin, net, len(m), list(m.keys()),
                    )
                    continue
                key, witnesses = next(iter(m.items()))
                if len(witnesses) < min_witnesses:
                    low_witness += 1
                    logger.debug(
                        "Back-fill %s %s/%s -> %s below threshold: %d witness(es) %s < %d — skipped",
                        exchange_name, entry.coin, net, key, len(witnesses),
                        sorted(witnesses), min_witnesses,
                    )
                    continue
                index[key][exchange_name] = base
                attached += 1
                logger.debug(
                    "Back-fill attached %s:%s -> %s as %s (witnesses=%s)",
                    exchange_name, entry.coin, key, base, sorted(witnesses),
                )
            counts[exchange_name] = {
                "fetched": len(entries), "attached": attached, "unmatched": unmatched,
                "ambiguous": ambiguous, "low_witness": low_witness, "not_tradable": not_tradable,
            }
            if x_chains:
                logger.info(
                    "Back-fill %s: %d chain string(s) outside SoulScan networks kept as "
                    "x-* (not matched): %s", exchange_name, len(x_chains), sorted(x_chains),
                )
            logger.info(
                "Back-fill %s: attached=%d unmatched=%d ambiguous=%d low_witness=%d "
                "not_tradable=%d (min_witnesses=%d)",
                exchange_name, attached, unmatched, ambiguous, low_witness,
                not_tradable, min_witnesses,
            )

        # ---- Phase 2.5: price-fingerprint matching (fill producer gaps by order-book price) ----
        if price_match:
            try:
                self._price_match_fill(index, price_match_max_deviation, price_match_stream_max_age)
            except Exception as e:
                logger.warning("price-match phase failed (non-fatal): %s", e)

        logger.info(
            "Contract index rebuild: %d unique (network:address) keys across %d exchanges | per-exchange %s",
            len(index), len(all_exchange_data), counts,
        )

        if not index:
            logger.warning(
                "Contract index rebuild produced 0 entries — SKIPPING swap, keeping "
                "previous index to avoid blanking lookups. per-exchange %s", counts,
            )
            self.client.delete(temp_key)
            return

        pipe = self.client.pipeline()
        pipe.delete(temp_key)
        for key, exchange_map in index.items():
            pipe.hset(temp_key, key, json.dumps(exchange_map))
        # Freshness stamp (reserved field; "_version" never collides with a key).
        pipe.hset(temp_key, "_version", str(int(time.time())))
        pipe.rename(temp_key, REDIS_CONFIG.contract_index_key)
        pipe.execute()

    def _stream_mid(self, exchange: str, base: str, max_age_s: float) -> Optional[float]:
        """Fresh top-of-book mid for (exchange, base) from its order-book stream, or None.
        Tries USDT then USDC; ignores entries older than max_age_s so we never price-match
        on stale data."""
        now_ms = int(time.time() * 1000)
        for quote in canonical.QUOTE_ASSETS:
            key = f"stream:orderbook:{exchange}:spot:{base}{quote}"
            try:
                entries = self.client.xrevrange(key, count=1)
            except Exception:
                continue
            if not entries:
                continue
            fields = entries[0][1]
            ts = fields.get("timestamp_ms")
            try:
                if (now_ms - int(float(ts))) / 1000.0 > max_age_s:
                    continue
            except (TypeError, ValueError):
                continue
            try:
                bids = json.loads(fields.get("bids", "[]"))
                asks = json.loads(fields.get("asks", "[]"))
                if bids and asks:
                    bid = float(bids[0][0]); ask = float(asks[0][0])
                    if bid > 0 and ask > 0:
                        return (bid + ask) / 2.0
            except (ValueError, TypeError, IndexError):
                continue
        return None

    def _price_match_fill(self, index: Dict[str, Dict[str, str]],
                          max_deviation: float, max_age_s: float) -> None:
        """Phase 2.5: resolve a producer exchange's tradable symbol that its wallet API
        left uncovered by matching its order-book mid-price to an address other exchanges
        already resolved for the same base. Same token -> prices agree within max_deviation;
        ticker collisions differ by orders of magnitude so only the right address matches.
        Fill-gaps only: never overrides an existing (exchange, base) resolved upstream."""
        mid_cache: Dict[tuple, Optional[float]] = {}

        def mid(ex: str, base: str) -> Optional[float]:
            ck = (ex, base)
            if ck not in mid_cache:
                mid_cache[ck] = self._stream_mid(ex, base, max_age_s)
            return mid_cache[ck]

        # (exchange, base) already resolved by wallet API / witness back-fill.
        resolved = {(ex, base) for exmap in index.values() for ex, base in exmap.items()}

        # Producer (exchange, base) universe from live order-book stream keys.
        ex_bases: Dict[str, Set[str]] = {}
        for sk in self.client.scan_iter(match="stream:orderbook:*:spot:*", count=2000):
            parts = sk.split(":")
            if len(parts) < 5:
                continue
            ex, suffix = parts[2], parts[4]
            base, quote = canonical.split_stream_symbol(suffix)
            if quote in canonical.QUOTE_ASSETS:
                ex_bases.setdefault(ex, set()).add(base)

        gaps = [(ex, base) for ex, bases in ex_bases.items()
                for base in bases if (ex, base) not in resolved]
        if not gaps:
            logger.info("price-match: no producer gaps to resolve")
            return
        needed_bases = {b for _, b in gaps}

        # Candidate addresses (with a median reference mid) per base we need to resolve.
        base_to_cand: Dict[str, list] = {}
        for key, exmap in index.items():
            bases = set(exmap.values()) & needed_bases
            if not bases:
                continue
            refs = list(exmap.keys())
            for base in bases:
                ref_mids = sorted(m for m in (mid(rx, base) for rx in refs) if m)
                if ref_mids:
                    base_to_cand.setdefault(base, []).append((key, ref_mids[len(ref_mids) // 2]))

        stats: Dict[str, Dict[str, int]] = {}

        def bump(ex: str, field: str) -> None:
            stats.setdefault(ex, {"matched": 0, "no_candidate": 0,
                                  "no_fresh_price": 0, "rejected": 0})[field] += 1

        for ex, base in gaps:
            cands = base_to_cand.get(base)
            if not cands:
                bump(ex, "no_candidate"); continue
            em = mid(ex, base)
            if em is None:
                bump(ex, "no_fresh_price"); continue
            matched = False
            for key, ref_price in cands:
                if ex in index[key]:
                    continue
                hi, lo = (em, ref_price) if em >= ref_price else (ref_price, em)
                if lo > 0 and hi / lo <= 1.0 + max_deviation:
                    index[key][ex] = base  # E trades this token (price confirms identity)
                    matched = True
            bump(ex, "matched" if matched else "rejected")

        total = sum(s["matched"] for s in stats.values())
        logger.info("price-match: filled %d (exchange,address) symbol-gaps | per-exchange %s",
                    total, stats)

    def lookup_contract(self, network: str, contract_address: str) -> Optional[Dict[str, str]]:
        """
        Look up a token by (network, address) and return the exchanges that trade
        it plus the tradable base symbol each uses.

        Args:
            network: raw or canonical network name (normalized internally)
            contract_address: on-chain address / mint

        Returns:
            Dict of {exchange_name: base_symbol} or None if not found.
        """
        net = canonical.canonical_network(network)
        addr = canonical.canonical_address(net, contract_address, "")
        if not addr:
            return None
        key = canonical.make_index_key(net, addr)
        result = self.client.hget(REDIS_CONFIG.contract_index_key, key)
        if result:
            return json.loads(result)
        return None

    def get_index_stats(self) -> Dict:
        """Get statistics about the contract index."""
        return {
            "total_contracts": self.client.hlen(REDIS_CONFIG.contract_index_key),
        }

    def get_last_update(self, exchange_name: str) -> Optional[int]:
        """Get the last update timestamp for an exchange."""
        ts_key = REDIS_CONFIG.last_update_key.format(exchange=exchange_name)
        result = self.client.get(ts_key)
        return int(result) if result else None
