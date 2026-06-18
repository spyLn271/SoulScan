"""cex_v2 choosability: CLI parsing, market/exchange selection in discovery, binance futures parse."""
import json

import pytest

from src.cex_v2.cli import parse_markets, parse_exchanges
from src.cex_v2.supervisor import _discover as discover_ob
from src.cex_v2.market_data.manager import _discover as discover_md
from src.cex_v2.plugins.binance import BinanceSpotConnector, BinanceFuturesConnector


def test_cli_parse_markets():
    assert parse_markets("spot") == ("spot",)
    assert parse_markets("futures") == ("futures",)
    assert parse_markets("both") == ("spot", "futures")
    import argparse
    with pytest.raises(argparse.ArgumentTypeError):
        parse_markets("perp")


def test_cli_parse_exchanges():
    assert parse_exchanges("all") is None
    assert parse_exchanges("binance, bybit ,OKX") == ["binance", "bybit", "okx"]


def _names(targets):
    return sorted(t.name for t in targets)


def test_orderbook_discovery_by_market():
    assert "binance_spot" in _names(discover_ob(("spot",)))
    assert "binance_futures" in _names(discover_ob(("futures",)))
    assert {"binance_spot", "binance_futures"} <= set(_names(discover_ob(("spot", "futures"))))


def test_orderbook_discovery_by_exchange():
    assert _names(discover_ob(("spot",), exchanges=["bybit"])) == ["bybit_spot"]   # bybit now onboarded
    assert _names(discover_ob(("spot", "futures"), exchanges=["binance"])) == ["binance_futures", "binance_spot"]
    fut = discover_ob(("futures",), exchanges=["binance"])
    assert fut[0].class_name == "BinanceFuturesConnector" and fut[0].market_type == "futures"


def test_marketdata_discovery_filters():
    assert ("binance", "spot") in discover_md(("spot",))
    assert ("binance", "futures") in discover_md(("futures",))
    assert discover_md(("spot",), exchanges=["bybit"]) == [("bybit", "spot")]


def test_binance_futures_parse_uses_b_a_s_E():
    f = BinanceFuturesConnector()
    raw = json.dumps({"stream": "btcusdt@depth20@100ms",
                      "data": {"e": "depthUpdate", "E": 1781433994841, "s": "BTCUSDT",
                               "b": [["64537.10", "1.138"]], "a": [["64538.00", "0.5"]]}})
    books = f.parse(raw)
    assert books and books[0].symbol == "BTCUSDT"
    assert books[0].bids == [["64537.10", "1.138"]] and books[0].asks == [["64538.00", "0.5"]]
    assert books[0].event_ts_ms == 1781433994841           # futures carries exchange event ts


def test_binance_spot_parse_still_uses_bids_asks():
    s = BinanceSpotConnector()
    raw = json.dumps({"stream": "ethusdt@depth20@100ms", "data": {"bids": [["3000", "1"]], "asks": [["3001", "1"]]}})
    books = s.parse(raw)
    assert books and books[0].symbol == "ETHUSDT" and books[0].bids == [["3000", "1"]]
    assert books[0].event_ts_ms is None                    # spot has no event ts -> core stamps recv
