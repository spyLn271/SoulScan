"""CoinEx market-data: spot market+ticker merge (last-priced, no BBO); futures linear + funding merge."""
from src.cex.market_data.handlers.coinex import CoinexSpotMarketData, CoinexFuturesMarketData


def test_spot_merge_filters_and_last_priced():
    h = CoinexSpotMarketData()
    markets = [
        {"market": "BTCUSDT", "quote_ccy": "USDT", "status": "online", "delisted_at": 0},
        {"market": "ETHUSDC", "quote_ccy": "USDC", "status": "online", "delisted_at": 0},
        {"market": "XMRBTC", "quote_ccy": "BTC", "status": "online", "delisted_at": 0},       # non USDT/USDC
        {"market": "OLDUSDT", "quote_ccy": "USDT", "status": "offline", "delisted_at": 0},    # not online
        {"market": "DEADUSDT", "quote_ccy": "USDT", "status": "online", "delisted_at": 1700},  # delisted
    ]
    tickers = [
        {"market": "BTCUSDT", "last": "65000", "value": "12345.6"},
        {"market": "ETHUSDC", "last": "1800", "value": "50"},
        {"market": "XMRBTC", "last": "0.003", "value": "5"},
        {"market": "OLDUSDT", "last": "1", "value": "1"},
        {"market": "ZEROUSDT", "last": "0", "value": "0"},   # zero-priced (and not in markets)
    ]
    out = {r["symbol"]: r["data"] for r in h._merge(markets, tickers)}
    assert set(out) == {"BTCUSDT", "ETHUSDC"}                 # BTC-quote + offline + delisted dropped
    assert out["BTCUSDT"]["best_bid"] is None and out["BTCUSDT"]["best_ask"] is None
    assert out["BTCUSDT"]["lastPrice"] == "65000" and out["BTCUSDT"]["24h_volume_usdt"] == 12345.6


def test_futures_merge_linear_and_funding():
    h = CoinexFuturesMarketData()
    markets = [
        {"market": "BTCUSDT", "quote_ccy": "USDT", "status": "online", "contract_type": "linear", "delisted_at": 0},
        {"market": "ETHUSDC", "quote_ccy": "USDC", "status": "online", "contract_type": "linear", "delisted_at": 0},
        {"market": "BTCUSD", "quote_ccy": "USD", "status": "online", "contract_type": "inverse", "delisted_at": 0},
    ]
    tickers = [
        {"market": "BTCUSDT", "last": "65000", "index_price": "64990", "mark_price": "65005",
         "value": "99999", "open_interest_volume": "1514.9"},
        {"market": "ETHUSDC", "last": "1800", "index_price": "1799", "mark_price": "1801", "value": "500"},
        {"market": "BTCUSD", "last": "65000", "value": "1"},   # inverse -> dropped
    ]
    funding = [{"market": "BTCUSDT", "latest_funding_rate": "0.0001", "next_funding_time": 1781769600000}]
    out = {r["symbol"]: r["data"] for r in h._merge(markets, tickers, funding)}
    assert set(out) == {"BTCUSDT", "ETHUSDC"}                 # USD inverse dropped
    b = out["BTCUSDT"]
    assert b["best_bid"] is None and b["lastPrice"] == "65000"
    assert b["indexPrice"] == "64990" and b["markPrice"] == "65005"
    assert b["open_interest"] == "1514.9" and b["24h_volume_usdt"] == 99999.0
    assert abs(b["funding_rate_percent"] - 0.01) < 1e-9      # 0.0001 * 100
    assert b["next_funding_time"] == 1781769600              # ms -> s
    # ETHUSDC has no funding row -> rate 0, time None
    assert out["ETHUSDC"]["funding_rate_percent"] == 0.0 and out["ETHUSDC"]["next_funding_time"] is None
