"""KuCoin md handlers: spot allTickers (BBO/filter/wire) + futures contracts/active x allTickers merge
(multiplier, XBT->BTC canonical, inverse/non-open/quote filters, wire, null-BBO when a contract lacks a ticker)."""
from src.cex.market_data.handlers.kucoin import KucoinSpotMarketData, KucoinFuturesMarketData


def test_spot_md_bbo_filter_wire():
    h = object.__new__(KucoinSpotMarketData)   # parse_api_response is pure; skip __init__ (redis/config)
    resp = {"data": {"ticker": [
        {"symbol": "BTC-USDT", "buy": "100", "sell": "101", "last": "100.5", "volValue": "123"},
        {"symbol": "FOO-BTC", "buy": "1", "sell": "2", "last": "1.5", "volValue": "9"},     # non USDT/USDC quote -> drop
        {"symbol": "BAD-USDT", "buy": "0", "sell": "5", "last": "5", "volValue": "9"},       # no bid -> drop
    ]}}
    out = {r["symbol"]: r["data"] for r in h.parse_api_response(resp)}
    assert set(out) == {"BTCUSDT"}
    d = out["BTCUSDT"]
    assert d["best_bid"] == "100" and d["best_ask"] == "101" and d["wire"] == "BTC-USDT"


def test_futures_md_merge_multiplier_canonical_filters():
    h = object.__new__(KucoinFuturesMarketData)
    contracts = {"data": [
        {"symbol": "XBTUSDTM", "baseCurrency": "XBT", "quoteCurrency": "USDT", "multiplier": 0.001,
         "markPrice": 100, "indexPrice": 101, "fundingFeeRate": 0.0001, "turnoverOf24h": 9,
         "isInverse": False, "status": "Open"},
        {"symbol": "XBTUSDM", "baseCurrency": "XBT", "quoteCurrency": "USD", "multiplier": 1,
         "isInverse": True, "status": "Open"},                                       # inverse + USD quote -> drop
        {"symbol": "ETHUSDTM", "baseCurrency": "ETH", "quoteCurrency": "USDT", "multiplier": 0.01,
         "markPrice": 3, "isInverse": False, "status": "Open"},                      # present in contracts, ABSENT from tickers
        {"symbol": "DEADUSDTM", "baseCurrency": "DEAD", "quoteCurrency": "USDT", "multiplier": 1,
         "isInverse": False, "status": "Paused"},                                    # not Open -> drop
    ]}
    tickers = {"data": [{"symbol": "XBTUSDTM", "bestBidPrice": "99", "bestAskPrice": "100", "price": "99.5"}]}
    out = {r["symbol"]: r["data"] for r in h.parse_api_response(contracts, tickers)}
    assert set(out) == {"BTCUSDT", "ETHUSDT"}                                        # XBT->BTC; inverse + paused dropped
    assert out["BTCUSDT"]["multiplier"] == "0.001" and out["BTCUSDT"]["wire"] == "XBTUSDTM"
    assert out["BTCUSDT"]["best_bid"] == "99" and out["BTCUSDT"]["best_ask"] == "100"
    # a contract missing from /allTickers is still published (OB needs multiplier+wire) with null BBO
    assert out["ETHUSDT"]["best_bid"] is None and out["ETHUSDT"]["multiplier"] == "0.01" and out["ETHUSDT"]["wire"] == "ETHUSDTM"


def test_futures_md_drops_contract_without_multiplier():
    h = object.__new__(KucoinFuturesMarketData)
    contracts = {"data": [
        {"symbol": "NOMULTUSDTM", "baseCurrency": "NOMULT", "quoteCurrency": "USDT", "multiplier": 0,
         "isInverse": False, "status": "Open"},   # multiplier 0 -> OB couldn't scale -> drop
    ]}
    assert h.parse_api_response(contracts, {"data": []}) == []
