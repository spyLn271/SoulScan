"""Python -> Rust order-book schema contract.

Drives the real production write path (`BaseExchangeConnector._process_orderbook_data`)
against an in-memory Redis and asserts the exact fields/types the Rust reader
(`src/engine/rusted_engine/src/cex_api/order_book.rs`) reads by name. If this test
breaks, the Rust consumer breaks — so it guards the contract on every change.
"""
import json
import time
import pytest

from src.cex.producer.core.base_connector import BaseExchangeConnector
from src.cex.producer.config import get_stream_key


class _DummyConnector(BaseExchangeConnector):
    """Minimal concrete connector (not collected by pytest: name doesn't start with Test)."""
    async def get_websocket_url(self, symbol: str = None) -> str:
        return "wss://example.invalid"

    async def parse_message(self, message):
        return None

    async def subscribe_to_symbols(self, websocket, symbols):
        return None


@pytest.fixture
def connector():
    # bybit/spot is enabled in producer config; market_config['enabled'] must be truthy
    return _DummyConnector("bybit", "spot")


async def test_orderbook_schema_contract(connector, fake_redis):
    connector.redis_client = fake_redis

    await connector._process_orderbook_data({
        "symbol": "BTCUSDT",
        "timestamp_ms": int(time.time() * 1000),
        # intentionally unsorted + string-typed to exercise normalization + float coercion
        "bids": [["99.0", "0.1"], ["100.5", "1.2"]],
        "asks": [["102.5", "0.3"], ["101.0", "2.0"]],
    })

    key = get_stream_key("bybit", "spot", "BTCUSDT")
    entries = await fake_redis.xrevrange(key, count=1)
    assert entries, "no stream entry was written"
    _entry_id, fields = entries[0]

    # --- fields the Rust reader reads by name ---
    assert "timestamp_ms" in fields and int(fields["timestamp_ms"]) > 0
    assert fields["symbol"] == "BTCUSDT"
    assert "worker_id" in fields

    bids = json.loads(fields["bids"])
    asks = json.loads(fields["asks"])
    # every level must be [float, float] (Rust deserializes Vec<Vec<f64>>)
    for level in bids + asks:
        assert len(level) == 2
        assert isinstance(level[0], (int, float)) and isinstance(level[1], (int, float))

    # normalization invariants: bids descending, asks ascending by price
    assert bids == sorted(bids, key=lambda x: -x[0]), f"bids not desc: {bids}"
    assert asks == sorted(asks, key=lambda x: x[0]), f"asks not asc: {asks}"
    assert bids[0][0] == 100.5 and asks[0][0] == 101.0


async def test_malformed_levels_are_dropped_not_crashed(connector, fake_redis):
    connector.redis_client = fake_redis
    await connector._process_orderbook_data({
        "symbol": "ETHUSDT",
        "timestamp_ms": int(time.time() * 1000),
        "bids": [["bad", "x"], ["50.0", "1.0"]],   # first level unparseable -> dropped
        "asks": [["51.0", "2.0"]],
    })
    key = get_stream_key("bybit", "spot", "ETHUSDT")
    entries = await fake_redis.xrevrange(key, count=1)
    assert entries
    _id, fields = entries[0]
    bids = json.loads(fields["bids"])
    assert bids == [[50.0, 1.0]], f"malformed level not dropped: {bids}"
