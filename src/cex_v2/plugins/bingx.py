#!/usr/bin/env python3
"""
BingX order books on the cex_v2 core — spot AND futures (USDT/USDC perps), documented WS depth.

Spot  -> wss://open-api-ws.bingx.com/market
Futures (perp) -> wss://open-api-swap.bingx.com/swap-market
Both: subscribe {"id","reqType":"sub","dataType":"<BASE>-<QUOTE>@depth<level>"}, GZIP-compressed frames,
each a FULL top-N snapshot {bids, asks} -> STATELESS plugin (decode -> emit, collapse-to-latest handles
the rest). No exchange event ts in the frame (recv-time stamped). Keepalive: BingX uses server "Ping" /
client "Pong"; an unsolicited periodic "Pong" keeps the connection alive (verified 2026-06-16) and fits
the connector's ping loop, so ping_message()="Pong".

ORDERING QUIRK (verified): BingX SPOT returns asks DESCENDING (best/lowest ask is last); perp returns
asks ascending. We sort BOTH sides explicitly (bids desc / asks asc) — cheap at 20 levels — so the
ordering source doesn't matter, and we drop crossed/corrupt frames.

Symbols are dashed (BTC-USDT) like OKX; canonical = strip the dash (BTCUSDT). The dashed form for the
subscribe is reconstructed from the canonical (quote is always USDT/USDC, 4 chars) — no md lookup needed.
"""
import asyncio
import gzip
import json as _json
from typing import List, Optional

from src.cex_v2.core.connector import OrderBookConnector, Book

try:
    import orjson

    def _loads(raw):
        return orjson.loads(raw)
except ImportError:
    def _loads(raw):
        return _json.loads(raw)


class _BingxBase(OrderBookConnector):
    def __init__(self, market_type: str, worker_id: int = None, num_workers: int = None):
        super().__init__("bingx", market_type, worker_id=worker_id, num_workers=num_workers)
        self.depth_level = int(self.special_params.get("depth_level", 20))
        self._id = 0

    async def ws_url(self) -> str:
        return self.market_config["ws_url"]

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.upper().replace("-", "")   # BTC-USDT -> BTCUSDT

    def _ws_symbol(self, canon: str) -> str:
        # BTCUSDT -> BTC-USDT (quote is USDT/USDC -> 4 chars). Idempotent if already dashed.
        if "-" in canon:
            return canon
        return canon[:-4] + "-" + canon[-4:]

    async def subscribe(self, ws, symbols: List[str]) -> None:
        for s in symbols:
            self._id += 1
            dt = f"{self._ws_symbol(self.normalize_symbol(s))}@depth{self.depth_level}"
            await ws.send(_json.dumps({"id": str(self._id), "reqType": "sub", "dataType": dt}))
            await asyncio.sleep(0.02)   # respect BingX per-connection message rate
        self.logger.info("SUBSCRIBE %d symbols (depth%d)", len(symbols), self.depth_level)

    async def ping_message(self) -> Optional[str]:
        return "Pong"   # BingX keepalive (server Ping / client Pong); periodic Pong keeps it alive

    def parse(self, raw) -> Optional[List[Book]]:
        if isinstance(raw, (bytes, bytearray)):
            try:
                raw = gzip.decompress(raw).decode("utf-8", "replace")
            except Exception:
                return None
        s = raw.strip().strip('"')
        if s in ("Ping", "Pong"):
            return None   # keepalive frames
        try:
            m = _loads(raw)
        except (ValueError, TypeError):
            return None
        if not isinstance(m, dict):
            return None
        dt = m.get("dataType", "")
        if "@depth" not in dt:
            if m.get("code") not in (0, None):
                self.logger.warning("bingx sub error: %s", str(m)[:140])
            return None
        d = m.get("data")
        if not isinstance(d, dict):
            return None
        rb, ra = d.get("bids"), d.get("asks")
        if not rb or not ra:
            return None
        sym = self.normalize_symbol(dt.split("@")[0])
        n = self.depth_level
        try:
            bids = sorted(([p, q] for p, q in rb if float(q) > 0), key=lambda x: float(x[0]), reverse=True)[:n]
            asks = sorted(([p, q] for p, q in ra if float(q) > 0), key=lambda x: float(x[0]))[:n]
        except (ValueError, TypeError):
            return None
        if not bids or not asks:
            return None
        if float(bids[0][0]) >= float(asks[0][0]):
            return None   # never emit a crossed/corrupt book
        return [Book(symbol=sym, bids=bids, asks=asks, event_ts_ms=None)]   # no exchange event ts


class BingxSpotConnector(_BingxBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("spot", worker_id=worker_id, num_workers=num_workers)


class BingxFuturesConnector(_BingxBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("futures", worker_id=worker_id, num_workers=num_workers)
