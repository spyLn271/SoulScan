"""OKX order-book plugin (documented `books` channel: snapshot+update, size 0 = remove, CRC32
checksum integrity, instId<->canonical mapping). Spot + futures share _OkxBase."""
import asyncio
import json

import pytest

from src.cex_v2.core.connector import ResyncRequired
from src.cex_v2.plugins.okx import OkxSpotConnector, OkxFuturesConnector, _okx_checksum


def _msg(instId, bids, asks, action="snapshot", ts="1000", checksum=None):
    d = {"asks": asks, "bids": bids, "ts": ts}
    if checksum is not None:
        d["checksum"] = checksum
    return json.dumps({"arg": {"channel": "books", "instId": instId}, "action": action, "data": [d]})


def _lv(px, sz):
    return [px, sz, "0", "1"]   # OKX level shape [px, sz, deprecated, orderCount]


def test_snapshot_then_update_merges():
    c = OkxSpotConnector()
    c._inst2canon["BTC-USDT"] = "BTCUSDT"
    c.parse(_msg("BTC-USDT", [_lv("100", "1"), _lv("99", "5")], [_lv("101", "2"), _lv("102", "3")]))
    out = c.parse(_msg("BTC-USDT", [_lv("100", "0")], [_lv("101", "4")], action="update"))
    assert out[0].symbol == "BTCUSDT"
    assert out[0].bids == [["99", "5"]]                  # 100 removed (size 0)
    assert out[0].asks == [["101", "4"], ["102", "3"]]   # 101 updated, 102 kept
    assert out[0].event_ts_ms == 1000


def test_futures_sizes_scaled_by_ctval():
    c = OkxFuturesConnector()
    c._inst2canon["BTC-USDT-SWAP"] = "BTCUSDT"
    c._mult["BTCUSDT"] = 0.01                                  # ctVal: 1 contract = 0.01 BTC
    out = c.parse(_msg("BTC-USDT-SWAP", [_lv("100", "5"), _lv("99", "10")], [_lv("101", "3")]))
    assert out[0].bids[0][0] == "100" and abs(out[0].bids[0][1] - 0.05) < 1e-12   # 5 contracts -> 0.05 BTC
    assert abs(out[0].bids[1][1] - 0.10) < 1e-12
    assert abs(out[0].asks[0][1] - 0.03) < 1e-12


def test_spot_sizes_not_scaled():
    c = OkxSpotConnector()                                     # spot has no ctVal -> _mult empty -> unchanged
    c._inst2canon["BTC-USDT"] = "BTCUSDT"
    out = c.parse(_msg("BTC-USDT", [_lv("100", "5")], [_lv("101", "3")]))
    assert out[0].bids[0] == ["100", "5"] and out[0].asks[0] == ["101", "3"]   # strings, untouched


def test_checksum_uses_raw_sizes_despite_ctval():
    c = OkxFuturesConnector()
    c._inst2canon["BTC-USDT-SWAP"] = "BTCUSDT"
    c._mult["BTCUSDT"] = 0.01
    c.parse(_msg("BTC-USDT-SWAP", [_lv("100", "1")], [_lv("101", "2")]))
    good = _okx_checksum([("100", "3")], [("101", "2")])       # checksum over RAW contract sizes
    out = c.parse(_msg("BTC-USDT-SWAP", [_lv("100", "3")], [], action="update", checksum=good))
    assert out is not None                                     # raw-size checksum still matches
    assert abs(out[0].bids[0][1] - 0.03) < 1e-12              # ...yet emitted size is scaled (3 * 0.01)


def test_update_gated_until_snapshot():
    c = OkxSpotConnector()
    c._inst2canon["BTC-USDT"] = "BTCUSDT"
    assert c.parse(_msg("BTC-USDT", [_lv("1", "1")], [_lv("2", "1")], action="update")) is None
    assert c.parse(_msg("BTC-USDT", [_lv("1", "1")], [_lv("2", "1")])) is not None


def test_checksum_match_emits_mismatch_resyncs():
    c = OkxSpotConnector()
    c._inst2canon["BTC-USDT"] = "BTCUSDT"
    c.parse(_msg("BTC-USDT", [_lv("100", "1")], [_lv("101", "2")]))
    good = _okx_checksum([("100", "3")], [("101", "2")])   # book after the update below
    out = c.parse(_msg("BTC-USDT", [_lv("100", "3")], [], action="update", checksum=good))
    assert out[0].bids == [["100", "3"]] and out[0].asks == [["101", "2"]]
    # now a delta whose declared checksum disagrees with our merged book -> resync
    with pytest.raises(ResyncRequired):
        c.parse(_msg("BTC-USDT", [_lv("100", "9")], [], action="update", checksum=good + 1))
    assert c._book["BTCUSDT"]["synced"] is False


def test_one_sided_book_not_emitted():
    c = OkxSpotConnector()
    c._inst2canon["BTC-USDT"] = "BTCUSDT"
    # snapshot with only bids -> empty asks -> suppress
    assert c.parse(_msg("BTC-USDT", [_lv("100", "1")], [])) is None


def test_instid_to_canonical_spot_and_swap():
    c = OkxFuturesConnector()
    c._inst2canon["BTC-USDT-SWAP"] = "BTCUSDT"
    out = c.parse(_msg("BTC-USDT-SWAP", [_lv("100", "1")], [_lv("101", "1")]))
    assert out[0].symbol == "BTCUSDT"
    # fallback when instId not pre-mapped: normalize_symbol strips -SWAP and dashes
    c2 = OkxFuturesConnector()
    out2 = c2.parse(_msg("SOL-USDT-SWAP", [_lv("1", "1")], [_lv("2", "1")]))
    assert out2[0].symbol == "SOLUSDT"


def test_normalize_symbol():
    c = OkxSpotConnector()
    assert c.normalize_symbol("BTC-USDT") == "BTCUSDT"
    assert c.normalize_symbol("BTC-USDT-SWAP") == "BTCUSDT"
    assert c.normalize_symbol("BTCUSDT") == "BTCUSDT"


def test_ignores_control_frames():
    c = OkxSpotConnector()
    for raw in ("pong",
                json.dumps({"event": "subscribe", "arg": {"channel": "books", "instId": "BTC-USDT"}}),
                json.dumps({"event": "error", "msg": "bad", "code": "60012"}),
                json.dumps({"arg": {"channel": "tickers", "instId": "BTC-USDT"}, "data": [{}]}),
                "not json{"):
        assert c.parse(raw) is None


def test_subscribe_resolves_instid_and_chunks():
    c = OkxSpotConnector()
    c.sub_chunk = 2

    async def fake_instids(syms):
        return {s: ("BTC-USDT" if s == "BTCUSDT" else f"{s[:-4]}-USDT") for s in syms}
    c._inst_ids = fake_instids
    sent = []

    class _WS:
        async def send(self, m):
            sent.append(json.loads(m))

    asyncio.run(c.subscribe(_WS(), ["BTCUSDT", "ETHUSDT", "SOLUSDT"]))
    args = [a for m in sent for a in m["args"]]
    assert all(m["op"] == "subscribe" and len(m["args"]) <= 2 for m in sent)   # chunked
    assert {a["instId"] for a in args} == {"BTC-USDT", "ETH-USDT", "SOL-USDT"}
    assert all(a["channel"] == "books" for a in args)
    assert c._inst2canon["BTC-USDT"] == "BTCUSDT"        # reverse map populated
    assert c._book["BTCUSDT"] == {"b": {}, "a": {}, "synced": False}   # reset for clean resync


def test_corrupt_price_dropped_no_crash():
    # a non-numeric price in a delta must be dropped, not persisted (else the heapq float() sort
    # would crash on every later frame). parse() must keep working.
    c = OkxSpotConnector()
    c._inst2canon["BTC-USDT"] = "BTCUSDT"
    c.parse(_msg("BTC-USDT", [_lv("100", "1")], [_lv("101", "2")]))
    out = c.parse(_msg("BTC-USDT", [["oops", "5", "0", "1"]], [_lv("102", "3")], action="update"))
    assert "oops" not in c._book["BTCUSDT"]["b"]              # corrupt level not stored
    assert out[0].bids == [["100", "1"]]                      # good levels intact, no crash
    assert out[0].asks == [["101", "2"], ["102", "3"]]


def test_ping_and_ws_url():
    c = OkxSpotConnector()
    assert asyncio.run(c.ping_message()) == "ping"
    assert asyncio.run(c.ws_url()) == "wss://ws.okx.com:8443/ws/v5/public"
