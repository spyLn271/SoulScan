"""MEXC spot market-data handler: exchangeInfo + 24hr ticker merge, USDT/USDC + status filtering."""
from src.cex_v2.market_data.handlers.mexc import MexcSpotMarketData


def test_spot_merge_filters_and_volume():
    h = MexcSpotMarketData()
    symbols = [
        {"symbol": "BTCUSDT", "quoteAsset": "USDT", "status": "1", "isSpotTradingAllowed": True},
        {"symbol": "ETHUSDC", "quoteAsset": "USDC", "status": "1", "isSpotTradingAllowed": True},
        {"symbol": "BTCEUR", "quoteAsset": "EUR", "status": "1", "isSpotTradingAllowed": True},      # non-USDT/USDC
        {"symbol": "OLDUSDT", "quoteAsset": "USDT", "status": "2", "isSpotTradingAllowed": True},    # status != 1
        {"symbol": "NOSPOTUSDT", "quoteAsset": "USDT", "status": "1", "isSpotTradingAllowed": False},# no spot trading
    ]
    tickers = [
        {"symbol": "BTCUSDT", "bidPrice": "100.1", "askPrice": "100.2", "lastPrice": "100.15", "quoteVolume": "5000"},
        {"symbol": "ETHUSDC", "bidPrice": "50", "askPrice": "50.1", "lastPrice": "50", "quoteVolume": "200"},
        {"symbol": "BTCEUR", "bidPrice": "90", "askPrice": "90.1", "lastPrice": "90", "quoteVolume": "1"},
        {"symbol": "OLDUSDT", "bidPrice": "1", "askPrice": "1.1", "lastPrice": "1", "quoteVolume": "9"},
        {"symbol": "NOSPOTUSDT", "bidPrice": "1", "askPrice": "1.1", "lastPrice": "1", "quoteVolume": "9"},
        {"symbol": "DEADUSDT", "bidPrice": "0", "askPrice": "0", "lastPrice": "0", "quoteVolume": "0"},   # zero-priced
    ]
    out = {r["symbol"]: r["data"] for r in h._merge(symbols, tickers)}
    assert set(out) == {"BTCUSDT", "ETHUSDC"}                  # EUR + non-status1 + no-spot + dead dropped
    assert out["BTCUSDT"]["best_bid"] == "100.1" and out["BTCUSDT"]["lastPrice"] == "100.15"
    assert out["BTCUSDT"]["24h_volume_usdt"] == 5000.0
    assert isinstance(out["BTCUSDT"]["best_bid"], str)
