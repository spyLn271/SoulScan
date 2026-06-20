#!/usr/bin/env python3
"""
Bybit order books on the cex_v2 core. BOTH markets use the feeds the bybit WEBSITE renders — NOT the
raw v5 public API, whose sizes read "off" vs the site. The two feeds aggregate DIFFERENTLY:

SPOT    -> ws2 mergedDepth (wss://ws2.bybit.com/spot/ws/quote/v2): PRICE-bucketed — finer ticks are
           collapsed into per-symbol `dumpScale` price buckets (published by the market-data handler),
           sizes summed within a bucket. Full snapshot per message.
FUTURES -> realtime_w (wss://ws2.bybit.com/realtime_w): topic `orderBook_20@m1.H.<SYMBOL>`, the
           website's 20-level derivatives book. NATIVE tick prices (no price bucketing) but the @m1
           merge tier reports LARGER per-level sizes than the v5 raw book. GZIP-compressed frames;
           SNAPSHOT+DELTA (size "0" = remove) with b1/a1 best-bid/ask for an integrity check.
           Covers USDT + USDC perps.
Both keep per-symbol book state (the core is collapse-to-latest and stateless); the full book is kept
and truncated to emit_levels only at emit.
"""
import gzip
import json as _json
import time
import zlib
from typing import Dict, List, Optional

from src.cex.core.connector import OrderBookConnector, Book, ResyncRequired
from src.cex.config import get_market_data_key
from src.cex.observability import metrics as _m

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


def _gunzip(b) -> str:
    try:
        return gzip.decompress(b).decode("utf-8", "replace")
    except Exception:
        return zlib.decompressobj(47).decompress(b).decode("utf-8", "replace")


def _to_map(levels) -> Dict[str, str]:
    out = {}
    for lvl in levels or []:
        if isinstance(lvl, (list, tuple)) and len(lvl) >= 2:
            out[lvl[0]] = lvl[1]
    return out


def _apply(side: Dict[str, str], levels) -> None:
    for lvl in (levels or []):
        if not (isinstance(lvl, (list, tuple)) and len(lvl) >= 2):
            continue
        p, q = lvl[0], lvl[1]
        try:
            remove = float(q) <= 0
        except (ValueError, TypeError):
            remove = True   # unparseable size -> treat as a removal (never keep a corrupt level)
        if remove:
            side.pop(p, None)
        else:
            side[p] = q


# ============================================================ SPOT — ws2 mergedDepth (full snapshot)
class BybitSpotConnector(OrderBookConnector):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("bybit", "spot", worker_id=worker_id, num_workers=num_workers)
        self.limit = int(self.special_params.get("limit", 40))
        self.default_ds = int(self.special_params.get("default_dump_scale", 4))

    async def ws_url(self) -> str:
        return f"{self.market_config['ws_url']}?_platform=2&tamp={int(time.time() * 1000)}"

    async def _dump_scales(self, symbols) -> Dict[str, int]:
        try:
            vals = await self.redis.hmget(get_market_data_key("bybit", "spot"), *symbols)
        except Exception:
            vals = [None] * len(symbols)
        out = {}
        for s, v in zip(symbols, vals):
            ds = self.default_ds
            if v:
                try:
                    ds = int(_loads(v).get("dumpScale", self.default_ds))
                except Exception:
                    pass
            out[s] = ds
        return out

    async def subscribe(self, ws, symbols: List[str]) -> None:
        syms = [self.normalize_symbol(s) for s in symbols]
        ds = await self._dump_scales(syms)
        for s in syms:
            await ws.send(_json.dumps({
                "topic": "mergedDepth", "event": "sub", "symbol": s, "limit": self.limit,
                "params": {"binary": False, "dumpScale": ds.get(s, self.default_ds)},
            }))
        self.logger.info("SUBSCRIBE %d symbols (mergedDepth)", len(syms))

    async def ping_message(self) -> Optional[str]:
        return _json.dumps({"ping": int(time.time() * 1000)})  # ws2 ping format

    def parse(self, raw) -> Optional[List[Book]]:
        try:
            m = _loads(raw)
        except (ValueError, TypeError):
            return None
        if "pong" in m:
            return None
        if m.get("topic") != "mergedDepth":
            if m.get("desc"):
                self.logger.warning("ws2 sub error: %s", str(m.get("desc"))[:120])
            return None
        data = m.get("data")
        if not data:
            return None
        d = data[0] if isinstance(data, list) else data
        sym = d.get("s")
        if not sym:
            return None
        return [Book(symbol=self.normalize_symbol(sym), bids=d.get("b", []), asks=d.get("a", []),
                     event_ts_ms=d.get("t"))]


# ============================================================ FUTURES — realtime_w aggregated book
class BybitFuturesConnector(OrderBookConnector):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("bybit", "futures", worker_id=worker_id, num_workers=num_workers)
        self.depth = int(self.special_params.get("depth", 20))
        self.merge = self.special_params.get("merge", "m1")     # @m1 grouping (website default)
        self.tier = self.special_params.get("tier", "H")        # .H. precision tier
        self.emit_levels = int(self.special_params.get("emit_levels", 20))
        self.sub_chunk = int(self.special_params.get("sub_chunk", 10))
        self._book: Dict[str, dict] = {}   # {SYM: {"b":{px:sz},"a":{px:sz},"synced":bool}}

    async def ws_url(self) -> str:
        return f"{self.market_config['ws_url']}?v=1&timestamp={int(time.time() * 1000)}"

    async def _connection_kwargs(self, proxied: bool) -> dict:
        kw = await super()._connection_kwargs(proxied)
        kw["origin"] = "https://www.bybit.com"   # match the browser (cloudfront-fronted)
        return kw

    def _topic(self, sym: str) -> str:
        return f"orderBook_{self.depth}@{self.merge}.{self.tier}.{sym}"

    async def subscribe(self, ws, symbols: List[str]) -> None:
        args = []
        for s in symbols:
            sym = self.normalize_symbol(s)
            self._book[sym] = {"b": {}, "a": {}, "synced": False}   # reset for a clean resync
            args.append(self._topic(sym))
        if not args:
            return
        for chunk in _chunks(args, self.sub_chunk):
            await ws.send(_json.dumps({"op": "subscribe", "args": chunk}))
        self.logger.info("SUBSCRIBE %d symbols (realtime_w %s@%s)", len(args), self.depth, self.merge)

    async def ping_message(self) -> Optional[str]:
        return _json.dumps({"op": "ping", "args": [int(time.time() * 1000)]})

    def parse(self, raw) -> Optional[List[Book]]:
        if isinstance(raw, (bytes, bytearray)):   # data frames are gzip; acks/pong are text
            try:
                raw = _gunzip(raw)
            except Exception:
                return None
        try:
            m = _loads(raw)
        except (ValueError, TypeError):
            return None
        if not isinstance(m, dict):
            return None
        if m.get("success") is False:   # subscribe rejected -> surface it (mirrors spot's desc logging)
            self.logger.warning("realtime_w sub error: %s", str(m.get("ret_msg"))[:120])
            return None
        topic = m.get("topic", "")
        if not topic.startswith("orderBook_"):
            return None  # pong / subscribe ack / instrument_info / other
        data = m.get("data")
        if not isinstance(data, dict):
            return None
        sym = data.get("s")
        if not sym:
            return None
        sym = self.normalize_symbol(sym)
        st = self._book.setdefault(sym, {"b": {}, "a": {}, "synced": False})
        mtype = m.get("type")
        if mtype == "snapshot":
            st["b"] = _to_map(data.get("b"))
            st["a"] = _to_map(data.get("a"))
            st["synced"] = True
        elif mtype == "delta":
            if not st["synced"]:
                return None
            _apply(st["b"], data.get("b"))
            _apply(st["a"], data.get("a"))
        else:
            return None
        n = self.emit_levels
        bids = [[p, q] for p, q in sorted(st["b"].items(), key=lambda kv: float(kv[0]), reverse=True)[:n]]
        asks = [[p, q] for p, q in sorted(st["a"].items(), key=lambda kv: float(kv[0]))[:n]]
        # integrity check: realtime_w deltas carry b1/a1 (true best bid/ask) — if our merged top drifts
        # from it (OR a side is empty while b1/a1 says it shouldn't be), we missed an update -> drop state
        # + reconnect for a fresh snapshot. NOTE: must check the EMPTY-side case (not `bids and ...`),
        # else a delta that empties a side bypasses the guard and we'd emit a stranded one-sided book.
        b1, a1 = data.get("b1"), data.get("a1")
        drift = ((b1 and (not bids or float(bids[0][0]) != float(b1))) or
                 (a1 and (not asks or float(asks[0][0]) != float(a1))))
        if mtype == "delta" and drift:
            st["synced"] = False
            _m.OB_GAPS.labels(self.exchange, self.market_type).inc()
            self.logger.warning("orderbook drift %s top=%s/%s vs b1/a1=%s/%s -> resync",
                                sym, bids[0][0] if bids else None, asks[0][0] if asks else None, b1, a1)
            raise ResyncRequired(f"bybit {sym} orderbook drift")
        if not bids or not asks:
            return None  # never emit a one-sided/empty book (would strand a consumer at 0 depth)
        return [Book(symbol=sym, bids=bids, asks=asks, event_ts_ms=m.get("ts"))]
