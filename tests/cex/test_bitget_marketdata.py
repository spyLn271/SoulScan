"""Bitget market-data handlers: v2 symbols/contracts + tickers merge, USDT/USDC filtering, futures
linear-only (perpetual) + product-line instType + funding/mark."""
from src.cex.market_data.handlers.bitget import BitgetSpotMarketData, BitgetFuturesMarketData


def test_spot_merge_filters_and_volume():
    h = BitgetSpotMarketData()
    symbols = [
        {"symbol": "BTCUSDT", "baseCoin": "BTC", "quoteCoin": "USDT", "status": "online", "areaSymbol": "no"},
        {"symbol": "ETHUSDC", "baseCoin": "ETH", "quoteCoin": "USDC", "status": "online", "areaSymbol": "no"},
        {"symbol": "BTCEUR", "baseCoin": "BTC", "quoteCoin": "EUR", "status": "online", "areaSymbol": "no"},     # non-USDT/USDC
        {"symbol": "OLDUSDT", "baseCoin": "OLD", "quoteCoin": "USDT", "status": "offline", "areaSymbol": "no"},  # not online
        {"symbol": "RNVDAUSDT", "baseCoin": "rNVDA", "quoteCoin": "USDT", "status": "online", "areaSymbol": "yes"},  # tokenized stock -> no L2 book
    ]
    tickers = [
        {"symbol": "BTCUSDT", "bidPr": "100.1", "askPr": "100.2", "lastPr": "100.15", "usdtVolume": "5000"},
        {"symbol": "ETHUSDC", "bidPr": "50", "askPr": "50.1", "lastPr": "50", "usdtVolume": "200"},
        {"symbol": "BTCEUR", "bidPr": "90", "askPr": "90.1", "lastPr": "90", "usdtVolume": "1"},
        {"symbol": "OLDUSDT", "bidPr": "1", "askPr": "1.1", "lastPr": "1", "usdtVolume": "9"},
        {"symbol": "DEADUSDT", "bidPr": "0", "askPr": "0", "lastPr": "0", "usdtVolume": "0"},   # zero-priced
        {"symbol": "RNVDAUSDT", "bidPr": "180", "askPr": "180.1", "lastPr": "180", "usdtVolume": "9999999"},  # has ticker, no book
    ]
    out = {r["symbol"]: r["data"] for r in h._merge(symbols, tickers)}
    assert set(out) == {"BTCUSDT", "ETHUSDC"}                  # EUR + offline + dead + tokenized-stock dropped
    assert out["BTCUSDT"]["best_bid"] == "100.1" and out["BTCUSDT"]["lastPrice"] == "100.15"
    assert out["BTCUSDT"]["24h_volume_usdt"] == 5000.0
    assert isinstance(out["BTCUSDT"]["best_bid"], str)


def test_futures_linear_perps_with_instType_and_funding():
    h = BitgetFuturesMarketData()
    contracts = {
        "BTCUSDT": ("USDT-FUTURES", {"symbol": "BTCUSDT", "quoteCoin": "USDT", "symbolStatus": "normal",
                                     "symbolType": "perpetual"}),
        "ETHPERP": ("USDC-FUTURES", {"symbol": "ETHPERP", "quoteCoin": "USDC", "symbolStatus": "normal",
                                     "symbolType": "perpetual"}),
        "OLDUSDT": ("USDT-FUTURES", {"symbol": "OLDUSDT", "quoteCoin": "USDT", "symbolStatus": "maintain",
                                     "symbolType": "perpetual"}),    # not normal -> dropped
        "DELUSDT": ("USDT-FUTURES", {"symbol": "DELUSDT", "quoteCoin": "USDT", "symbolStatus": "normal",
                                     "symbolType": "delivery"}),     # not perpetual -> dropped
    }
    tickers = {
        "BTCUSDT": {"symbol": "BTCUSDT", "bidPr": "100", "askPr": "100.1", "lastPr": "100",
                    "usdtVolume": "9000", "markPrice": "100.05", "indexPrice": "100.02",
                    "fundingRate": "0.0001", "holdingAmount": "1234"},
        "ETHPERP": {"symbol": "ETHPERP", "bidPr": "50", "askPr": "50.1", "lastPr": "50", "usdtVolume": "300"},
        "OLDUSDT": {"symbol": "OLDUSDT", "bidPr": "1", "askPr": "1.1", "lastPr": "1", "usdtVolume": "1"},
        "DELUSDT": {"symbol": "DELUSDT", "bidPr": "1", "askPr": "1.1", "lastPr": "1", "usdtVolume": "1"},
    }
    out = {r["symbol"]: r["data"] for r in h._merge(contracts, tickers)}
    assert set(out) == {"BTCUSDT", "ETHPERP"}                  # maintain + delivery dropped
    assert out["BTCUSDT"]["instType"] == "USDT-FUTURES"        # product line for OB subscribe
    assert out["ETHPERP"]["instType"] == "USDC-FUTURES"
    assert out["BTCUSDT"]["markPrice"] == "100.05" and out["BTCUSDT"]["indexPrice"] == "100.02"
    assert abs(out["BTCUSDT"]["funding_rate_percent"] - 0.01) < 1e-9   # 0.0001 * 100
    assert out["BTCUSDT"]["open_interest"] == "1234"
