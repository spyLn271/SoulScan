"""CoinEx order-book plugin (v1 website feed): gzip frames; depth.subscribe_multi (REPLACE, one call/conn);
clean snapshot then PURE diffs (amount 0 = remove); crc32-checksum resync; symbols already canonical;
spot + futures identical protocol (ws.coinex.com / perpetual.coinex.com); futures base-asset."""
import asyncio
import gzip
import json

import pytest

from src.cex_v2.core.connector import ResyncRequired
from src.cex_v2.plugins.coinex import CoinexSpotConnector, CoinexFuturesConnector, _checksum


def _cs(bids, asks):
    bd = sorted(([p, a] for p, a in bids), key=lambda x: -float(x[0]))
    aa = sorted(([p, a] for p, a in asks), key=lambda x: float(x[0]))
    return _checksum(bd, aa)


def _frame(market, bids, asks, clean=True, t=1700, checksum=None, gz=False):
    d = {"asks": asks, "bids": bids, "last": "100", "time": t}
    if checksum is not None:
        d["checksum"] = checksum
    msg = json.dumps({"method": "depth.update", "id": None, "params": [clean, d, market]})
    return gzip.compress(msg.encode()) if gz else msg


def test_full_snapshot_emits_sorted():
    c = CoinexSpotConnector()
    out = c.parse(_frame("BTCUSDT", [["99", "2"], ["100", "1"]], [["102", "4"], ["101", "3"]], gz=True))
    assert out[0].symbol == "BTCUSDT" and out[0].event_ts_ms == 1700
    assert out[0].bids == [["100", "1"], ["99", "2"]]    # bids descending
    assert out[0].asks == [["101", "3"], ["102", "4"]]   # asks ascending


def test_gzip_and_plaintext_both_parse():
    c = CoinexSpotConnector()
    assert c.parse(_frame("ETHUSDT", [["10", "1"]], [["11", "1"]], gz=True))[0].symbol == "ETHUSDT"
    assert c.parse(_frame("ETHUSDT", [["10", "1"]], [["11", "1"]], gz=False))[0].symbol == "ETHUSDT"


def test_incremental_diff_merge_and_remove():
    c = CoinexSpotConnector()
    c.parse(_frame("BTCUSDT", [["100", "1"], ["99", "5"]], [["101", "2"], ["102", "3"]], clean=True))
    out = c.parse(_frame("BTCUSDT", [["100", "0"], ["98", "7"]], [["101", "9"]], clean=False))
    assert out[0].bids == [["99", "5"], ["98", "7"]]     # 100 removed (0), 98 added, 99 kept
    assert out[0].asks == [["101", "9"], ["102", "3"]]   # 101 updated, 102 kept


def test_diff_before_snapshot_ignored():
    c = CoinexSpotConnector()
    assert c.parse(_frame("BTCUSDT", [["100", "1"]], [["101", "1"]], clean=False)) is None  # no snapshot yet
    assert c.parse(_frame("BTCUSDT", [["100", "1"]], [["101", "1"]], clean=True))[0].symbol == "BTCUSDT"


def test_checksum_match_emits_mismatch_resyncs():
    c = CoinexSpotConnector()
    bids = [["100", "1"], ["99", "5"]]; asks = [["101", "2"], ["102", "3"]]
    out = c.parse(_frame("BTCUSDT", bids, asks, clean=True, checksum=_cs(bids, asks)))
    assert out[0].symbol == "BTCUSDT"                    # valid checksum -> emits
    c2 = CoinexSpotConnector()
    with pytest.raises(ResyncRequired):                 # wrong checksum -> resync
        c2.parse(_frame("BTCUSDT", bids, asks, clean=True, checksum=_cs(bids, asks) + 1))
    assert c2._book["BTCUSDT"]["synced"] is False


def test_crossed_and_one_sided_suppressed():
    c = CoinexSpotConnector()
    assert c.parse(_frame("BTCUSDT", [["105", "1"]], [["104", "1"]])) is None   # crossed
    assert c.parse(_frame("BTCUSDT", [["100", "1"]], [])) is None               # one-sided


def test_malformed_level_does_not_crash():
    c = CoinexSpotConnector()
    out = c.parse(_frame("BTCUSDT", [["100", "1"], ["99"], ["98", "2", "x"]], [["101", "3"]]))
    assert out[0].bids == [["100", "1"], ["98", "2"]] and out[0].asks == [["101", "3"]]


def test_non_numeric_price_skipped_not_stored():
    c = CoinexSpotConnector()   # a corrupt price must be skipped (else it crashes the float-sort forever)
    out = c.parse(_frame("BTCUSDT", [["100", "1"], ["oops", "9"]], [["101", "3"]]))
    assert out[0].bids == [["100", "1"]] and "oops" not in c._book["BTCUSDT"]["b"]


def test_malformed_time_still_emits():
    c = CoinexSpotConnector()
    out = c.parse(_frame("BTCUSDT", [["100", "1"]], [["101", "1"]], t="bad"))
    assert out[0].event_ts_ms is None and out[0].symbol == "BTCUSDT"


def test_ack_and_error_ignored():
    c = CoinexSpotConnector()
    assert c.parse(json.dumps({"id": 1, "result": {"status": "success"}, "error": None})) is None
    assert c.parse(json.dumps({"id": 1, "error": {"code": 1, "message": "bad"}})) is None


def test_subscribe_multi_one_call_all_markets():
    c = CoinexSpotConnector(); sent = []

    class _WS:
        async def send(self, m): sent.append(json.loads(m))
    syms = ["BTCUSDT", "ETHUSDT", "SOLUSDC"]
    asyncio.run(c.subscribe(_WS(), syms))
    assert len(sent) == 1 and sent[0]["method"] == "depth.subscribe_multi"     # ONE call, REPLACE semantics
    assert sent[0]["params"] == [["BTCUSDT", 50, "0"], ["ETHUSDT", 50, "0"], ["SOLUSDC", 50, "0"]]
    assert json.loads(asyncio.run(c.ping_message())) == {"id": 1, "method": "server.ping", "params": []}


def test_ws_urls_spot_vs_futures():
    assert asyncio.run(CoinexSpotConnector().ws_url()) == "wss://ws.coinex.com/"
    assert asyncio.run(CoinexFuturesConnector().ws_url()) == "wss://perpetual.coinex.com/"


def test_futures_sizes_pass_through_base_asset():
    c = CoinexFuturesConnector()   # CoinEx linear futures depth is base-asset -> amounts unchanged
    out = c.parse(_frame("BTCUSDT", [["100", "1.0414"]], [["101", "0.5"]]))
    assert out[0].bids == [["100", "1.0414"]] and out[0].asks == [["101", "0.5"]]
