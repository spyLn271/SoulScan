"""Bybit order-book plugins.
SPOT    = ws2 mergedDepth (full snapshot, dumpScale subscribe, ws2 ping).
FUTURES = realtime_w (gzip frames, orderBook_20@m1.H.<sym>, snapshot+delta, b1/a1 drift resync)."""
import asyncio
import gzip
import json

import pytest

from src.cex_v2.core.connector import ResyncRequired
from src.cex_v2.plugins.bybit import BybitSpotConnector, BybitFuturesConnector


# ============================================================ SPOT (ws2 mergedDepth)
def test_spot_mergeddepth_full_snapshot():
    c = BybitSpotConnector()
    raw = json.dumps({"topic": "mergedDepth", "data": [{
        "s": "BTCUSDT", "t": 1700, "v": 9,
        "b": [["65594", "1.2"], ["65593.6", "0.02"]], "a": [["65594.1", "4.0"]]}]})
    out = c.parse(raw)
    assert out[0].symbol == "BTCUSDT" and out[0].event_ts_ms == 1700
    assert out[0].bids == [["65594", "1.2"], ["65593.6", "0.02"]] and out[0].asks == [["65594.1", "4.0"]]


def test_spot_ignores_control_frames():
    c = BybitSpotConnector()
    for raw in (json.dumps({"pong": 123}), json.dumps({"code": 0, "event": "sub"}),
                json.dumps({"event": "error", "desc": "DumpScale error"}),
                json.dumps({"topic": "mergedDepth", "data": []}), "bad{"):
        assert c.parse(raw) is None


def test_spot_subscribe_sends_mergeddepth_with_dumpscale():
    c = BybitSpotConnector()

    async def fake_ds(syms):
        return {s: (1 if s == "BTCUSDT" else 2) for s in syms}

    c._dump_scales = fake_ds
    sent = []

    class _WS:
        async def send(self, m):
            sent.append(json.loads(m))

    asyncio.run(c.subscribe(_WS(), ["BTCUSDT", "SOLUSDT"]))
    btc = next(x for x in sent if x["symbol"] == "BTCUSDT")
    assert btc["topic"] == "mergedDepth" and btc["event"] == "sub" and btc["params"]["dumpScale"] == 1
    assert next(x for x in sent if x["symbol"] == "SOLUSDT")["params"]["dumpScale"] == 2


def test_spot_ping_is_ws2_format():
    p = json.loads(asyncio.run(BybitSpotConnector().ping_message()))
    assert set(p) == {"ping"} and isinstance(p["ping"], int)


def test_spot_ws_url():
    url = asyncio.run(BybitSpotConnector().ws_url())
    assert url.startswith("wss://ws2.bybit.com/spot/ws/quote/v2?_platform=2&tamp=")


# ============================================================ FUTURES (realtime_w)
def _rtw(sym, b, a, typ="snapshot", ts=1000, b1=None, a1=None):
    data = {"s": sym, "b": b, "a": a}
    if b1 is not None:
        data["b1"] = b1
    if a1 is not None:
        data["a1"] = a1
    return json.dumps({"topic": f"orderBook_20@m1.H.{sym}", "type": typ, "ts": ts, "data": data})


def test_futures_snapshot_then_delta():
    c = BybitFuturesConnector()
    c.parse(_rtw("SOLPERP", [["75.04", "10"], ["75.03", "5"]], [["75.06", "8"], ["75.07", "3"]]))
    out = c.parse(_rtw("SOLPERP", [["75.04", "12"], ["75.05", "7"], ["75.03", "0"]], [["75.06", "0"]],
                       typ="delta", ts=2000, b1="75.05", a1="75.07"))
    assert out[0].bids == [["75.05", "7"], ["75.04", "12"]]   # 75.03 removed, 75.05 added, 75.04 updated
    assert out[0].asks == [["75.07", "3"]]                    # 75.06 removed
    assert out[0].event_ts_ms == 2000


def test_futures_gzip_frame_decodes():
    c = BybitFuturesConnector()
    raw = gzip.compress(_rtw("BTCPERP", [["67000", "1"]], [["67001", "2"]]).encode())
    out = c.parse(raw)   # bytes -> gunzip
    assert out[0].symbol == "BTCPERP" and out[0].bids == [["67000", "1"]] and out[0].asks == [["67001", "2"]]


def test_futures_delta_gated_until_snapshot():
    c = BybitFuturesConnector()
    assert c.parse(_rtw("XPERP", [["1", "1"]], [["2", "1"]], typ="delta")) is None
    assert c.parse(_rtw("XPERP", [["1", "1"]], [["2", "1"]])) is not None


def test_futures_b1a1_drift_triggers_resync():
    c = BybitFuturesConnector()
    c.parse(_rtw("SOLPERP", [["75.04", "10"]], [["75.06", "8"]]))
    with pytest.raises(ResyncRequired):  # delta says best bid is 75.05 but our top is 75.04 -> drift
        c.parse(_rtw("SOLPERP", [["75.03", "5"]], [], typ="delta", b1="75.05", a1="75.06"))
    assert c._book["SOLPERP"]["synced"] is False


def test_futures_ignores_control_frames():
    c = BybitFuturesConnector()
    for raw in (json.dumps({"success": True, "ret_msg": "pong"}),
                json.dumps({"topic": "instrument_info.H.SOLPERP", "data": {}}), "bad{"):
        assert c.parse(raw) is None


def test_futures_subscribe_failure_returns_none():
    c = BybitFuturesConnector()
    assert c.parse(json.dumps({"success": False, "ret_msg": "Invalid topic"})) is None


def test_futures_emptied_side_with_b1a1_forces_resync():
    # a delta that empties a side while b1/a1 still names a best price = a missed update -> resync
    # (must NOT silently emit a one-sided book). Regression guard for the empty-side bypass.
    c = BybitFuturesConnector()
    c.parse(_rtw("SOLPERP", [["75.04", "10"]], [["75.06", "8"]]))
    with pytest.raises(ResyncRequired):
        c.parse(_rtw("SOLPERP", [], [["75.06", "0"]], typ="delta", b1="75.04", a1="75.07"))
    assert c._book["SOLPERP"]["synced"] is False


def test_futures_one_sided_book_not_emitted():
    # no b1/a1 to trigger drift, but a side is empty -> suppress (never strand a consumer at 0 depth)
    c = BybitFuturesConnector()
    c.parse(_rtw("SOLPERP", [["75.04", "10"]], [["75.06", "8"]]))
    assert c.parse(_rtw("SOLPERP", [], [["75.06", "0"]], typ="delta")) is None


def test_futures_subscribe_resets_and_chunks():
    c = BybitFuturesConnector()
    c._book["SOLPERP"] = {"b": {"1": "1"}, "a": {}, "synced": True}
    sent = []

    class _WS:
        async def send(self, m):
            sent.append(json.loads(m))

    asyncio.run(c.subscribe(_WS(), [f"S{i}PERP" for i in range(12)] + ["SOLPERP"]))   # 13 symbols
    assert c._book["SOLPERP"] == {"b": {}, "a": {}, "synced": False}
    assert len(sent) == 2 and all(m["op"] == "subscribe" and len(m["args"]) <= 10 for m in sent)
    args = [a for m in sent for a in m["args"]]
    assert args[0] == "orderBook_20@m1.H.S0PERP" and len(args) == 13


def test_futures_ping_and_url():
    p = json.loads(asyncio.run(BybitFuturesConnector().ping_message()))
    assert p["op"] == "ping" and isinstance(p["args"][0], int)
    url = asyncio.run(BybitFuturesConnector().ws_url())
    assert url.startswith("wss://ws2.bybit.com/realtime_w?v=1&timestamp=")
