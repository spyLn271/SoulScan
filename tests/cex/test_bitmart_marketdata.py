"""BitMart market-data: spot symbols+positional-ticker merge; futures contract-details (last-priced)."""
from src.cex.market_data.handlers.bitmart import BitmartSpotMarketData, BitmartFuturesMarketData


def test_spot_merge_positional_tickers():
    h = BitmartSpotMarketData()
    symbols = [
        {"symbol": "BTC_USDT", "quote_currency": "USDT", "trade_status": "trading"},
        {"symbol": "ETH_USDC", "quote_currency": "USDC", "trade_status": "trading"},
        {"symbol": "DOGE_BTC", "quote_currency": "BTC", "trade_status": "trading"},   # non-USDT/USDC
        {"symbol": "OLD_USDT", "quote_currency": "USDT", "trade_status": "pre-trade"},# not trading
    ]
    # ticker array: [sym,last,v24,qv24,open,high,low,fluct,bidPx,bidSz,askPx,askSz,ts]
    tickers = [
        ["BTC_USDT", "100.1", "5", "5000", "9", "9", "9", "0", "100.0", "1", "100.2", "1", "1"],
        ["ETH_USDC", "50", "2", "200", "9", "9", "9", "0", "49.9", "1", "50.1", "1", "1"],
        ["DOGE_BTC", "1", "1", "9", "9", "9", "9", "0", "1", "1", "1.1", "1", "1"],
        ["OLD_USDT", "1", "1", "9", "9", "9", "9", "0", "1", "1", "1.1", "1", "1"],
        ["DEAD_USDT", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "1"],   # zero-priced (not in meta anyway)
    ]
    out = {r["symbol"]: r["data"] for r in h._merge(symbols, tickers)}
    assert set(out) == {"BTCUSDT", "ETHUSDC"}                  # BTC-quote + pre-trade dropped
    assert out["BTCUSDT"]["best_bid"] == "100.0" and out["BTCUSDT"]["best_ask"] == "100.2"
    assert out["BTCUSDT"]["lastPrice"] == "100.1" and out["BTCUSDT"]["24h_volume_usdt"] == 5000.0


def test_futures_details_last_priced():
    h = BitmartFuturesMarketData()
    resp = {"data": {"symbols": [
        {"symbol": "BTCUSDT", "quote_currency": "USDT", "status": "Trading", "last_price": "100.5",
         "index_price": "100.4", "turnover_24h": "9000", "funding_rate": "0.0001",
         "funding_time": "1781700000000", "open_interest": "1234", "contract_size": "0.001"},
        {"symbol": "ETHUSDC", "quote_currency": "USDC", "status": "Trading", "last_price": "50",
         "turnover_24h": "300"},
        {"symbol": "XUSD", "quote_currency": "USD", "status": "Trading", "last_price": "1"},   # inverse
        {"symbol": "OFFUSDT", "quote_currency": "USDT", "status": "Delisted", "last_price": "1"},
    ]}}
    out = {r["symbol"]: r["data"] for r in h.parse_api_response(resp)}
    assert set(out) == {"BTCUSDT", "ETHUSDC"}                  # USD inverse + delisted dropped
    assert out["BTCUSDT"]["best_bid"] is None and out["BTCUSDT"]["lastPrice"] == "100.5"
    assert out["BTCUSDT"]["indexPrice"] == "100.4"
    assert abs(out["BTCUSDT"]["funding_rate_percent"] - 0.01) < 1e-9
    assert out["BTCUSDT"]["next_funding_time"] == 1781700000   # ms -> s
    assert out["BTCUSDT"]["contract_size"] == "0.001"


def test_futures_bad_funding_time_keeps_batch():
    h = BitmartFuturesMarketData()
    resp = {"data": {"symbols": [
        {"symbol": "BTCUSDT", "quote_currency": "USDT", "status": "Trading", "last_price": "100",
         "funding_time": "not-a-number"},                       # malformed -> must NOT drop the whole batch
        {"symbol": "ETHUSDT", "quote_currency": "USDT", "status": "Trading", "last_price": "50",
         "funding_time": "1781700000000"},
    ]}}
    out = {r["symbol"]: r["data"] for r in h.parse_api_response(resp)}
    assert out["BTCUSDT"]["next_funding_time"] is None          # bad funding_time -> None, row kept
    assert out["ETHUSDT"]["next_funding_time"] == 1781700000    # sibling unaffected (batch survived)
