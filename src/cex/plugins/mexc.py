import json as _json
from typing import List, Optional

from src.cex.core.connector import OrderBookConnector, Book
from src.cex.plugins.mexc_proto import PushDataV3ApiWrapper_pb2 as _mexc_pb


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


class MexcSpotConnector(OrderBookConnector):
    def __init__(
            self,
            worker_id: int = None,
            num_workers: int = None
    ):
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
            return None

        try:
            if float(bids[0][0]) >= float(asks[0][0]):
                return None
        except (ValueError, TypeError):
            return None

        ts = w.sendTime or w.createTime or None
        return [
            Book(
                symbol=sym,
                bids=bids,
                asks=asks,
                event_ts_ms=ts
            )
        ]