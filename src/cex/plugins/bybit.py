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
            remove = True

        if remove:
            side.pop(p, None)
        else:
            side[p] = q


class BybitSpotConnector(OrderBookConnector):
    def __init__(
            self,
            worker_id: int = None,
            num_workers: int = None
    ):
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
                "topic": "mergedDepth",
                "event": "sub",
                "symbol": s,
                "limit": self.limit,
                "params": {"binary": False, "dumpScale": ds.get(s, self.default_ds)},
            }))

        self.logger.info("SUBSCRIBE %d symbols (mergedDepth)", len(syms))

    async def ping_message(self) -> Optional[str]:
        return _json.dumps({"ping": int(time.time() * 1000)})

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

        return [
            Book(
                symbol=self.normalize_symbol(sym),
                bids=d.get("b", []),
                asks=d.get("a", []),
                event_ts_ms=d.get("t")
            )
        ]



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
        kw["origin"] = "https://www.bybit.com"
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
        b1, a1 = data.get("b1"), data.get("a1")
        drift = ((b1 and (not bids or float(bids[0][0]) != float(b1))) or
                 (a1 and (not asks or float(asks[0][0]) != float(a1))))
        if mtype == "delta" and drift:
            st["synced"] = False
            _m.OB_GAPS.labels(self.exchange, self.market_type).inc()
            self.logger.warning(
                "orderbook drift %s top=%s/%s vs b1/a1=%s/%s -> resync",
                sym,
                bids[0][0] if bids else None,
                asks[0][0] if asks else None,
                b1,
                a1
            )
            raise ResyncRequired(f"bybit {sym} orderbook drift")

        if not bids or not asks:
            return None

        return [
            Book(
                symbol=sym,
                bids=bids,
                asks=asks,
                event_ts_ms=m.get("ts")
            )
        ]
