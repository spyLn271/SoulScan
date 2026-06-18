"""BingX market-data handlers: spot symbols+ticker merge, futures contracts+ticker+premium merge,
USDT/USDC + status filtering, dash->canonical, numeric prices stringified."""
from src.cex_v2.market_data.handlers.bingx import BingxSpotMarketData, BingxFuturesMarketData


def test_spot_merge_filters_and_stringifies():
    h = BingxSpotMarketData()
    symbols = [
        {"symbol": "BTC-USDT", "status": 1},
        {"symbol": "ETH-USDC", "status": 1},
        {"symbol": "DOGE-TRY", "status": 1},     # non-USDT/USDC
        {"symbol": "OLD-USDT", "status": 0},     # not trading
    ]
    tickers = [
        {"symbol": "BTC-USDT", "bidPrice": 65796.0, "askPrice": 65796.01, "lastPrice": 65796.0, "quoteVolume": 1.8e8},
        {"symbol": "ETH-USDC", "bidPrice": 1775.0, "askPrice": 1775.1, "lastPrice": 1775.0, "quoteVolume": 2e6},
        {"symbol": "DOGE-TRY", "bidPrice": 1, "askPrice": 1.1, "lastPrice": 1, "quoteVolume": 9},
        {"symbol": "OLD-USDT", "bidPrice": 1, "askPrice": 1.1, "lastPrice": 1, "quoteVolume": 9},
        {"symbol": "DEAD-USDT", "bidPrice": 0, "askPrice": 0, "lastPrice": 0, "quoteVolume": 0},  # zero-priced
    ]
    out = {r["symbol"]: r["data"] for r in h._merge(symbols, tickers)}
    assert set(out) == {"BTCUSDT", "ETHUSDC"}                 # TRY + non-trading + dead dropped; dash stripped
    assert out["BTCUSDT"]["best_bid"] == "65796.0"           # numeric -> string
    assert isinstance(out["BTCUSDT"]["best_ask"], str)
    assert out["BTCUSDT"]["24h_volume_usdt"] == 1.8e8


def test_futures_merge_with_funding_and_mark():
    h = BingxFuturesMarketData()
    contracts = [
        {"symbol": "BTC-USDT", "status": 1, "currency": "USDT"},
        {"symbol": "ETH-USDC", "status": 1, "currency": "USDC"},
        {"symbol": "X-USD", "status": 1, "currency": "USD"},     # inverse -> excluded
        {"symbol": "OFF-USDT", "status": 0, "currency": "USDT"}, # not trading
    ]
    tickers = [
        {"symbol": "BTC-USDT", "bidPrice": 100, "askPrice": 100.1, "lastPrice": 100, "quoteVolume": 9000},
        {"symbol": "ETH-USDC", "bidPrice": 50, "askPrice": 50.1, "lastPrice": 50, "quoteVolume": 300},
        {"symbol": "X-USD", "bidPrice": 1, "askPrice": 1.1, "lastPrice": 1, "quoteVolume": 1},
        {"symbol": "OFF-USDT", "bidPrice": 1, "askPrice": 1.1, "lastPrice": 1, "quoteVolume": 1},
    ]
    premium = [{"symbol": "BTC-USDT", "markPrice": 100.05, "indexPrice": 100.02,
                "lastFundingRate": 0.0001, "nextFundingTime": 1781600000000}]
    out = {r["symbol"]: r["data"] for r in h._merge(contracts, tickers, premium)}
    assert set(out) == {"BTCUSDT", "ETHUSDC"}                 # USD inverse + non-trading dropped
    assert out["BTCUSDT"]["markPrice"] == "100.05" and out["BTCUSDT"]["indexPrice"] == "100.02"
    assert abs(out["BTCUSDT"]["funding_rate_percent"] - 0.01) < 1e-9
    assert out["BTCUSDT"]["next_funding_time"] == 1781600000   # ms -> s
    assert out["ETHUSDC"]["markPrice"] is None                # no premium row -> None, still listed
