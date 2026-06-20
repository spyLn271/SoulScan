"""Bybit market-data handlers: spot + futures parse, string prices, funding math, ms->s, filters."""
import fakeredis

from src.cex.market_data.handlers.bybit import BybitSpotMarketData, BybitFuturesMarketData


def _spot():
    h = BybitSpotMarketData(); h.redis = fakeredis.FakeStrictRedis(decode_responses=True); return h


def _fut():
    h = BybitFuturesMarketData(); h.redis = fakeredis.FakeStrictRedis(decode_responses=True); return h


def _env(lst, ret=0):
    return {"retCode": ret, "result": {"list": lst}}


def test_spot_parse_strings_usdc_volume_and_filters():
    out = _spot().parse_api_response(_env([
        {"symbol": "BTCUSDT", "bid1Price": "60000.1", "ask1Price": "60000.2", "lastPrice": "60000.1", "turnover24h": "100"},
        {"symbol": "ETHUSDC", "bid1Price": "3000.5", "ask1Price": "3000.6", "lastPrice": "3000.5", "turnover24h": "50"},
        {"symbol": "FOOBTC", "bid1Price": "1", "ask1Price": "2", "lastPrice": "1", "turnover24h": "1"},      # non USDT/USDC -> drop
        {"symbol": "BADUSDT", "bid1Price": None, "ask1Price": "2", "lastPrice": "1", "turnover24h": "1"},     # malformed -> drop
        {"symbol": "DEADUSDT", "bid1Price": "0", "ask1Price": "0", "lastPrice": "0", "turnover24h": "0"},     # zero -> drop
    ]))
    assert {o["symbol"] for o in out} == {"BTCUSDT", "ETHUSDC"}          # USDC kept
    btc = next(o for o in out if o["symbol"] == "BTCUSDT")["data"]
    assert btc["best_bid"] == "60000.1" and isinstance(btc["best_bid"], str)
    assert isinstance(btc["24h_volume_usdt"], float) and btc["24h_volume_usdt"] == 100.0


def test_spot_bad_shape_returns_empty():
    h = _spot()
    assert h.parse_api_response({"retCode": 1, "result": {"list": []}}) == []      # error envelope
    assert h.parse_api_response([]) == []
    assert h.parse_api_response({"foo": "bar"}) == []
    assert h.parse_api_response({"retCode": 0, "result": "notadict"}) == []        # non-dict result
    assert h.parse_api_response({"retCode": 0, "result": {"list": "notalist"}}) == []


def test_futures_funding_math_ms_to_s_index_mark():
    out = _fut().parse_api_response(_env([
        {"symbol": "BTCUSDT", "bid1Price": "64000", "ask1Price": "64001", "lastPrice": "64000",
         "turnover24h": "1000", "indexPrice": "63999", "markPrice": "64000.5",
         "fundingRate": "0.0001", "nextFundingTime": "1781460000000", "deliveryTime": "0"},
    ]))
    d = out[0]["data"]
    assert out[0]["symbol"] == "BTCUSDT"
    assert d["best_bid"] == "64000" and d["indexPrice"] == "63999" and d["markPrice"] == "64000.5"
    assert abs(d["funding_rate_percent"] - 0.01) < 1e-9   # 0.0001 * 100
    assert d["next_funding_time"] == 1781460000           # ms -> s


def test_futures_drops_dated_delivery_and_zero():
    out = _fut().parse_api_response(_env([
        {"symbol": "PERPUSDT", "bid1Price": "1", "ask1Price": "2", "lastPrice": "1", "turnover24h": "1",
         "fundingRate": "0", "nextFundingTime": "1", "deliveryTime": "0"},
        {"symbol": "DATEDUSDT", "bid1Price": "1", "ask1Price": "2", "lastPrice": "1", "turnover24h": "1",
         "deliveryTime": "1735689600000"},   # dated future -> drop
        {"symbol": "ZEROUSDT", "bid1Price": "0", "ask1Price": "0", "lastPrice": "0", "turnover24h": "1",
         "deliveryTime": "0"},               # zero-priced -> drop
    ]))
    assert {o["symbol"] for o in out} == {"PERPUSDT"}


def test_futures_keeps_usdc_perp_named_perp():
    out = _fut().parse_api_response(_env([
        {"symbol": "BTCPERP", "bid1Price": "64000", "ask1Price": "64001", "lastPrice": "64000",
         "turnover24h": "5", "fundingRate": "0.0001", "nextFundingTime": "1781460000000", "deliveryTime": "0"},
        {"symbol": "ETHUSDT", "bid1Price": "3000", "ask1Price": "3001", "lastPrice": "3000",
         "turnover24h": "5", "fundingRate": "0", "nextFundingTime": "1", "deliveryTime": "0"},
    ]))
    assert {o["symbol"] for o in out} == {"BTCPERP", "ETHUSDT"}   # USDC perp (<BASE>PERP) NOT dropped


def test_redis_key_wiring():
    assert _spot().redis_key == "spot-market-data:bybit"
    assert _fut().redis_key == "futures-market-data:bybit"
