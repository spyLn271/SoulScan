"""Resolver: contract-index rebuild, canonicalization, tradable-base resolution,
last-good retention, and lookup semantics.

The index is keyed `{network}:{address}` -> `{exchange: tradable_base_symbol}`.
Tradability is validated against each exchange's `spot-market-data:{exchange}` hash
(the FIELD names are the tradable symbols, e.g. SOLUSDT). Uses sync fakeredis since
the checker uses a synchronous redis client.
"""
import pytest
import fakeredis

from src.cex.contract_address_cex_checker.service.redis_client import RedisClient
from src.cex.contract_address_cex_checker.service.config import REDIS_CONFIG
from src.cex.contract_address_cex_checker.service.exchanges.base import CoinEntry
from src.cex.contract_address_cex_checker.service import canonical as C

USDT_ETH = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
USDT_ETH_LC = USDT_ETH.lower()
TRUMP_MINT = "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN"


@pytest.fixture
def rc():
    client = RedisClient.__new__(RedisClient)  # skip __init__ (real Redis connect)
    client.client = fakeredis.FakeStrictRedis(decode_responses=True)
    return client


def _seed_market(rc, exchange, *symbols):
    rc.client.hset(f"spot-market-data:{exchange}", mapping={s: "x" for s in symbols})


def test_value_is_tradable_base_not_wallet_coin(rc):
    # Binance lists the Solana asset as wallet-coin WSOL, but trades it as SOLUSDT.
    _seed_market(rc, "binance", "SOLUSDT", "BTCUSDT")
    rc.rebuild_contract_index({
        "binance": [
            CoinEntry(coin="WSOL", network="SOL", contract_address=C.WSOL_MINT),
            CoinEntry(coin="SOL", network="SOL", contract_address=""),  # native
        ],
    })
    # keyed under solana:<WSOL mint>, value is the TRADABLE base "SOL" (not "WSOL")
    assert rc.lookup_contract("solana", C.WSOL_MINT) == {"binance": "SOL"}


def test_trump_same_address_per_exchange_symbols(rc):
    # Same mint, different per-exchange trading symbol -> all retained.
    _seed_market(rc, "binance", "TRUMPUSDT")
    _seed_market(rc, "gateio", "TRUMPUSDT")
    _seed_market(rc, "weirdex", "SOLTRUMPUSDT")
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="TRUMP", network="SOL", contract_address=TRUMP_MINT)],
        "gateio": [CoinEntry(coin="TRUMP", network="SOL", contract_address=TRUMP_MINT)],
        "weirdex": [CoinEntry(coin="SOLTRUMP", network="SOL", contract_address=TRUMP_MINT)],
    })
    assert rc.lookup_contract("solana", TRUMP_MINT) == {
        "binance": "TRUMP", "gateio": "TRUMP", "weirdex": "SOLTRUMP",
    }


def test_native_evm_chain_scoped_no_collision(rc):
    # ETH-on-eth and BNB-on-bsc are both native (empty address) -> must NOT collide.
    _seed_market(rc, "binance", "ETHUSDT", "BNBUSDT")
    rc.rebuild_contract_index({
        "binance": [
            CoinEntry(coin="ETH", network="ETH", contract_address=""),
            CoinEntry(coin="BNB", network="BSC", contract_address=""),
        ],
    })
    assert rc.lookup_contract("eth", C.EVM_NATIVE_ADDRESS) == {"binance": "ETH"}
    assert rc.lookup_contract("bsc", C.EVM_NATIVE_ADDRESS) == {"binance": "BNB"}


def test_wrapped_collapses_to_native(rc):
    # WETH wrapped address resolves to eth native key.
    _seed_market(rc, "binance", "ETHUSDT")
    weth = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="ETH", network="ETH", contract_address=weth)],
    })
    assert rc.lookup_contract("eth", C.EVM_NATIVE_ADDRESS) == {"binance": "ETH"}


def test_erc20_lowercased_and_merged(rc):
    _seed_market(rc, "binance", "USDTUSDT", "USDTUSDC")
    _seed_market(rc, "okx", "USDTUSDC")
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="USDT", network="ETH", contract_address=USDT_ETH)],
        "okx": [CoinEntry(coin="USDT", network="ERC20", contract_address=USDT_ETH.upper())],
    })
    # mixed-case + different network alias (ETH vs ERC20) -> one eth:lowercased key
    assert rc.lookup_contract("eth", USDT_ETH_LC) == {"binance": "USDT", "okx": "USDT"}


def test_non_tradable_dropped(rc):
    # coin has an address but no market on the exchange -> not indexed for it.
    _seed_market(rc, "binance", "BTCUSDT")  # no FOOUSDT/FOOUSDC
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="FOO", network="ETH", contract_address="0x" + "f" * 40)],
    })
    assert rc.lookup_contract("eth", "0x" + "f" * 40) is None


def test_unsupported_network_kept_with_x_prefix(rc):
    _seed_market(rc, "binance", "TRXUSDT")
    trx_addr = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # tron, non-EVM
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="TRX", network="TRC20", contract_address=trx_addr)],
    })
    # kept under an x-<slug> network key, not dropped
    assert rc.lookup_contract("TRC20", trx_addr) == {"binance": "TRX"}


def test_missing_market_data_falls_back_to_raw_coin(rc):
    # If an exchange has NO market-data hash, don't lose it — use raw coin as base.
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="USDT", network="ETH", contract_address=USDT_ETH)],
    })
    assert rc.lookup_contract("eth", USDT_ETH_LC) == {"binance": "USDT"}


def test_version_stamped_and_miss_returns_none(rc):
    _seed_market(rc, "binance", "USDTUSDT")
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="USDT", network="ETH", contract_address=USDT_ETH)],
    })
    assert rc.client.hget(REDIS_CONFIG.contract_index_key, "_version") is not None
    assert rc.lookup_contract("eth", "0x" + "a" * 40) is None


def test_empty_rebuild_does_not_blank_index(rc):
    _seed_market(rc, "binance", "USDTUSDT")
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="USDT", network="ETH", contract_address=USDT_ETH)],
    })
    assert rc.lookup_contract("eth", USDT_ETH_LC) is not None
    # total-failure cycle (no usable entries) must keep the previous index
    rc.rebuild_contract_index({"binance": [], "okx": []})
    assert rc.lookup_contract("eth", USDT_ETH_LC) == {"binance": "USDT"}
    assert rc.client.exists(f"{REDIS_CONFIG.contract_index_key}:temp") == 0


def test_last_good_load_roundtrip(rc):
    entries = [CoinEntry(coin="BTC", network="ETH", contract_address="0x" + "b" * 40)]
    rc.store_exchange_data("bybit", entries)
    loaded = rc.load_exchange_data("bybit")
    assert loaded == entries
    assert rc.load_exchange_data("neverseen") is None
