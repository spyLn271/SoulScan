"""BingX order-book plugin (gzip frames, full snapshot, sort-both-sides, Pong keepalive)."""
import asyncio
import gzip
import json

from src.cex.plugins.bingx import BingxSpotConnector, BingxFuturesConnector


def _frame(symdash, bids, asks, gz=True):
    msg = json.dumps({"code": 0, "dataType": f"{symdash}@depth20", "data": {"bids": bids, "asks": asks}})
    return gzip.compress(msg.encode()) if gz else msg


def test_decode_and_sort_spot_descending_asks():
    c = BingxSpotConnector()
    # BingX SPOT sends asks DESCENDING; plugin must re-sort asks ascending, bids descending
    out = c.parse(_frame("BTC-USDT", [["100", "1"], ["99", "2"]], [["102", "3"], ["101", "4"]]))
    assert out[0].symbol == "BTCUSDT"
    assert out[0].bids == [["100", "1"], ["99", "2"]]    # desc
    assert out[0].asks == [["101", "4"], ["102", "3"]]   # re-sorted asc (best/lowest first)


def test_plain_json_frame_also_decodes():
    c = BingxSpotConnector()
    out = c.parse(_frame("ETH-USDT", [["10", "1"]], [["11", "1"]], gz=False))
    assert out[0].symbol == "ETHUSDT" and out[0].asks == [["11", "1"]]


def test_zero_qty_levels_filtered():
    c = BingxSpotConnector()
    out = c.parse(_frame("BTC-USDT", [["100", "1"], ["99", "0"]], [["102", "0"], ["101", "4"]]))
    assert out[0].bids == [["100", "1"]]    # 99@0 dropped
    assert out[0].asks == [["101", "4"]]    # 102@0 dropped


def test_crossed_book_suppressed():
    c = BingxSpotConnector()
    assert c.parse(_frame("BTC-USDT", [["105", "1"]], [["104", "1"]])) is None   # bid>=ask


def test_one_sided_suppressed():
    c = BingxSpotConnector()
    assert c.parse(_frame("BTC-USDT", [["100", "1"]], [])) is None


def test_keepalive_frames_ignored():
    c = BingxSpotConnector()
    assert c.parse(gzip.compress(b'"Ping"')) is None      # gzipped server Ping
    assert c.parse("Pong") is None
    assert c.parse(gzip.compress(b'not json')) is None     # garbage -> no crash


def test_subscribe_uses_dashed_symbol_and_depth():
    c = BingxFuturesConnector()
    sent = []

    class _WS:
        async def send(self, m):
            sent.append(json.loads(m))

    asyncio.run(c.subscribe(_WS(), ["BTCUSDT", "1000PEPEUSDT", "ETHUSDC"]))
    dts = [m["dataType"] for m in sent]
    assert dts == ["BTC-USDT@depth20", "1000PEPE-USDT@depth20", "ETH-USDC@depth20"]   # canonical -> dashed
    assert all(m["reqType"] == "sub" for m in sent)


def test_ping_and_ws_urls():
    s = BingxSpotConnector(); f = BingxFuturesConnector()
    assert asyncio.run(s.ping_message()) == "Pong"
    assert asyncio.run(s.ws_url()) == "wss://open-api-ws.bingx.com/market"
    assert asyncio.run(f.ws_url()) == "wss://open-api-swap.bingx.com/swap-market"
