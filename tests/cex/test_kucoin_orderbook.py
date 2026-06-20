"""KuCoin plugin: stateless level2Depth50 snapshot parse, comma-batched subscribe (<=100/topic, chunked),
wire-from-md, spot hyphen mapping + futures XBT->BTC / strip-M mapping, futures CONTRACT->base (x multiplier)."""
import asyncio
import json

from src.cex.plugins.kucoin import KucoinSpotConnector, KucoinFuturesConnector


class _WS:
    def __init__(self):
        self.sent = []

    async def send(self, m):
        self.sent.append(m)


async def _noload(symbols):
    return None


def _spot():
    c = KucoinSpotConnector(); c.depth_level = 50; c.topic_chunk = 100; c._load_spec = _noload; return c


def _fut():
    c = KucoinFuturesConnector(); c.depth_level = 50; c.topic_chunk = 100; c._load_spec = _noload; return c


def test_normalize_spot_and_futures():
    assert _spot().normalize_symbol("BTC-USDT") == "BTCUSDT"
    f = _fut()
    assert f.normalize_symbol("XBTUSDTM") == "BTCUSDT"        # XBT=bitcoin, strip trailing M
    assert f.normalize_symbol("ETHUSDTM") == "ETHUSDT"
    assert f.normalize_symbol("1000000MOGUSDTM") == "1000000MOGUSDT"
    assert f.normalize_symbol("XBTGUSDTM") == "XBTGUSDT"     # only real bitcoin (XBT+quote) is swapped, not an XBT*-named base


def test_spot_subscribe_comma_batched():
    c = _spot(); ws = _WS()
    c._wire = {"BTCUSDT": "BTC-USDT", "ETHUSDT": "ETH-USDT"}
    asyncio.run(c.subscribe(ws, ["BTCUSDT", "ETHUSDT", "NOWIREUSDT"]))   # NOWIRE skipped (no wire yet)
    m = json.loads(ws.sent[0])
    assert m["type"] == "subscribe" and m["topic"] == "/spotMarket/level2Depth50:BTC-USDT,ETH-USDT"


def test_subscribe_chunks_at_topic_limit():
    c = _spot(); c.topic_chunk = 2; ws = _WS()
    c._wire = {"AUSDT": "A-USDT", "BUSDT": "B-USDT", "CUSDT": "C-USDT"}
    asyncio.run(c.subscribe(ws, ["AUSDT", "BUSDT", "CUSDT"]))
    topics = [json.loads(s)["topic"] for s in ws.sent]
    assert topics == ["/spotMarket/level2Depth50:A-USDT,B-USDT", "/spotMarket/level2Depth50:C-USDT"]


def test_futures_subscribe_wire():
    c = _fut(); ws = _WS()
    c._wire = {"BTCUSDT": "XBTUSDTM"}
    asyncio.run(c.subscribe(ws, ["BTCUSDT"]))
    assert json.loads(ws.sent[0])["topic"] == "/contractMarket/level2Depth50:XBTUSDTM"


def test_spot_parse_full_snapshot_base_asset():
    c = _spot()
    frame = {"type": "message", "subject": "level2", "topic": "/spotMarket/level2Depth50:BTC-USDT",
             "data": {"bids": [["100", "5"], ["99", "3"]], "asks": [["101", "4"], ["102", "1"]], "timestamp": 123}}
    b = c.parse(json.dumps(frame))[0]
    assert b.symbol == "BTCUSDT" and b.event_ts_ms == 123
    assert b.bids[0] == ["100", "5"] and b.asks[0] == ["101", "4"]


def test_futures_parse_scales_contracts_by_multiplier():
    c = _fut(); c._mult = {"BTCUSDT": 0.001}
    frame = {"type": "message", "subject": "level2", "topic": "/contractMarket/level2Depth50:XBTUSDTM",
             "data": {"bids": [["100", 603]], "asks": [["101", 126]], "timestamp": 1}}
    b = c.parse(json.dumps(frame))[0]
    assert b.symbol == "BTCUSDT"
    assert b.bids[0] == ["100", 603 * 0.001] and b.asks[0] == ["101", 126 * 0.001]


def test_futures_parse_raw_when_no_mult():
    c = _fut()
    frame = {"type": "message", "subject": "level2", "topic": "/contractMarket/level2Depth50:ETHUSDTM",
             "data": {"bids": [["3000", 10]], "asks": [["3001", 5]]}}
    b = c.parse(json.dumps(frame))[0]
    assert b.bids[0] == ["3000", 10] and b.asks[0] == ["3001", 5]


def test_parse_rejects_crossed_control_and_bad_rows():
    c = _spot()
    crossed = {"type": "message", "subject": "level2", "topic": "/spotMarket/level2Depth50:BTC-USDT",
               "data": {"bids": [["101", "1"]], "asks": [["100", "1"]]}}
    assert c.parse(json.dumps(crossed)) is None
    assert c.parse(json.dumps({"type": "welcome", "id": "1"})) is None
    assert c.parse(json.dumps({"type": "pong", "id": "1"})) is None
    assert c.parse(json.dumps({"type": "ack", "id": "1"})) is None
    # non-list row drops only that row, not the whole frame
    f = {"type": "message", "subject": "level2", "topic": "/spotMarket/level2Depth50:BTC-USDT",
         "data": {"bids": [None, ["100", "5"], 7], "asks": [["101", "4"]]}}
    b = c.parse(json.dumps(f))[0]
    assert b.bids[0] == ["100", "5"] and b.asks[0] == ["101", "4"]


def test_topn_orders_by_price():
    c = _spot()
    f = {"type": "message", "subject": "level2", "topic": "/spotMarket/level2Depth50:BTC-USDT",
         "data": {"bids": [["99", "3"], ["100", "5"]], "asks": [["102", "1"], ["101", "4"]]}}
    b = c.parse(json.dumps(f))[0]
    assert b.bids[0] == ["100", "5"] and b.asks[0] == ["101", "4"]
