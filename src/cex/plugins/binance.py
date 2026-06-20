#!/usr/bin/env python3
"""
Binance order books on the cex_v2 OrderBookConnector core — spot AND futures.

Both use combined partial-depth streams (`<symbol>@depth20@100ms`, wrapped as {stream, data}).
They differ only in endpoint + payload field names:
  - spot  (stream.binance.com): data has `bids`/`asks`, no symbol, no event ts -> recv-time stamped.
  - futures (fstream.binance.com): data has `b`/`a`, `s` (symbol), `E` (event ms).
Each payload is a full top-N snapshot, so the core's collapse-to-latest + pipelined flush applies.
"""
import asyncio
import itertools
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


class _BinanceBase(OrderBookConnector):
    # payload field names (overridden per market)
    _bids_key = "bids"
    _asks_key = "asks"
    _ts_key = None  # None -> core stamps recv time

    def __init__(self, market_type: str, worker_id: int = None, num_workers: int = None):
        super().__init__("binance", market_type, worker_id=worker_id, num_workers=num_workers)
        self.depth_level = self.special_params.get("depth_level", 20)
        self.update_speed = self.special_params.get("update_speed", "100ms")
        self._req_id = itertools.count(1)

    async def ws_url(self) -> str:
        return self.market_config["ws_url"]

    def _stream_name(self, symbol: str) -> str:
        return f"{symbol.lower()}@depth{self.depth_level}@{self.update_speed}"

    async def subscribe(self, ws, symbols: List[str]) -> None:
        params = [self._stream_name(s) for s in symbols]
        if not params:
            return
        await ws.send(_json.dumps({"method": "SUBSCRIBE", "params": params, "id": next(self._req_id)}))
        self.logger.info("SUBSCRIBE %d symbols", len(params))

    def parse(self, raw) -> Optional[List[Book]]:
        try:
            m = _loads(raw)
        except (ValueError, TypeError):
            return None
        stream = m.get("stream")
        data = m.get("data")
        if not stream or not isinstance(data, dict):
            return None  # SUBSCRIBE ack / control
        bids = data.get(self._bids_key, [])
        asks = data.get(self._asks_key, [])
        if not bids and not asks:
            return None
        symbol = stream.split("@", 1)[0].upper()
        ts = data.get(self._ts_key) if self._ts_key else None
        return [Book(symbol=symbol, bids=bids, asks=asks, event_ts_ms=ts)]


class BinanceSpotConnector(_BinanceBase):
    _bids_key, _asks_key, _ts_key = "bids", "asks", None

    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("spot", worker_id=worker_id, num_workers=num_workers)


class BinanceFuturesConnector(_BinanceBase):
    _bids_key, _asks_key, _ts_key = "b", "a", "E"

    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("futures", worker_id=worker_id, num_workers=num_workers)
