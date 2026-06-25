"""HTX plugin: gzip snapshot parse, server-ping->client-pong, per-symbol subscribe, and the futures
CONTRACT->base-asset scaling (x contract_size). Spot + futures share one stateless full-snapshot core."""
import asyncio
import gzip
import json

from src.cex.plugins.htx import HtxSpotConnector, HtxFuturesConnector


class _WS:
    def __init__(self):
        self.sent = []

    async def send(self, m):
        self.sent.append(m)


def _gz(obj):
    return gzip.compress(json.dumps(obj).encode())


def _spot():
    c = HtxSpotConnector(); c.depth_level = 50; return c


def _fut():
    c = HtxFuturesConnector(); c.depth_level = 50; return c


# ---- symbol normalization (one canonical space for both legs) ----
def test_normalize_symbol():
    c = _spot()
    assert c.normalize_symbol("btcusdt") == "BTCUSDT"
    assert c.normalize_symbol("BTC-USDT") == "BTCUSDT"        # futures dashed wire
    assert c.normalize_symbol("BTCUSDT") == "BTCUSDT"         # idempotent on canonical


# ---- subscribe message shapes (match the website forms) ----
def test_spot_sub_msg():
    assert _spot()._sub_msg("btcusdt") == {
        "sub": "market.btcusdt.depth.step0", "symbol": "btcusdt",
        "pick": ["bids.50", "asks.50"], "step": "step0"}


def test_futures_sub_msg_and_derive_wire():
    c = _fut()
    assert c._sub_msg("BTC-USDT") == {"sub": "market.BTC-USDT.depth.step0", "zip": 1}
    assert c._derive_wire("BTCUSDT") == "BTC-USDT"
    assert c._derive_wire("ETHUSDC") == "ETH-USDC"


def test_spot_subscribe_sends_one_per_symbol():
    c = _spot(); ws = _WS()
    asyncio.run(c.subscribe(ws, ["BTCUSDT", "ETHUSDT"]))
    subbed = [json.loads(m)["sub"] for m in ws.sent]
    assert subbed == ["market.btcusdt.depth.step0", "market.ethusdt.depth.step0"]


# ---- gzip snapshot parse ----
def test_spot_parse_gzip_snapshot():
    c = _spot()
    frame = {"ch": "market.btcusdt.depth.step0", "ts": 1781780800178,
             "tick": {"bids": [[64000.0, 2.5], [63999.0, 1.0]], "asks": [[64001.0, 0.5], [64002.0, 1.0]]}}
    books = c.parse(_gz(frame))
    assert len(books) == 1
    b = books[0]
    assert b.symbol == "BTCUSDT" and b.event_ts_ms == 1781780800178
    assert b.bids[0] == [64000.0, 2.5] and b.asks[0] == [64001.0, 0.5]   # base-asset, untouched


def test_depth_level_slices_top_n():
    c = _spot(); c.depth_level = 1
    frame = {"ch": "market.btcusdt.depth.step0", "ts": 1,
             "tick": {"bids": [[64000, 1], [63999, 1]], "asks": [[64001, 1], [64002, 1]]}}
    b = c.parse(_gz(frame))[0]
    assert len(b.bids) == 1 and len(b.asks) == 1


def test_parse_rejects_crossed_and_acks():
    c = _spot()
    crossed = {"ch": "market.btcusdt.depth.step0", "ts": 1,
               "tick": {"bids": [[64001, 1]], "asks": [[64000, 1]]}}
    assert c.parse(_gz(crossed)) is None
    assert c.parse(_gz({"id": None, "status": "ok", "subbed": "market.btcusdt.depth.step0"})) is None
    assert c.parse(_gz({"ping": 123})) is None   # ping is not a book (handled in handle_control)


# ---- futures contract -> base-asset scaling ----
def test_futures_scale_by_contract_size():
    c = _fut(); c._mult = {"BTCUSDT": 0.001}     # BTC-USDT: 1 contract = 0.001 BTC
    frame = {"ch": "market.BTC-USDT.depth.step0", "ts": 9,
             "tick": {"bids": [[64000, 4092]], "asks": [[64001, 1517]]}}
    b = c.parse(_gz(frame))[0]
    assert b.symbol == "BTCUSDT"
    assert b.bids[0] == [64000, 4092 * 0.001] and b.asks[0] == [64001, 1517 * 0.001]


def test_futures_scale_noop_when_mult_missing():
    c = _fut()   # no _mult -> defaults to 1.0 (raw contracts until md publishes contract_size)
    frame = {"ch": "market.ETH-USDT.depth.step0", "ts": 9,
             "tick": {"bids": [[3000, 10]], "asks": [[3001, 5]]}}
    b = c.parse(_gz(frame))[0]
    assert b.bids[0] == [3000, 10] and b.asks[0] == [3001, 5]


# ---- {"ping":ts} -> {"pong":ts}, size-gated ----
def test_handle_control_ping_pong():
    c = _spot(); ws = _WS()
    assert asyncio.run(c.handle_control(ws, _gz({"ping": 123}))) is True
    assert json.loads(ws.sent[0]) == {"pong": 123}


def test_handle_control_ignores_non_ping_and_big_frames():
    c = _spot(); ws = _WS()
    assert asyncio.run(c.handle_control(ws, _gz({"status": "ok"}))) is False   # small, not ping
    assert asyncio.run(c.handle_control(ws, b"x" * 400)) is False              # big -> gated, not decompressed
    assert asyncio.run(c.handle_control(ws, b"not-gzip")) is False             # small, undecodable
    assert ws.sent == []


def test_handle_control_text_ping():
    c = _spot(); ws = _WS()
    assert asyncio.run(c.handle_control(ws, '{"ping":456}')) is True   # defensive: text-framed ping
    assert json.loads(ws.sent[0]) == {"pong": 456}
    ws2 = _WS()
    assert asyncio.run(c.handle_control(ws2, '{"ch":"market.btcusdt.depth.step0"}')) is False  # text data
    assert ws2.sent == []
