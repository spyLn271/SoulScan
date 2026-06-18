#!/usr/bin/env python3
"""
MEXC order books on the cex_v2 core — SPOT (the documented v3 PROTOBUF WebSocket).

MEXC is the first PROTOBUF venue: v3 WS data frames are protobuf-encoded binary (the `.pb` channels);
MEXC removed the JSON depth channels (they return "Blocked!"). We use
`spot@public.limit.depth.v3.api.pb@<SYMBOL>@<level>` — a FULL top-N snapshot per frame, so this is a
STATELESS plugin (like binance): decode → emit, collapse-to-latest handles the rest. VERIFIED 2026-06-16:
decoded book == REST /api/v3/depth byte-for-byte (0.00 bps incl sizes).

Frames decode via MEXC's official .proto schema, vendored + compiled to `mexc_proto/*_pb2.py`
(generated with grpcio-tools; runtime only needs `google.protobuf`). The wrapper is
`PushDataV3ApiWrapper{channel, symbol, sendTime, publicLimitDepths{asks[], bids[]}}` where each level is
`{price, quantity}` (already sorted: bids desc, asks asc). We import the pb2 flat via sys.path to avoid
protobuf's double-registration (importing the same generated module twice raises).

NOTE: MEXC FUTURES uses the SAME endpoint + protobuf wrapper (channel futures@public.limit.depth.v3.api.pb)
but is GEO-RESTRICTED from this datacenter ("Blocked!" direct + via proxy; all our IPs are Hetzner/Germany).
Left disabled (config futures.enabled=False) until a region-allowed egress exists. If/when enabled, a
MexcFuturesConnector here is ~identical to spot (futures@ channel + contract.mexc.com REST for the
universe, symbols BTC_USDT->BTCUSDT, settleCoin USDT/USDC for the linear filter), routed via that proxy.
MEXC WS limits: 30 subscriptions/connection (hard), ping {"method":"PING"} within 60s.
"""
import json as _json
import os
import sys
from typing import List, Optional

from src.cex_v2.core.connector import OrderBookConnector, Book

_PROTO_DIR = os.path.join(os.path.dirname(__file__), "mexc_proto")
if _PROTO_DIR not in sys.path:
    sys.path.insert(0, _PROTO_DIR)
import PushDataV3ApiWrapper_pb2 as _mexc_pb   # noqa: E402  (flat import; resolves the other pb2 deps)


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


class MexcSpotConnector(OrderBookConnector):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("mexc", "spot", worker_id=worker_id, num_workers=num_workers)
        self.depth_level = int(self.special_params.get("depth_level", 20))
        self.sub_chunk = int(self.special_params.get("sub_chunk", 10))
        self._id = 0

    async def ws_url(self) -> str:
        return self.market_config["ws_url"]

    def _channel(self, sym: str) -> str:
        return f"spot@public.limit.depth.v3.api.pb@{sym}@{self.depth_level}"

    async def subscribe(self, ws, symbols: List[str]) -> None:
        chans = [self._channel(self.normalize_symbol(s)) for s in symbols]
        for chunk in _chunks(chans, self.sub_chunk):
            self._id += 1
            await ws.send(_json.dumps({"method": "SUBSCRIPTION", "params": chunk, "id": self._id}))
        self.logger.info("SUBSCRIBE %d symbols (limit.depth.pb)", len(chans))

    async def ping_message(self) -> Optional[str]:
        return _json.dumps({"method": "PING"})   # MEXC -> {"id":0,"code":0,"msg":"PONG"}

    def parse(self, raw) -> Optional[List[Book]]:
        if not isinstance(raw, (bytes, bytearray)):
            return None   # JSON control frame (subscribe ack / PONG) — protobuf data only
        w = _mexc_pb.PushDataV3ApiWrapper()
        try:
            w.ParseFromString(raw)
        except Exception as e:
            self.logger.debug("protobuf decode failed (%dB): %s", len(raw), str(e)[:100])
            return None
        if not w.HasField("publicLimitDepths"):
            return None
        sym = self.normalize_symbol(w.symbol)
        if not sym:
            return None
        d = w.publicLimitDepths
        bids = [[i.price, i.quantity] for i in d.bids]   # already sorted desc
        asks = [[i.price, i.quantity] for i in d.asks]   # already sorted asc
        if not bids or not asks:
            return None   # never emit a one-sided/empty book
        try:
            if float(bids[0][0]) >= float(asks[0][0]):
                return None   # never emit a crossed/corrupt book to the engine
        except (ValueError, TypeError):
            return None
        ts = w.sendTime or w.createTime or None
        return [Book(symbol=sym, bids=bids, asks=asks, event_ts_ms=ts)]
