import gzip
import heapq
import json as _json
from typing import Dict, List, Optional

from src.cex.core.connector import OrderBookConnector, Book
from src.cex.config import get_market_data_key

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


def _scale(levels, mult):
    if mult == 1.0:
        return levels
    out = []

    for lvl in levels:
        try:
            out.append([lvl[0], float(lvl[1]) * mult])
        except (ValueError, TypeError, IndexError):
            out.append(lvl)

    return out


def _topn(levels, n, reverse):
    good = [lvl for lvl in levels if len(lvl) >= 2 and _isnum(lvl[0])]
    return (
        heapq.nlargest(n, good, key=lambda l: float(l[0])) if reverse
            else heapq.nsmallest(n, good, key=lambda l: float(l[0]))
    )


def _isnum(v) -> bool:
    try:
        float(v)
        return True
    except (ValueError, TypeError):
        return False


class _HtxBase(OrderBookConnector):
    def __init__(
            self,
            market_type: str,
            worker_id: int = None,
            num_workers: int = None
    ):
        super().__init__("htx", market_type, worker_id=worker_id, num_workers=num_workers)
        self.depth_level = int(self.special_params.get("depth_level", 50))
        self._mult: Dict[str, float] = {}

    async def ws_url(self) -> str:
        return self.market_config["ws_url"]

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.upper().replace("-", "")   # btcusdt / BTC-USDT -> BTCUSDT (idempotent on canonical)

    async def _wire_map(self, symbols: List[str]) -> Dict[str, str]:
        return {s: s.lower() for s in symbols}   # spot: canonical -> wire (lowercase concat)

    def _sub_msg(self, wire: str) -> dict:
        raise NotImplementedError   # per-leaf (spot pick form / futures zip form)

    async def subscribe(self, ws, symbols: List[str]) -> None:
        wm = await self._wire_map(symbols)
        for s in symbols:
            await ws.send(_json.dumps(self._sub_msg(wm[s])))

        self.logger.info("SUBSCRIBE %d symbols", len(symbols))

    async def handle_control(self, ws, raw) -> bool:
        m = None
        if isinstance(raw, (bytes, bytearray)):
            if len(raw) > 300:
                return False
            try:
                m = _loads(gzip.decompress(raw))
            except Exception:
                return False
        elif isinstance(raw, str):
            if '"ping"' not in raw:
                return False
            try:
                m = _loads(raw)
            except Exception:
                return False
        else:
            return False

        if isinstance(m, dict) and "ping" in m:
            await ws.send(_json.dumps({"pong": m["ping"]}))
            return True

        return False

    def _scale_for(self, canon: str, levels):
        return levels   # spot no-op; futures overrides with x contract_size

    def parse(self, raw) -> Optional[List[Book]]:
        try:
            m = _loads(_text(raw))
        except (ValueError, TypeError):
            return None

        if not isinstance(m, dict):
            return None

        ch = m.get("ch")
        tick = m.get("tick")
        if not ch or not isinstance(tick, dict):
            return None   # sub ack / ping / status / a non-depth channel

        parts = ch.split(".")
        if len(parts) < 2:
            return None

        canon = self.normalize_symbol(parts[1])   # market.<sym>.depth.step0 -> <sym>
        bids = tick.get("bids") or []
        asks = tick.get("asks") or []
        if not bids or not asks:
            return None   # never emit a one-sided/empty book

        L = self.depth_level
        out_b = self._scale_for(canon, _topn(bids, L, reverse=True))    # robust top-L by price (no order assumption)
        out_a = self._scale_for(canon, _topn(asks, L, reverse=False))
        try:
            if float(out_b[0][0]) >= float(out_a[0][0]):
                return None   # never emit a crossed book
        except (ValueError, TypeError, IndexError):
            return None

        ts = m.get("ts")
        return [
            Book(
                symbol=canon,
                bids=out_b,
                asks=out_a,
                event_ts_ms=int(ts) if ts else None
            )
        ]


class HtxSpotConnector(_HtxBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("spot", worker_id=worker_id, num_workers=num_workers)

    def _sub_msg(self, wire: str) -> dict:
        return {
            "sub": f"market.{wire}.depth.step0",
            "symbol": wire,
            "pick": [f"bids.{self.depth_level}", f"asks.{self.depth_level}"],
            "step": "step0"
        }


class HtxFuturesConnector(_HtxBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("futures", worker_id=worker_id, num_workers=num_workers)

    async def _connection_kwargs(self, proxied: bool) -> dict:
        kw = await super()._connection_kwargs(proxied)
        kw["origin"] = "https://www.htx.com"
        return kw

    def _sub_msg(self, wire: str) -> dict:
        return {"sub": f"market.{wire}.depth.step0", "zip": 1}

    def _derive_wire(self, canon: str) -> str:
        for q in ("USDT", "USDC"):
            if canon.endswith(q) and len(canon) > len(q):
                return f"{canon[:-len(q)]}-{q}"
        return canon

    async def _wire_map(self, symbols: List[str]) -> Dict[str, str]:
        try:
            vals = await self.redis.hmget(get_market_data_key("htx", "futures"), *symbols)
        except Exception:
            vals = [None] * len(symbols)

        out = {}
        for s, v in zip(symbols, vals):
            code = None
            if v:
                try:
                    meta = _loads(v)
                    code = meta.get("contract_code")
                    cs = meta.get("contract_size")
                    if cs is not None:
                        cf = float(cs)
                        if cf > 0:
                            self._mult[s] = cf
                except Exception:
                    pass

            out[s] = code or self._derive_wire(s)

        return out

    def _scale_for(self, canon: str, levels):
        return _scale(levels, self._mult.get(canon, 1.0))
