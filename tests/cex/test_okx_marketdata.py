"""OKX market-data handlers: instrument+ticker(+mark) merge, canonical key + instId field,
USDT/USDC filtering (quoteCcy spot / settleCcy linear futures), state + zero-price hygiene."""
from src.cex.market_data.handlers.okx import OkxSpotMarketData, OkxFuturesMarketData


def test_spot_merge_filters_and_maps():
    h = OkxSpotMarketData()
    instruments = [
        {"instId": "BTC-USDT", "baseCcy": "BTC", "quoteCcy": "USDT", "state": "live"},
        {"instId": "ETH-USDC", "baseCcy": "ETH", "quoteCcy": "USDC", "state": "live"},
        {"instId": "BTC-EUR", "baseCcy": "BTC", "quoteCcy": "EUR", "state": "live"},      # non-USDT/USDC
        {"instId": "OLD-USDT", "baseCcy": "OLD", "quoteCcy": "USDT", "state": "suspend"}, # not live
    ]
    tickers = [
        {"instId": "BTC-USDT", "bidPx": "100.1", "askPx": "100.2", "last": "100.15", "volCcy24h": "5000"},
        {"instId": "ETH-USDC", "bidPx": "50", "askPx": "50.1", "last": "50", "volCcy24h": "200"},
        {"instId": "BTC-EUR", "bidPx": "90", "askPx": "90.1", "last": "90", "volCcy24h": "1"},
        {"instId": "OLD-USDT", "bidPx": "1", "askPx": "1.1", "last": "1", "volCcy24h": "9"},
        {"instId": "DEAD-USDT", "bidPx": "0", "askPx": "0", "last": "0", "volCcy24h": "0"},  # zero-priced
    ]
    out = {r["symbol"]: r["data"] for r in h._merge(instruments, tickers)}
    assert set(out) == {"BTCUSDT", "ETHUSDC"}                         # EUR + suspended + dead dropped
    assert out["BTCUSDT"]["instId"] == "BTC-USDT"                     # subscribe target stored
    assert out["BTCUSDT"]["best_bid"] == "100.1" and out["BTCUSDT"]["lastPrice"] == "100.15"
    assert out["BTCUSDT"]["24h_volume_usdt"] == 5000.0
    assert isinstance(out["BTCUSDT"]["best_bid"], str)               # full-precision string preserved


def test_futures_linear_only_and_contract_meta():
    h = OkxFuturesMarketData()
    instruments = [
        {"instId": "BTC-USDT-SWAP", "instFamily": "BTC-USDT", "settleCcy": "USDT", "state": "live",
         "ctVal": "0.01", "ctValCcy": "BTC"},
        {"instId": "SOL-USDC-SWAP", "instFamily": "SOL-USDC", "settleCcy": "USDC", "state": "live",
         "ctVal": "1", "ctValCcy": "SOL"},
        {"instId": "BTC-USD-SWAP", "instFamily": "BTC-USD", "settleCcy": "BTC", "state": "live",
         "ctVal": "100", "ctValCcy": "USD"},   # INVERSE -> excluded (settleCcy not USDT/USDC)
    ]
    tickers = [
        {"instId": "BTC-USDT-SWAP", "bidPx": "100", "askPx": "100.1", "last": "100", "vol24h": "2000"},
        {"instId": "SOL-USDC-SWAP", "bidPx": "75", "askPx": "75.1", "last": "75", "vol24h": "300"},
        {"instId": "BTC-USD-SWAP", "bidPx": "100", "askPx": "100.1", "last": "100", "vol24h": "9"},
    ]
    mark = [{"instId": "BTC-USDT-SWAP", "markPx": "100.05"}]
    out = {r["symbol"]: r["data"] for r in h._merge(instruments, tickers, mark)}
    assert set(out) == {"BTCUSDT", "SOLUSDC"}                         # inverse BTC-USD-SWAP dropped
    assert out["BTCUSDT"]["instId"] == "BTC-USDT-SWAP"
    assert out["BTCUSDT"]["markPrice"] == "100.05"
    assert out["BTCUSDT"]["ctVal"] == "0.01" and out["BTCUSDT"]["ctValCcy"] == "BTC"
    # USD notional = vol24h(contracts) * ctVal * last = 2000 * 0.01 * 100 = 2000
    assert out["BTCUSDT"]["24h_volume_usdt"] == 2000.0
    assert out["SOLUSDC"]["markPrice"] is None                       # missing mark -> None, still listed


def test_spot_drops_zero_last_and_missing_baseccy():
    h = OkxSpotMarketData()
    instruments = [
        {"instId": "AAA-USDT", "baseCcy": "AAA", "quoteCcy": "USDT", "state": "live"},
        {"instId": "BBB-USDT", "quoteCcy": "USDT", "state": "live"},   # missing baseCcy -> dropped
    ]
    tickers = [
        {"instId": "AAA-USDT", "bidPx": "1", "askPx": "1.1", "last": "0", "volCcy24h": "9"},  # last=0 -> drop
        {"instId": "BBB-USDT", "bidPx": "1", "askPx": "1.1", "last": "1", "volCcy24h": "9"},
    ]
    assert h._merge(instruments, tickers) == []   # both rejected


def test_futures_drops_blank_instfamily():
    h = OkxFuturesMarketData()
    instruments = [{"instId": "X-USDT-SWAP", "instFamily": "", "settleCcy": "USDT", "state": "live",
                    "ctVal": "1", "ctValCcy": "X"}]
    tickers = [{"instId": "X-USDT-SWAP", "bidPx": "1", "askPx": "1.1", "last": "1", "vol24h": "5"}]
    assert h._merge(instruments, tickers, []) == []   # blank instFamily -> no canonical -> skipped
