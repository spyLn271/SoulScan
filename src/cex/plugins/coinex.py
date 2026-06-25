import gzip
import json as _json
import zlib
from typing import Dict, List, Optional

from src.cex.core.connector import OrderBookConnector, Book, ResyncRequired

try:
    import orjson

    def _loads(raw):
        return orjson.loads(raw)
except ImportError:
    def _loads(raw):
        return _json.loads(raw)


def _text(raw):
    if isinstance(raw, (bytes, bytearray)):
        try:
            return gzip.decompress(raw).decode("utf-8", "replace")
        except Exception:
            return bytes(raw).decode("utf-8", "replace")
    return raw


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def _rm(q) -> bool:
    try:
        return float(q) <= 0
    except (ValueError, TypeError):
        return True


def _ts(v):
    if v is None:
        return None

    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def _pairs(levels):
    for lvl in (levels or []):
        if isinstance(lvl, (list, tuple)) and len(lvl) >= 2:
            try:
                float(lvl[0])
            except (ValueError, TypeError):
                continue

            yield lvl[0], lvl[1]


def _checksum(bids_desc, asks_asc) -> int:
    parts = [f"{p}:{a}" for p, a in bids_desc] + [f"{p}:{a}" for p, a in asks_asc]
    return zlib.crc32(":".join(parts).encode())


class _CoinexBase(OrderBookConnector):
    def __init__(
            self,
            market_type: str,
            worker_id: int = None,
            num_workers: int = None
    ):
        super().__init__("coinex", market_type, worker_id=worker_id, num_workers=num_workers)

        self.depth_level = int(self.special_params.get("depth_level", 50))
        self.merge = str(self.special_params.get("merge", "0"))
        self._book: Dict[str, dict] = {}

    async def ws_url(self) -> str:
        return self.market_config["ws_url"]

    async def _connection_kwargs(self, proxied: bool) -> dict:
        kw = await super()._connection_kwargs(proxied)
        kw["compression"] = "deflate"   # ws.coinex.com REQUIRES permessage-deflate (else InvalidHandshake)
        return kw

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.upper()   # CoinEx markets are already BASE+QUOTE concat (BTCUSDT)

    async def subscribe(self, ws, symbols: List[str]) -> None:
        args = []
        for s in symbols:
            sym = self.normalize_symbol(s)
            self._book[sym] = {"b": {}, "a": {}, "synced": False}   # reset; await the clean snapshot
            args.append([sym, self.depth_level, self.merge])

        await ws.send(_json.dumps({"id": 1, "method": "depth.subscribe_multi", "params": args}))
        self.logger.info(
            "SUBSCRIBE %d symbols (depth_multi limit=%d merge=%s)",
            len(args),
            self.depth_level,
            self.merge
        )

    async def ping_message(self) -> Optional[str]:
        return _json.dumps({"id": 1, "method": "server.ping", "params": []})

    def parse(self, raw) -> Optional[List[Book]]:
        raw = _text(raw)
        try:
            m = _loads(raw)
        except (ValueError, TypeError):
            return None
        if not isinstance(m, dict) or m.get("method") != "depth.update":
            if isinstance(m, dict) and m.get("error"):
                self.logger.warning("coinex ws error: %s", str(m)[:140])
            return None

        p = m.get("params") or []
        if len(p) < 3 or not isinstance(p[1], dict) or not isinstance(p[2], str):
            return None

        clean, d, market = p[0], p[1], p[2]
        sym = self.normalize_symbol(market)
        if not sym:
            return None

        st = self._book.setdefault(sym, {"b": {}, "a": {}, "synced": False})
        if clean:                                   # full snapshot -> replace both sides
            st["b"] = {px: a for px, a in _pairs(d.get("bids"))}
            st["a"] = {px: a for px, a in _pairs(d.get("asks"))}
            st["synced"] = True
        elif st["synced"]:                          # incremental: 0-amount removes, else upsert
            for px, a in _pairs(d.get("bids")):
                st["b"].pop(px, None) if _rm(a) else st["b"].__setitem__(px, a)
            for px, a in _pairs(d.get("asks")):
                st["a"].pop(px, None) if _rm(a) else st["a"].__setitem__(px, a)
        else:
            return None

        bids_all = sorted(st["b"].items(), key=lambda kv: float(kv[0]), reverse=True)
        asks_all = sorted(st["a"].items(), key=lambda kv: float(kv[0]))
        cs = d.get("checksum")
        if cs is not None and _checksum(bids_all, asks_all) != cs:
            st["synced"] = False
            raise ResyncRequired(f"coinex {sym} checksum mismatch")

        out_b = [[p, a] for p, a in bids_all[:self.depth_level]]
        out_a = [[p, a] for p, a in asks_all[:self.depth_level]]
        if not out_b or not out_a or float(out_b[0][0]) >= float(out_a[0][0]):
            return None

        return [
            Book(
                symbol=sym,
                bids=out_b,
                asks=out_a,
                event_ts_ms=_ts(d.get("time"))
            )
        ]


class CoinexSpotConnector(_CoinexBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("spot", worker_id=worker_id, num_workers=num_workers)


class CoinexFuturesConnector(_CoinexBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("futures", worker_id=worker_id, num_workers=num_workers)
