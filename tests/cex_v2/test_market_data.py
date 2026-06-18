"""cex_v2 market-data invariant tests (from MARKET_DATA_AUDIT.md): never-blank, count-drop guard,
malformed-drop, USDC coverage, string prices."""
import json

import fakeredis

from src.cex_v2.market_data.handlers.binance import BinanceSpotMarketData


def _h():
    h = BinanceSpotMarketData()
    h.redis = fakeredis.FakeStrictRedis(decode_responses=True)
    return h


# --- parser: USDC coverage + malformed-drop + string prices (binance handler) ---
def test_binance_parse_usdc_and_strings_and_drop_malformed():
    h = _h()
    resp = [
        {"symbol": "BTCUSDT", "bidPrice": "60000.1", "askPrice": "60000.2", "lastPrice": "60000.1", "quoteVolume": "100"},
        {"symbol": "ETHUSDC", "bidPrice": "3000.5", "askPrice": "3000.6", "lastPrice": "3000.5", "quoteVolume": "50"},
        {"symbol": "FOOBTC", "bidPrice": "1", "askPrice": "2", "lastPrice": "1", "quoteVolume": "1"},   # non-USDT/USDC -> drop
        {"symbol": "BADUSDT", "bidPrice": None, "askPrice": "2", "lastPrice": "1", "quoteVolume": "1"},  # malformed -> drop
    ]
    out = h.parse_api_response(resp)
    syms = {o["symbol"] for o in out}
    assert syms == {"BTCUSDT", "ETHUSDC"}            # USDC kept (legacy dropped it); non-USDT/USDC + malformed dropped
    btc = next(o for o in out if o["symbol"] == "BTCUSDT")["data"]
    assert btc["best_bid"] == "60000.1" and isinstance(btc["best_bid"], str)   # full-precision string, not float
    assert isinstance(btc["24h_volume_usdt"], float)
    assert h.parse_api_response({"not": "a list"}) == []


# --- core invariant: NEVER blank a populated hash when all records are invalid ---
def test_store_never_blanks_on_all_invalid():
    h = _h()
    h.redis.hset(h.redis_key, "BTCUSDT", json.dumps({"best_bid": "1"}))
    h._last_count = 50
    ok = h._store([{"symbol": "X", "data": None}, {"symbol": None, "data": {}}])  # all invalid
    assert ok is False
    assert h.redis.hget(h.redis_key, "BTCUSDT") is not None   # preserved, not blanked


# --- core invariant: reject a catastrophic count collapse (suspected partial API break) ---
def test_store_rejects_count_collapse():
    h = _h()
    h.redis.hset(h.redis_key, "BTCUSDT", json.dumps({"best_bid": "1"}))
    h._last_count = 100
    ok = h._store([{"symbol": "AAAUSDT", "data": {"best_bid": "1", "best_ask": "2", "lastPrice": "1.5"}}])  # 1 << 50
    assert ok is False
    assert h.redis.hget(h.redis_key, "BTCUSDT") is not None   # preserved


# --- core: a good batch writes atomically + stamps _version + tracks last_count ---
def test_store_writes_good_batch():
    h = _h()
    batch = [{"symbol": f"S{i}USDT", "data": {"best_bid": "1", "best_ask": "2", "lastPrice": "1.5"}} for i in range(5)]
    ok = h._store(batch)
    assert ok is True
    assert h.redis.hlen(h.redis_key) == 6              # 5 symbols + _version
    assert h.redis.hget(h.redis_key, "_version")
    assert h._last_count == 5
    assert json.loads(h.redis.hget(h.redis_key, "S0USDT"))["best_bid"] == "1"


def test_manager_discovers_binance():
    from src.cex_v2.market_data.manager import _discover, _make_handler
    assert ("binance", "spot") in _discover()
    assert ("binance", "futures") in _discover()
    h = _make_handler("binance", "spot")
    assert h.exchange == "binance" and h.redis_key == "spot-market-data:binance"
    hf = _make_handler("binance", "futures")
    assert hf.market_type == "futures" and hf.redis_key == "futures-market-data:binance"


def test_binance_futures_merges_three_endpoints():
    from src.cex_v2.market_data.handlers.binance import BinanceFuturesMarketData
    h = BinanceFuturesMarketData()
    ticker = [{"symbol": "BTCUSDT", "lastPrice": "64000", "quoteVolume": "1000"},
              {"symbol": "ETHUSDC", "lastPrice": "3000", "quoteVolume": "500"},
              {"symbol": "NOPREMUSDT", "lastPrice": "1", "quoteVolume": "1"},   # missing premium -> drop
              {"symbol": "FOOBUSD", "lastPrice": "1", "quoteVolume": "1"}]        # non-USDT/USDC -> drop
    book = [{"symbol": "BTCUSDT", "bidPrice": "63999", "askPrice": "64001"},
            {"symbol": "ETHUSDC", "bidPrice": "2999", "askPrice": "3001"},
            {"symbol": "NOPREMUSDT", "bidPrice": "1", "askPrice": "2"}]
    premium = [{"symbol": "BTCUSDT", "markPrice": "64000.5", "indexPrice": "64000.2",
                "lastFundingRate": "0.0001", "nextFundingTime": 1781460000000},
               {"symbol": "ETHUSDC", "markPrice": "3000.1", "indexPrice": "3000.0",
                "lastFundingRate": "-0.0002", "nextFundingTime": 1781460000000}]
    by_url = {h._ep_ticker: ticker, h._ep_book: book, h._ep_premium: premium}
    h._get = lambda url: by_url[url]   # map by URL: _get_many fetches concurrently, order is not fixed
    by = {o["symbol"]: o["data"] for o in h.fetch_parsed()}
    assert set(by) == {"BTCUSDT", "ETHUSDC"}                  # USDC kept; missing-premium + non-USDT/USDC dropped
    btc = by["BTCUSDT"]
    assert btc["best_bid"] == "63999" and isinstance(btc["best_bid"], str)
    assert btc["markPrice"] == "64000.5" and btc["indexPrice"] == "64000.2"
    assert abs(btc["funding_rate_percent"] - 0.01) < 1e-9    # 0.0001 * 100
    assert btc["next_funding_time"] == 1781460000            # ms -> s


# --- universe hygiene: drop delisted/halted (0.00000000) pairs so the order-book never subscribes to dead symbols ---
def test_spot_drops_zero_priced_dead_symbols():
    h = _h()
    resp = [
        {"symbol": "LIVEUSDT", "bidPrice": "1.0", "askPrice": "1.1", "lastPrice": "1.05", "quoteVolume": "10"},
        {"symbol": "DEADUSDT", "bidPrice": "0.00000000", "askPrice": "0.00000000", "lastPrice": "0", "quoteVolume": "0"},
        {"symbol": "HALFUSDT", "bidPrice": "0", "askPrice": "2.0", "lastPrice": "1", "quoteVolume": "1"},  # one side 0 -> dead
    ]
    assert {o["symbol"] for o in h.parse_api_response(resp)} == {"LIVEUSDT"}


def test_futures_drops_zero_priced_dead_symbols():
    from src.cex_v2.market_data.handlers.binance import BinanceFuturesMarketData
    h = BinanceFuturesMarketData()
    ticker = [{"symbol": "LIVEUSDT", "lastPrice": "1", "quoteVolume": "1"},
              {"symbol": "DEADUSDT", "lastPrice": "1", "quoteVolume": "1"}]
    book = [{"symbol": "LIVEUSDT", "bidPrice": "1.0", "askPrice": "1.1"},
            {"symbol": "DEADUSDT", "bidPrice": "0.00000000", "askPrice": "0.00000000"}]
    premium = [{"symbol": s, "markPrice": "1", "indexPrice": "1", "lastFundingRate": "0",
                "nextFundingTime": 1781460000000} for s in ("LIVEUSDT", "DEADUSDT")]
    by_url = {h._ep_ticker: ticker, h._ep_book: book, h._ep_premium: premium}
    h._get = lambda u: by_url[u]
    assert {o["symbol"] for o in h.fetch_parsed()} == {"LIVEUSDT"}
