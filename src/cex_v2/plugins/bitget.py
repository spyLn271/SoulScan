#!/usr/bin/env python3
"""
Bitget order books on the cex_v2 core — spot AND futures — via the DOCUMENTED v2 public `books`
channel (wss://ws.bitget.com/v2/ws/public).

VERIFIED 2026-06-16 (live, 8 symbols across price scales, both markets, ~40s parallel maintenance):
the v2 `books` channel is byte-for-byte identical (numerically) to the feed the Bitget WEBSITE renders
(its v1 `stream` `depth` channel at scale=tick) — 100.0000% on every stable level, 0 persistent diffs.
v2 is preferred: documented/current (no v1-deprecation risk), deeper (200 spot / 500 futures), plain
text (no gzip), shares the v2 REST family used by the market-data handler, and carries `seq`/`pseq`
sequence numbers for gap detection.

SNAPSHOT+UPDATE incremental (size "0" = remove). INTEGRITY: each update carries `seq` (this book
version) and `pseq` (the previous version); if our last seq != incoming pseq we missed an update ->
ResyncRequired -> the core reconnects+resubscribes -> fresh snapshot. (Validated live: 120/120 updates
chained, 0 broken.) The connector is collapse-to-latest/stateless, so the plugin keeps per-symbol book
state and emits a full top-N Book each frame.

Symbols are plain (BTCUSDT spot; BTCUSDT USDT-perp; <BASE>PERP USDC-perp) — no canonical remap needed.
The only per-symbol lookup is the FUTURES product line (instType): USDT perps subscribe under
"USDT-FUTURES", USDC perps under "USDC-FUTURES"; the market-data handler publishes each symbol's
instType as a field and this plugin reads it (hmget) to build the subscribe.
"""
import heapq
import json as _json
from typing import Dict, List, Optional

from src.cex_v2.core.connector import OrderBookConnector, Book, ResyncRequired
from src.cex_v2.config import get_market_data_key
from src.cex_v2.observability import metrics as _m

try:
    import orjson

    def _loads(raw):
        return orjson.loads(raw)
except ImportError:
    def _loads(raw):
        return _json.loads(raw)


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def _apply(side: Dict[str, str], levels) -> None:
    for lvl in (levels or []):
        if not (isinstance(lvl, (list, tuple)) and len(lvl) >= 2):
            continue
        px, sz = lvl[0], lvl[1]
        try:
            remove = float(sz) <= 0
            float(px)       # validate price is numeric (a corrupt px would crash the heapq sort later)
        except (ValueError, TypeError):
            remove = True   # unparseable price/size -> drop the level (never keep a corrupt entry)
        if remove:
            side.pop(px, None)
        else:
            side[px] = sz


class _BitgetBase(OrderBookConnector):
    def __init__(self, market_type: str, worker_id: int = None, num_workers: int = None):
        super().__init__("bitget", market_type, worker_id=worker_id, num_workers=num_workers)
        self.emit_levels = int(self.special_params.get("emit_levels", 20))
        self.sub_chunk = int(self.special_params.get("sub_chunk", 50))
        self._book: Dict[str, dict] = {}   # SYM -> {"b":{px:sz},"a":{px:sz},"synced":bool,"seq":int|None}

    async def ws_url(self) -> str:
        return self.market_config["ws_url"]

    async def ping_message(self) -> Optional[str]:
        return "ping"   # Bitget v2 literal-text ping; server replies "pong"

    async def _inst_types(self, symbols) -> Dict[str, str]:
        """SYM -> v2 instType for the subscribe. Spot is always SPOT; futures vary by product line
        (USDT-FUTURES / USDC-FUTURES), published per-symbol by the market-data handler."""
        return {s: "SPOT" for s in symbols}

    async def subscribe(self, ws, symbols: List[str]) -> None:
        itypes = await self._inst_types(symbols)
        args = []
        for s in symbols:
            self._book[s] = {"b": {}, "a": {}, "synced": False, "seq": None}   # reset for a clean resync
            args.append({"instType": itypes[s], "channel": "books", "instId": s})
        if not args:
            return
        for chunk in _chunks(args, self.sub_chunk):
            await ws.send(_json.dumps({"op": "subscribe", "args": chunk}))
        self.logger.info("SUBSCRIBE %d symbols (v2 books)", len(args))

    def parse(self, raw) -> Optional[List[Book]]:
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", "replace")
        if raw == "pong":
            return None
        try:
            m = _loads(raw)
        except (ValueError, TypeError):
            return None
        if not isinstance(m, dict):
            return None
        if m.get("event"):
            if m.get("event") == "error":
                self.logger.warning("bitget sub error: %s", str(m.get("msg") or m.get("arg"))[:140])
            return None
        arg = m.get("arg") or {}
        if arg.get("channel") != "books":
            return None
        data = m.get("data")
        if not data:
            return None
        sym = self.normalize_symbol(arg.get("instId") or "")
        if not sym:
            return None
        d = data[0]
        st = self._book.setdefault(sym, {"b": {}, "a": {}, "synced": False, "seq": None})
        act = m.get("action")
        if act == "snapshot":
            st["b"] = {p: s for p, s, *_ in d.get("bids", [])}
            st["a"] = {p: s for p, s, *_ in d.get("asks", [])}
            st["synced"] = True
            st["seq"] = d.get("seq")
        elif act == "update":
            if not st["synced"]:
                return None   # gated until the first snapshot
            pseq = d.get("pseq")
            # gap detection: this update's pseq must equal our last seq, else we missed one -> resync.
            if pseq is not None and st["seq"] is not None and pseq != st["seq"]:
                st["synced"] = False
                _m.OB_GAPS.labels(self.exchange, self.market_type).inc()
                self.logger.warning("seq gap %s (have %s, pseq %s) -> resync", sym, st["seq"], pseq)
                raise ResyncRequired(f"bitget {sym} seq gap")
            _apply(st["b"], d.get("bids"))
            _apply(st["a"], d.get("asks"))
            st["seq"] = d.get("seq")
        else:
            return None
        # top-k by price WITHOUT a full sort: nlargest(bids)/nsmallest(asks) is O(n) for small k.
        n = self.emit_levels
        bids = heapq.nlargest(n, st["b"].items(), key=lambda kv: float(kv[0]))   # descending
        asks = heapq.nsmallest(n, st["a"].items(), key=lambda kv: float(kv[0]))  # ascending
        out_b = [[p, s] for p, s in bids]
        out_a = [[p, s] for p, s in asks]
        if not out_b or not out_a:
            return None   # never emit a one-sided/empty book
        ts = d.get("ts")
        return [Book(symbol=sym, bids=out_b, asks=out_a, event_ts_ms=int(ts) if ts else None)]


class BitgetSpotConnector(_BitgetBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("spot", worker_id=worker_id, num_workers=num_workers)


class BitgetFuturesConnector(_BitgetBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("futures", worker_id=worker_id, num_workers=num_workers)
        self.default_inst_type = self.special_params.get("default_inst_type", "USDT-FUTURES")

    async def _inst_types(self, symbols) -> Dict[str, str]:
        try:
            vals = await self.redis.hmget(get_market_data_key("bitget", "futures"), *symbols)
        except Exception:
            vals = [None] * len(symbols)
        out = {}
        for s, v in zip(symbols, vals):
            it = None
            if v:
                try:
                    it = _loads(v).get("instType")
                except Exception:
                    pass
            out[s] = it or self.default_inst_type   # best-effort fallback (md not yet populated)
        return out
