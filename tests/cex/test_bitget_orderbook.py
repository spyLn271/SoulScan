"""Bitget order-book plugin (v2 `books`: snapshot+update, size 0 = remove, seq/pseq gap detection)."""
import asyncio
import json

import pytest

from src.cex.core.connector import ResyncRequired
from src.cex.plugins.bitget import BitgetSpotConnector, BitgetFuturesConnector


def _msg(sym, bids, asks, action="snapshot", ts="1000", seq=None, pseq=None, instType="SPOT"):
    d = {"asks": asks, "bids": bids, "ts": ts}
    if seq is not None:
        d["seq"] = seq
    if pseq is not None:
        d["pseq"] = pseq
    return json.dumps({"action": action, "arg": {"instType": instType, "channel": "books", "instId": sym},
                       "data": [d]})


def test_snapshot_then_update_merges():
    c = BitgetSpotConnector()
    c.parse(_msg("BTCUSDT", [["100", "1"], ["99", "5"]], [["101", "2"], ["102", "3"]], seq=10))
    out = c.parse(_msg("BTCUSDT", [["100", "0"]], [["101", "4"]], action="update", seq=11, pseq=10))
    assert out[0].symbol == "BTCUSDT"
    assert out[0].bids == [["99", "5"]]                  # 100 removed
    assert out[0].asks == [["101", "4"], ["102", "3"]]   # 101 updated, 102 kept
    assert out[0].event_ts_ms == 1000


def test_update_gated_until_snapshot():
    c = BitgetSpotConnector()
    assert c.parse(_msg("BTCUSDT", [["1", "1"]], [["2", "1"]], action="update", seq=2, pseq=1)) is None
    assert c.parse(_msg("BTCUSDT", [["1", "1"]], [["2", "1"]], seq=1)) is not None


def test_seq_chain_ok_then_gap_resyncs():
    c = BitgetSpotConnector()
    c.parse(_msg("BTCUSDT", [["100", "1"]], [["101", "2"]], seq=10))
    out = c.parse(_msg("BTCUSDT", [["100", "3"]], [["101", "2"]], action="update", seq=11, pseq=10))
    assert out[0].bids == [["100", "3"]]                  # chained update applied
    # next update's pseq (99) != our last seq (11) -> missed an update -> resync
    with pytest.raises(ResyncRequired):
        c.parse(_msg("BTCUSDT", [["100", "9"]], [["101", "2"]], action="update", seq=12, pseq=99))
    assert c._book["BTCUSDT"]["synced"] is False


def test_one_sided_book_not_emitted():
    c = BitgetSpotConnector()
    assert c.parse(_msg("BTCUSDT", [["100", "1"]], [], seq=1)) is None   # empty asks -> suppress


def test_corrupt_price_dropped_no_crash():
    c = BitgetSpotConnector()
    c.parse(_msg("BTCUSDT", [["100", "1"]], [["101", "2"]], seq=1))
    out = c.parse(_msg("BTCUSDT", [["oops", "5"]], [["102", "3"]], action="update", seq=2, pseq=1))
    assert "oops" not in c._book["BTCUSDT"]["b"]
    assert out[0].bids == [["100", "1"]] and out[0].asks == [["101", "2"], ["102", "3"]]


def test_ignores_control_frames():
    c = BitgetSpotConnector()
    for raw in ("pong",
                json.dumps({"event": "subscribe", "arg": {"channel": "books", "instId": "BTCUSDT"}}),
                json.dumps({"event": "error", "msg": "bad", "code": "30001"}),
                json.dumps({"action": "snapshot", "arg": {"channel": "trade", "instId": "BTCUSDT"}, "data": [{}]}),
                "not json{"):
        assert c.parse(raw) is None


def test_subscribe_spot_uses_SPOT_instType():
    c = BitgetSpotConnector()
    sent = []

    class _WS:
        async def send(self, m):
            sent.append(json.loads(m))

    asyncio.run(c.subscribe(_WS(), ["BTCUSDT", "ETHUSDT"]))
    args = [a for m in sent for a in m["args"]]
    assert all(a["instType"] == "SPOT" and a["channel"] == "books" for a in args)
    assert {a["instId"] for a in args} == {"BTCUSDT", "ETHUSDT"}
    assert c._book["BTCUSDT"] == {"b": {}, "a": {}, "synced": False, "seq": None}


def test_subscribe_futures_uses_per_symbol_instType():
    c = BitgetFuturesConnector()

    async def fake(syms):
        return {s: ("USDC-FUTURES" if s.endswith("PERP") else "USDT-FUTURES") for s in syms}
    c._inst_types = fake
    sent = []

    class _WS:
        async def send(self, m):
            sent.append(json.loads(m))

    asyncio.run(c.subscribe(_WS(), ["BTCUSDT", "ETHPERP"]))
    by = {a["instId"]: a["instType"] for m in sent for a in m["args"]}
    assert by == {"BTCUSDT": "USDT-FUTURES", "ETHPERP": "USDC-FUTURES"}


def test_ping_and_ws_url():
    c = BitgetSpotConnector()
    assert asyncio.run(c.ping_message()) == "ping"
    assert asyncio.run(c.ws_url()) == "wss://ws.bitget.com/v2/ws/public"
