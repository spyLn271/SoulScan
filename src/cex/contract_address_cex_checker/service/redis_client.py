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

    def rebuild_contract_index(self, all_exchange_data: Dict[str, List[CoinEntry]]) -> None:
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

        Uses a temporary key + atomic rename for zero-downtime updates.

        Safety (PRC-01): if a rebuild produced NO entries at all (every fetch failed),
        the swap is SKIPPED and the previous index kept — stale-but-present beats
        blanking lookups. Logged at WARNING so a total failure is visible.
        """
        temp_key = f"{REDIS_CONFIG.contract_index_key}:temp"

        index: Dict[str, Dict[str, str]] = {}
        counts: Dict[str, Dict[str, int]] = {}

        for exchange_name, entries in all_exchange_data.items():
            market_symbols = self._load_market_symbols(exchange_name)
            with_addr = 0          # entries that yielded a canonical address
            tradable = 0           # entries that also resolved to a tradable base
            for entry in entries:
                net = canonical.canonical_network(entry.network)
                addr = canonical.canonical_address(net, entry.contract_address, entry.coin)
                if not addr:
                    continue  # no usable address (e.g. native on an unsupported net)
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
            counts[exchange_name] = {
                "fetched": len(entries), "with_address": with_addr, "tradable": tradable,
            }

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
