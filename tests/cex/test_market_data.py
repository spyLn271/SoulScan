"""market_data BaseMarketDataHandler: atomic hash rebuild + store semantics.

Tests target the REAL handler API (parse_api_response / _store_data_in_redis),
using fakeredis. The key guarantee is that _store_data_in_redis rebuilds the hash
atomically (MULTI/EXEC) and stamps a _version, so a reader never sees a partial
hash.
"""
import json
import fakeredis

from src.cex.market_data.core.base_handler import BaseMarketDataHandler


class _Handler(BaseMarketDataHandler):
    def __init__(self):
        super().__init__("testex", "spot")
        self.redis_key = "spot-market-data:testex"
        self.redis_client = fakeredis.FakeStrictRedis(decode_responses=True)

    def parse_api_response(self, response_data):
        # response_data is already in the [{symbol, data}] shape for tests
        return response_data


def test_store_writes_hash_with_version():
    h = _Handler()
    n = h._store_data_in_redis([
        {"symbol": "BTCUSDT", "data": {"lastPrice": "50000"}},
        {"symbol": "ETHUSDT", "data": {"lastPrice": "3000"}},
    ])
    assert n == 2
    assert json.loads(h.redis_client.hget(h.redis_key, "BTCUSDT")) == {"lastPrice": "50000"}
    assert h.redis_client.hget(h.redis_key, "_version") is not None


def test_store_uses_transaction_pipeline(monkeypatch):
    """The rebuild must use a MULTI/EXEC (transaction=True) pipeline."""
    h = _Handler()
    seen = {}
    real_pipeline = h.redis_client.pipeline

    def spy_pipeline(*a, **kw):
        seen["transaction"] = kw.get("transaction", a[0] if a else None)
        return real_pipeline(*a, **kw)

    monkeypatch.setattr(h.redis_client, "pipeline", spy_pipeline)
    h._store_data_in_redis([{"symbol": "BTCUSDT", "data": {"p": 1}}])
    assert seen.get("transaction") is True


def test_store_empty_returns_zero():
    h = _Handler()
    assert h._store_data_in_redis([]) == 0


def test_store_skips_rows_missing_symbol_or_data():
    h = _Handler()
    n = h._store_data_in_redis([
        {"symbol": "BTCUSDT", "data": {"p": 1}},
        {"symbol": None, "data": {"p": 2}},      # skipped
        {"symbol": "ETHUSDT", "data": None},     # skipped
    ])
    assert n == 1
    assert h.redis_client.hget(h.redis_key, "BTCUSDT") is not None
    assert h.redis_client.hget(h.redis_key, "ETHUSDT") is None


def test_rebuild_replaces_previous_contents():
    h = _Handler()
    h._store_data_in_redis([{"symbol": "OLD", "data": {"p": 1}}])
    h._store_data_in_redis([{"symbol": "NEW", "data": {"p": 2}}])
    # delete-then-repopulate means stale symbols are gone
    assert h.redis_client.hget(h.redis_key, "OLD") is None
    assert h.redis_client.hget(h.redis_key, "NEW") is not None
