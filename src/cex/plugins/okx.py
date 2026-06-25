import heapq
import json as _json
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


def _okx_checksum(bids_desc, asks_asc) -> int:
    parts = []
    for i in range(25):
        if i < len(bids_desc):
            parts.append(f"{bids_desc[i][0]}:{bids_desc[i][1]}")

        if i < len(asks_asc):
            parts.append(f"{asks_asc[i][0]}:{asks_asc[i][1]}")

    crc = zlib.crc32(":".join(parts).encode())
    return crc - (1 << 32) if crc >= (1 << 31) else crc


def _scale_levels(levels, mult):
    if mult == 1.0:
        return levels

    out = []
    for p, s in levels:
        try:
            out.append([p, float(s) * mult])
        except (ValueError, TypeError):
            out.append([p, s])

    return out


def _apply(side: Dict[str, str], levels) -> None:
    for lvl in (levels or []):
        if not (isinstance(lvl, (list, tuple)) and len(lvl) >= 2):
            continue

        px, sz = lvl[0], lvl[1]
        try:
            remove = float(sz) <= 0
            float(px)
        except (ValueError, TypeError):
            remove = True

        if remove:
            side.pop(px, None)
        else:
            side[px] = sz


class _OkxBase(OrderBookConnector):
    def __init__(
            self,
            market_type: str,
            worker_id: int = None,
            num_workers: int = None
    ):
        super().__init__("okx", market_type, worker_id=worker_id, num_workers=num_workers)

        self.emit_levels = int(self.special_params.get("emit_levels", 20))
        self.sub_chunk = int(self.special_params.get("sub_chunk", 50))
        self._book: Dict[str, dict] = {}        # canonical -> {"b":{px:sz}, "a":{px:sz}, "synced":bool}
        self._inst2canon: Dict[str, str] = {}   # OKX instId -> canonical symbol
        self._mult: Dict[str, float] = {}       # canonical -> ctVal (SWAP contract->base; spot stays empty -> 1.0)

    async def ws_url(self) -> str:
        return self.market_config["ws_url"]

    async def _connection_kwargs(self, proxied: bool) -> dict:
        kw = await super()._connection_kwargs(proxied)
        kw["origin"] = "https://www.okx.com"
        kw["compression"] = "deflate"
        return kw

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.upper().replace("-SWAP", "").replace("-", "")

    async def _inst_ids(self, canon_syms) -> Dict[str, str]:
        try:
            vals = await self.redis.hmget(get_market_data_key("okx", self.market_type), *canon_syms)
        except Exception:
            vals = [None] * len(canon_syms)

        out = {}
        for s, v in zip(canon_syms, vals):
            inst = None
            if v:
                try:
                    meta = _loads(v)
                    inst = meta.get("instId")
                    ctv = meta.get("ctVal")
                    if ctv is not None:
                        try:
                            cf = float(ctv)
                            if cf > 0:
                                self._mult[s] = cf
                        except (ValueError, TypeError):
                            pass

                except Exception:
                    pass

            out[s] = inst or s
        return out

    async def subscribe(self, ws, symbols: List[str]) -> None:
        instmap = await self._inst_ids(symbols)
        args = []
        for canon in symbols:
            inst = instmap[canon]
            self._inst2canon[inst] = canon
            self._book[canon] = {"b": {}, "a": {}, "synced": False}
            args.append({"channel": "books", "instId": inst})

        if not args:
            return

        for chunk in _chunks(args, self.sub_chunk):
            await ws.send(_json.dumps({"op": "subscribe", "args": chunk}))

        self.logger.info("SUBSCRIBE %d symbols (books)", len(args))

    async def ping_message(self) -> Optional[str]:
        return "ping"

    def parse(self, raw) -> Optional[List[Book]]:
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
                self.logger.warning("okx sub error: %s", str(m.get("msg"))[:140])
            return None

        arg = m.get("arg") or {}
        if arg.get("channel") != "books":
            return None

        data = m.get("data")
        if not data:
            return None

        inst = arg.get("instId")
        canon = self._inst2canon.get(inst) or self.normalize_symbol(inst or "")
        if not canon:
            return None

        d = data[0]
        st = self._book.setdefault(canon, {"b": {}, "a": {}, "synced": False})
        act = m.get("action")
        if act == "snapshot":
            st["b"] = {p: s for p, s, *_ in d.get("bids", [])}
            st["a"] = {p: s for p, s, *_ in d.get("asks", [])}
            st["synced"] = True
        elif act == "update":
            if not st["synced"]:
                return None   # gated until the first snapshot
            _apply(st["b"], d.get("bids"))
            _apply(st["a"], d.get("asks"))
        else:
            return None

        k = max(self.emit_levels, 25)
        bids = heapq.nlargest(k, st["b"].items(), key=lambda kv: float(kv[0]))
        asks = heapq.nsmallest(k, st["a"].items(), key=lambda kv: float(kv[0]))
        cs = d.get("checksum")
        if act == "update" and cs is not None and _okx_checksum(bids[:25], asks[:25]) != cs:
            st["synced"] = False
            _m.OB_GAPS.labels(self.exchange, self.market_type).inc()
            self.logger.warning("checksum mismatch %s -> resync", canon)
            raise ResyncRequired(f"okx {canon} checksum mismatch")

        mult = self._mult.get(canon, 1.0)
        out_b = _scale_levels([[p, s] for p, s in bids[:self.emit_levels]], mult)
        out_a = _scale_levels([[p, s] for p, s in asks[:self.emit_levels]], mult)
        if not out_b or not out_a:
            return None

        ts = d.get("ts")
        return [
            Book(
                symbol=canon,
                bids=out_b,
                asks=out_a,
                event_ts_ms=int(ts) if ts else None
            )
        ]


class OkxSpotConnector(_OkxBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("spot", worker_id=worker_id, num_workers=num_workers)


class OkxFuturesConnector(_OkxBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("futures", worker_id=worker_id, num_workers=num_workers)
