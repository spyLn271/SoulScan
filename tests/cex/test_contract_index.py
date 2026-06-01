"""Contract-index rebuild safety (PRC-01) + lookup semantics.

Guards: an all-empty rebuild cycle must NOT blank an existing index; a populated
rebuild swaps atomically and stamps `_version`; lookups return None on miss.
Uses sync fakeredis since the contract checker uses a synchronous redis client.
"""
import pytest
import fakeredis

from src.cex.contract_address_cex_checker.service.redis_client import RedisClient
from src.cex.contract_address_cex_checker.service.config import REDIS_CONFIG
from src.cex.contract_address_cex_checker.service.exchanges.base import CoinEntry


@pytest.fixture
def rc():
    client = RedisClient.__new__(RedisClient)  # skip __init__ (real Redis connect)
    client.client = fakeredis.FakeStrictRedis(decode_responses=True)
    return client


def _entry(coin, addr):
    return CoinEntry(coin=coin, network="evm", contract_address=addr)


def test_populated_rebuild_swaps_and_versions(rc):
    rc.rebuild_contract_index({
        "binance": [_entry("USDT", "0x" + "d" * 40)],
        "okx": [_entry("USDT", "0x" + "D" * 40)],  # same addr, mixed case -> normalized
    })
    key = REDIS_CONFIG.contract_index_key
    # both exchanges merged under one normalized address
    mapping = rc.lookup_contract("0x" + "d" * 40)
    assert mapping == {"binance": "USDT", "okx": "USDT"}
    # version stamped as a hash field; cannot collide with a real 0x/base58 address
    assert rc.client.hget(key, "_version") is not None
    assert rc.lookup_contract("0x" + "a" * 40) is None  # genuine miss -> None


def test_empty_rebuild_does_not_blank_existing_index(rc):
    # seed a good index
    rc.rebuild_contract_index({"binance": [_entry("USDT", "0x" + "d" * 40)]})
    assert rc.lookup_contract("0x" + "d" * 40) is not None

    # a total-failure cycle (no addresses) must KEEP the previous index
    rc.rebuild_contract_index({"binance": [], "okx": []})
    assert rc.lookup_contract("0x" + "d" * 40) == {"binance": "USDT"}, \
        "empty rebuild wrongly blanked the index"

    # and the temp key must not linger
    assert rc.client.exists(f"{REDIS_CONFIG.contract_index_key}:temp") == 0
