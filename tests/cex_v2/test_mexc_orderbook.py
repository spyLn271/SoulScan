"""MEXC spot order-book plugin (protobuf limit.depth, full snapshot, stateless)."""
import asyncio
import json

import src.cex_v2.plugins.mexc as mexc   # importing sets up the mexc_proto sys.path
from src.cex_v2.plugins.mexc import MexcSpotConnector
import PushDataV3ApiWrapper_pb2 as mpb    # same cached flat module the plugin uses


def _frame(sym, bids, asks, ts=1700):
    w = mpb.PushDataV3ApiWrapper()
    w.channel = f"spot@public.limit.depth.v3.api.pb@{sym}@20"
    w.symbol = sym
    w.sendTime = ts
    for p, q in bids:
        it = w.publicLimitDepths.bids.add(); it.price = p; it.quantity = q
    for p, q in asks:
        it = w.publicLimitDepths.asks.add(); it.price = p; it.quantity = q
    return w.SerializeToString()


def test_decode_limit_depth_snapshot():
    c = MexcSpotConnector()
    out = c.parse(_frame("SOLUSDT", [["73.44", "206.3"], ["73.43", "10"]], [["73.45", "1751.9"], ["73.46", "5"]]))
    assert out[0].symbol == "SOLUSDT" and out[0].event_ts_ms == 1700
    assert out[0].bids == [["73.44", "206.3"], ["73.43", "10"]]   # bids desc, preserved
    assert out[0].asks == [["73.45", "1751.9"], ["73.46", "5"]]   # asks asc, preserved


def test_ignores_json_control_frames():
    c = MexcSpotConnector()
    # JSON acks / PONG arrive as text, not bytes -> protobuf path skips them
    assert c.parse(json.dumps({"id": 1, "code": 0, "msg": "spot@..."})) is None
    assert c.parse(json.dumps({"id": 0, "code": 0, "msg": "PONG"})) is None
    assert c.parse(b"\x00\x01garbage") is None   # undecodable bytes -> None, no crash


def test_one_sided_book_suppressed():
    c = MexcSpotConnector()
    assert c.parse(_frame("SOLUSDT", [["73.44", "1"]], [])) is None   # empty asks -> suppress


def test_crossed_book_suppressed():
    c = MexcSpotConnector()
    # best bid >= best ask = corrupt -> never emit
    assert c.parse(_frame("SOLUSDT", [["73.50", "1"]], [["73.45", "1"]])) is None


def test_subscribe_builds_pb_channels_chunked():
    c = MexcSpotConnector()
    c.sub_chunk = 2
    sent = []

    class _WS:
        async def send(self, m):
            sent.append(json.loads(m))

    asyncio.run(c.subscribe(_WS(), ["BTCUSDT", "ETHUSDT", "SOLUSDT"]))
    assert all(m["method"] == "SUBSCRIPTION" and len(m["params"]) <= 2 for m in sent)   # chunked <=2
    params = [p for m in sent for p in m["params"]]
    assert params == ["spot@public.limit.depth.v3.api.pb@BTCUSDT@20",
                      "spot@public.limit.depth.v3.api.pb@ETHUSDT@20",
                      "spot@public.limit.depth.v3.api.pb@SOLUSDT@20"]


def test_ping_and_ws_url():
    c = MexcSpotConnector()
    assert json.loads(asyncio.run(c.ping_message())) == {"method": "PING"}
    assert asyncio.run(c.ws_url()) == "wss://wbs-api.mexc.com/ws"
