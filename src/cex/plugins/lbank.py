import asyncio
import gzip
import heapq
import json as _json
from typing import List, Optional

from src.cex.core.connector import OrderBookConnector, Book

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


def _isnum(v) -> bool:
    try:
        float(v)
        return True
    except (ValueError, TypeError):
        return False


def _topn(levels, n, reverse):
    good = [lvl for lvl in levels if len(lvl) >= 2 and _isnum(lvl[0])]
    return (
        heapq.nlargest(n, good, key=lambda l: float(l[0])) if reverse
            else heapq.nsmallest(n, good, key=lambda l: float(l[0]))
    )


class _LbankBase(OrderBookConnector):
    def __init__(
            self,
            market_type: str,
            worker_id: int = None,
            num_workers: int = None
    ):
        super().__init__("lbank", market_type, worker_id=worker_id, num_workers=num_workers)

        self.depth_level = int(self.special_params.get("depth_level", 50))
        self.sub_delay = float(self.special_params.get("sub_delay", 0.05))

    async def ws_url(self) -> str:
        return self.market_config["ws_url"]

    async def _connection_kwargs(self, proxied: bool) -> dict:
        kw = await super()._connection_kwargs(proxied)
        kw["origin"] = "https://www.lbank.com"
        return kw

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.upper().replace("_", "")

    def _wire(self, canon: str) -> str:
        for q in ("USDT", "USDC"):
            if canon.endswith(q) and len(canon) > len(q):
                return f"{canon[:-len(q)].lower()}_{q.lower()}"   # SOLUSDT -> sol_usdt
        return canon.lower()

    async def subscribe(self, ws, symbols: List[str]) -> None:
        for s in symbols:
            await ws.send(_json.dumps({
                "action": "subscribe",
                "subscribe": "depth",
                "depth": 200,
                "pair": self._wire(s),
                "msgType": 2,
                "limit": self.depth_level,
                "type": 0,
                "dataType": 3,
                "clientType": "",
            }))
            if self.sub_delay:
                await asyncio.sleep(self.sub_delay)

        self.logger.info("SUBSCRIBE %d symbols", len(symbols))

    async def handle_control(self, ws, raw) -> bool:
        if isinstance(raw, (bytes, bytearray)):
            if len(raw) > 300:
                return False
            try:
                txt = gzip.decompress(raw).decode("utf-8", "replace")
            except Exception:
                try:
                    txt = bytes(raw).decode("utf-8", "replace")
                except Exception:
                    return False
        elif isinstance(raw, str):
            if '"ping"' not in raw:
                return False
            txt = raw
        else:
            return False

        try:
            d = _loads(txt)
        except Exception:
            return False

        if isinstance(d, dict) and d.get("action") == "ping":
            await ws.send(_json.dumps({"action": "pong", "pong": d.get("ping")}))
            return True

        return False

    def parse(self, raw) -> Optional[List[Book]]:
        try:
            m = _loads(_text(raw))
        except (ValueError, TypeError):
            return None

        if not isinstance(m, dict):
            return None

        dep = m.get("depth")
        pair = m.get("pair")
        if not isinstance(dep, dict) or not pair:
            return None   # ping / ack / a non-depth frame

        canon = self.normalize_symbol(pair)
        bids = dep.get("bids") or []
        asks = dep.get("asks") or []
        if not bids or not asks:
            return None

        L = self.depth_level
        out_b = [[l[0], l[1]] for l in _topn(bids, L, reverse=True)]    # level = [px, sz, ratio, cum] -> [px, sz]
        out_a = [[l[0], l[1]] for l in _topn(asks, L, reverse=False)]
        try:
            if float(out_b[0][0]) >= float(out_a[0][0]):
                return None
        except (ValueError, TypeError, IndexError):
            return None

        ds = m.get("ds")
        return [
            Book(
                symbol=canon,
                bids=out_b,
                asks=out_a,
                event_ts_ms=int(ds) if isinstance(ds, (int, float)) else None)
        ]


class LbankSpotConnector(_LbankBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("spot", worker_id=worker_id, num_workers=num_workers)
