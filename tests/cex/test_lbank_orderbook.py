"""LBank spot plugin: gzip V3 depth snapshot parse ([px,sz] from [px,sz,ratio,cum]), server ping->pong,
per-pair subscribe, and the lowercase_underscore <-> canonical symbol mapping. Stateless full snapshot."""
import asyncio
import gzip
import json

from src.cex.plugins.lbank import LbankSpotConnector


class _WS:
    def __init__(self):
        self.sent = []

    async def send(self, m):
        self.sent.append(m)


def _gz(obj):
    return gzip.compress(json.dumps(obj).encode())


def _c():
    c = LbankSpotConnector(); c.depth_level = 50; c.sub_delay = 0; return c


def test_normalize_and_wire():
    c = _c()
    assert c.normalize_symbol("sol_usdt") == "SOLUSDT"
    assert c.normalize_symbol("SOLUSDT") == "SOLUSDT"   # idempotent
    assert c._wire("SOLUSDT") == "sol_usdt"
    assert c._wire("ETHUSDC") == "eth_usdc"


def test_subscribe_one_per_pair():
    c = _c(); ws = _WS()
    asyncio.run(c.subscribe(ws, ["SOLUSDT", "BTCUSDT"]))
    msgs = [json.loads(m) for m in ws.sent]
    assert [m["pair"] for m in msgs] == ["sol_usdt", "btc_usdt"]
    assert all(m["action"] == "subscribe" and m["subscribe"] == "depth" for m in msgs)
    assert all(m["type"] == 0 for m in msgs)   # type=0 = RAW minimal tick (NOT the 0.01-merge type=100)


def _frame(bids, asks, pair="sol_usdt", ds=1781787311433):
    return {"depth": {"bids": bids, "asks": asks}, "pair": pair, "ds": ds, "type": "depth"}


def test_parse_snapshot_keeps_price_size_only():
    c = _c()
    # V3 levels are [price, size, ratio, cumulative]; we keep [price, size]
    fr = _frame(bids=[["71.49", "283.078", "0.0119", "283.078"], ["71.48", "462.40", "0.03", "745.4"]],
                asks=[["71.50", "181.32", "0.0089", "181.32"], ["71.51", "300.78", "0.02", "482.1"]])
    b = c.parse(_gz(fr))[0]
    assert b.symbol == "SOLUSDT" and b.event_ts_ms == 1781787311433
    assert b.bids[0] == ["71.49", "283.078"] and b.asks[0] == ["71.50", "181.32"]   # ratio/cum dropped, base-asset


def test_depth_level_caps_and_orders():
    c = _c(); c.depth_level = 1
    fr = _frame(bids=[["71.49", "1", "0", "1"], ["71.50", "1", "0", "1"]],   # unsorted on purpose
                asks=[["71.60", "1", "0", "1"], ["71.55", "1", "0", "1"]])
    b = c.parse(_gz(fr))[0]
    assert b.bids == [["71.50", "1"]]   # highest bid
    assert b.asks == [["71.55", "1"]]   # lowest ask


def test_parse_rejects_crossed_and_acktoken():
    c = _c()
    crossed = _frame(bids=[["71.60", "1", "0", "1"]], asks=[["71.50", "1", "0", "1"]])
    assert c.parse(_gz(crossed)) is None
    # the plain-text sub-ack token (not JSON) is ignored
    assert c.parse("cQnBZmVmOqARan8TKi5qLoROQkxwnZdjZraZCrsx_depth_sol_usdt_200_100") is None
    assert c.parse(_gz({"action": "ping", "ping": 123})) is None   # ping is not a book


def test_handle_control_ping_pong():
    c = _c(); ws = _WS()
    assert asyncio.run(c.handle_control(ws, _gz({"action": "ping", "ping": "abc"}))) is True
    assert json.loads(ws.sent[0]) == {"action": "pong", "pong": "abc"}
    # also handle a str-framed ping; ignore the ack token + big frames
    ws2 = _WS()
    assert asyncio.run(c.handle_control(ws2, '{"action":"ping","ping":"x"}')) is True
    assert json.loads(ws2.sent[0]) == {"action": "pong", "pong": "x"}
    ws3 = _WS()
    assert asyncio.run(c.handle_control(ws3, "ack_token_text")) is False
    assert asyncio.run(c.handle_control(ws3, b"x" * 400)) is False   # big -> gated
    assert ws3.sent == []
