"""Resolver: contract-index rebuild, canonicalization, tradable-base resolution,
last-good retention, and lookup semantics.

The index is keyed `{network}:{address}` -> `{exchange: tradable_base_symbol}`.
Tradability is validated against each exchange's `spot-market-data:{exchange}` hash
(the FIELD names are the tradable symbols, e.g. SOLUSDT). Uses sync fakeredis since
the checker uses a synchronous redis client.
"""
import json
import time

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


def _seed_stream(rc, exchange, base, price, quote="USDT", ts_ms=None):
    """Seed an order-book stream with a top-of-book around `price` (0.1% spread)."""
    if ts_ms is None:
        ts_ms = int(time.time() * 1000)
    spread = price * 0.001
    rc.client.xadd(f"stream:orderbook:{exchange}:spot:{base}{quote}", {
        "timestamp_ms": str(ts_ms),
        "symbol": f"{base}{quote}",
        "bids": json.dumps([[price - spread, 1]]),
        "asks": json.dumps([[price + spread, 1]]),
    })


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


def test_htx_lowercase_market_data_resolves(rc):
    # htx stores market-data symbols lowercase; orderbook streams are uppercase.
    # The resolver must match case-insensitively and store the UPPERCASE base.
    rc.client.hset("spot-market-data:htx", mapping={"acxusdt": "x"})
    rc.rebuild_contract_index({
        "htx": [CoinEntry(coin="ACX", network="ETH", contract_address="0x" + "a" * 40)],
    })
    assert rc.lookup_contract("eth", "0x" + "a" * 40) == {"htx": "ACX"}


def test_blank_network_native_assigned_home_chain(rc):
    # htx reports native assets with blank network + empty address.
    _seed_market(rc, "htx", "ETHUSDT", "BNBUSDT", "SOLUSDT", "BTCUSDT")
    rc.rebuild_contract_index({
        "htx": [
            CoinEntry(coin="ETH", network="", contract_address=""),
            CoinEntry(coin="BNB", network="", contract_address=""),
            CoinEntry(coin="SOL", network="", contract_address=""),
            CoinEntry(coin="BTC", network="", contract_address=""),  # non-SoulScan -> x-btc
        ],
    })
    assert rc.lookup_contract("eth", C.EVM_NATIVE_ADDRESS) == {"htx": "ETH"}
    assert rc.lookup_contract("bsc", C.EVM_NATIVE_ADDRESS) == {"htx": "BNB"}
    assert rc.lookup_contract("solana", C.WSOL_MINT) == {"htx": "SOL"}
    # BTC kept under x-btc:native (not dropped, not on a SoulScan chain)
    assert rc.client.hget(REDIS_CONFIG.contract_index_key, "x-btc:native") is not None


def test_last_good_load_roundtrip(rc):
    entries = [CoinEntry(coin="BTC", network="ETH", contract_address="0x" + "b" * 40)]
    rc.store_exchange_data("bybit", entries)
    loaded = rc.load_exchange_data("bybit")
    assert loaded == entries
    assert rc.load_exchange_data("neverseen") is None


# --------------------------------------------------------------------------- #
# Cross-exchange back-fill (LBank et al. that expose no contract address).
# Phase 2 attaches a back-fill exchange to the SINGLE address other exchanges
# resolved for (chain, wallet-coin), only when >= min_witnesses agree.
# --------------------------------------------------------------------------- #
PEPE = "0x6982508145454ce325ddbe47a25d4ec3d2311933"


def test_backfill_attaches_with_two_witnesses(rc):
    _seed_market(rc, "binance", "PEPEUSDT")
    _seed_market(rc, "okx", "PEPEUSDT")
    _seed_market(rc, "lbank", "PEPEUSDT")
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="PEPE", network="ETH", contract_address=PEPE)],
        "okx": [CoinEntry(coin="PEPE", network="ERC20", contract_address=PEPE)],
        "lbank": [CoinEntry(coin="PEPE", network="erc20", contract_address="")],
    }, backfill_exchanges={"lbank"}, min_witnesses=2)
    assert rc.lookup_contract("eth", PEPE) == {
        "binance": "PEPE", "okx": "PEPE", "lbank": "PEPE",
    }


def test_backfill_single_witness_respects_threshold(rc):
    addr = "0x" + "a" * 40
    _seed_market(rc, "binance", "AAAUSDT")
    _seed_market(rc, "lbank", "AAAUSDT")
    data = {
        "binance": [CoinEntry(coin="AAA", network="ETH", contract_address=addr)],
        "lbank": [CoinEntry(coin="AAA", network="erc20", contract_address="")],
    }
    # one witness, threshold 2 -> lbank NOT attached
    rc.rebuild_contract_index(data, backfill_exchanges={"lbank"}, min_witnesses=2)
    assert rc.lookup_contract("eth", addr) == {"binance": "AAA"}
    # same data, threshold 1 -> lbank attached
    rc.rebuild_contract_index(data, backfill_exchanges={"lbank"}, min_witnesses=1)
    assert rc.lookup_contract("eth", addr) == {"binance": "AAA", "lbank": "AAA"}


def test_backfill_unmatched_creates_no_key(rc):
    btc = "0x" + "b" * 40
    _seed_market(rc, "binance", "BTCUSDT")
    _seed_market(rc, "lbank", "FOOUSDT")
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="BTC", network="ETH", contract_address=btc)],
        "lbank": [CoinEntry(coin="FOO", network="erc20", contract_address="")],
    }, backfill_exchanges={"lbank"}, min_witnesses=1)
    # FOO has no address from any other exchange -> no phantom key, lbank absent
    assert rc.lookup_contract("eth", "0x" + "f" * 40) is None
    assert "lbank" not in rc.lookup_contract("eth", btc)


def test_backfill_ambiguous_multiple_addresses_skipped(rc):
    a1, a2 = "0x" + "1" * 40, "0x" + "2" * 40
    _seed_market(rc, "binance", "BARUSDT")
    _seed_market(rc, "okx", "BARUSDT")
    _seed_market(rc, "lbank", "BARUSDT")
    # same (chain, coin) resolves to two different addresses -> ambiguous
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="BAR", network="ETH", contract_address=a1)],
        "okx": [CoinEntry(coin="BAR", network="ETH", contract_address=a2)],
        "lbank": [CoinEntry(coin="BAR", network="erc20", contract_address="")],
    }, backfill_exchanges={"lbank"}, min_witnesses=1)
    assert "lbank" not in rc.lookup_contract("eth", a1)
    assert "lbank" not in rc.lookup_contract("eth", a2)


def test_backfill_same_address_multi_exchange_not_ambiguous(rc):
    # TRUMP at ONE mint on two exchanges -> set semantics: a single key, 2 witnesses.
    _seed_market(rc, "binance", "TRUMPUSDT")
    _seed_market(rc, "gateio", "TRUMPUSDT")
    _seed_market(rc, "lbank", "TRUMPUSDT")
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="TRUMP", network="SOL", contract_address=TRUMP_MINT)],
        "gateio": [CoinEntry(coin="TRUMP", network="SOL", contract_address=TRUMP_MINT)],
        "lbank": [CoinEntry(coin="TRUMP", network="solana", contract_address="")],
    }, backfill_exchanges={"lbank"}, min_witnesses=2)
    assert rc.lookup_contract("solana", TRUMP_MINT) == {
        "binance": "TRUMP", "gateio": "TRUMP", "lbank": "TRUMP",
    }


def test_backfill_skips_when_not_tradable_on_lbank(rc):
    addr = "0x" + "c" * 40
    _seed_market(rc, "binance", "BAZUSDT")
    _seed_market(rc, "okx", "BAZUSDT")
    _seed_market(rc, "lbank", "OTHERUSDT")  # lbank has market data but not BAZ
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="BAZ", network="ETH", contract_address=addr)],
        "okx": [CoinEntry(coin="BAZ", network="ETH", contract_address=addr)],
        "lbank": [CoinEntry(coin="BAZ", network="erc20", contract_address="")],
    }, backfill_exchanges={"lbank"}, min_witnesses=2)
    assert "lbank" not in rc.lookup_contract("eth", addr)


def test_backfill_native_tokens_attach(rc):
    # Natives back-fill onto the canonical native keys; also exercises the
    # bep20(bsc) chain alias on a native.
    _seed_market(rc, "binance", "ETHUSDT", "BNBUSDT", "SOLUSDT")
    _seed_market(rc, "okx", "ETHUSDT", "BNBUSDT", "SOLUSDT")
    _seed_market(rc, "lbank", "ETHUSDT", "BNBUSDT", "SOLUSDT")
    rc.rebuild_contract_index({
        "binance": [
            CoinEntry(coin="ETH", network="ETH", contract_address=""),
            CoinEntry(coin="BNB", network="BSC", contract_address=""),
            CoinEntry(coin="SOL", network="SOL", contract_address=""),
        ],
        "okx": [
            CoinEntry(coin="ETH", network="ETH", contract_address=""),
            CoinEntry(coin="BNB", network="BSC", contract_address=""),
            CoinEntry(coin="SOL", network="SOL", contract_address=""),
        ],
        "lbank": [
            CoinEntry(coin="ETH", network="erc20", contract_address=""),
            CoinEntry(coin="BNB", network="bep20(bsc)", contract_address=""),
            CoinEntry(coin="SOL", network="solana", contract_address=""),
        ],
    }, backfill_exchanges={"lbank"}, min_witnesses=2)
    assert rc.lookup_contract("eth", C.EVM_NATIVE_ADDRESS).get("lbank") == "ETH"
    assert rc.lookup_contract("bsc", C.EVM_NATIVE_ADDRESS).get("lbank") == "BNB"
    assert rc.lookup_contract("solana", C.WSOL_MINT).get("lbank") == "SOL"


def test_backfill_native_symbol_indexing_matches_wrapped_wallet_coin(rc):
    # Producers file native SOL as wallet-coin "SOL"; lbank names it "WSOL".
    # native-symbol indexing registers the native key under WSOL too, so it matches.
    _seed_market(rc, "binance", "SOLUSDT")
    _seed_market(rc, "okx", "SOLUSDT")
    _seed_market(rc, "lbank", "WSOLUSDT")  # lbank trades it as WSOL
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="SOL", network="SOL", contract_address="")],
        "okx": [CoinEntry(coin="SOL", network="SOL", contract_address="")],
        "lbank": [CoinEntry(coin="WSOL", network="solana", contract_address="")],
    }, backfill_exchanges={"lbank"}, min_witnesses=2)
    assert rc.lookup_contract("solana", C.WSOL_MINT).get("lbank") == "WSOL"


def test_backfill_base_mainnet_alias_attaches(rc):
    addr = "0x" + "d" * 40
    _seed_market(rc, "binance", "TKNUSDT")
    _seed_market(rc, "okx", "TKNUSDT")
    _seed_market(rc, "lbank", "TKNUSDT")
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="TKN", network="BASE", contract_address=addr)],
        "okx": [CoinEntry(coin="TKN", network="base", contract_address=addr)],
        "lbank": [CoinEntry(coin="TKN", network="base mainnet", contract_address="")],
    }, backfill_exchanges={"lbank"}, min_witnesses=2)
    assert rc.lookup_contract("base", addr).get("lbank") == "TKN"


def test_backfill_testnet_chain_not_collapsed_to_mainnet(rc):
    addr = "0x" + "e" * 40
    _seed_market(rc, "binance", "TSTUSDT")
    _seed_market(rc, "okx", "TSTUSDT")
    _seed_market(rc, "lbank", "TSTUSDT")
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="TST", network="BASE", contract_address=addr)],
        "okx": [CoinEntry(coin="TST", network="base", contract_address=addr)],
        # "base goerli" must NOT canonicalize to base -> no attach
        "lbank": [CoinEntry(coin="TST", network="base goerli", contract_address="")],
    }, backfill_exchanges={"lbank"}, min_witnesses=2)
    assert "lbank" not in rc.lookup_contract("base", addr)


def test_backfill_cross_chain_isolation(rc):
    addr = "0x" + "9" * 40
    _seed_market(rc, "binance", "XYZUSDT")
    _seed_market(rc, "okx", "XYZUSDT")
    _seed_market(rc, "lbank", "XYZUSDT")
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="XYZ", network="ETH", contract_address=addr)],
        "okx": [CoinEntry(coin="XYZ", network="ETH", contract_address=addr)],
        # lbank lists XYZ on a different chain -> must not attach to the eth key
        "lbank": [CoinEntry(coin="XYZ", network="trc20", contract_address="")],
    }, backfill_exchanges={"lbank"}, min_witnesses=2)
    assert "lbank" not in rc.lookup_contract("eth", addr)


def test_backfill_lbank_only_coin_creates_no_key(rc):
    # The load-bearing Phase-1 exclusion: an address-less lbank EVM entry must NOT
    # create a key (and especially must not poison the native 0x0 key).
    btc = "0x" + "b" * 40
    _seed_market(rc, "binance", "BTCUSDT")
    _seed_market(rc, "lbank", "SOLOUSDT")
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="BTC", network="ETH", contract_address=btc)],
        "lbank": [CoinEntry(coin="SOLO", network="erc20", contract_address="")],
    }, backfill_exchanges={"lbank"}, min_witnesses=1)
    assert rc.lookup_contract("eth", C.EVM_NATIVE_ADDRESS) is None  # not poisoned
    allvals = rc.client.hgetall(REDIS_CONFIG.contract_index_key)
    assert not any("lbank" in v for k, v in allvals.items() if k != "_version")


def test_backfill_cannot_rescue_empty_phase1(rc):
    _seed_market(rc, "binance", "USDTUSDT")
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="USDT", network="ETH", contract_address=USDT_ETH)],
    })
    assert rc.lookup_contract("eth", USDT_ETH_LC) is not None
    _seed_market(rc, "lbank", "PEPEUSDT")
    # every address-bearing exchange empty -> Phase 1 empty -> back-fill can't rescue
    rc.rebuild_contract_index({
        "binance": [],
        "lbank": [CoinEntry(coin="PEPE", network="erc20", contract_address="")],
    }, backfill_exchanges={"lbank"}, min_witnesses=1)
    assert rc.lookup_contract("eth", USDT_ETH_LC) == {"binance": "USDT"}  # retained
    assert rc.client.exists(f"{REDIS_CONFIG.contract_index_key}:temp") == 0


def test_backfill_refuses_without_lbank_market_data(rc):
    # No spot-market-data:lbank -> refuse to guess bases (no attachment).
    addr = "0x" + "7" * 40
    _seed_market(rc, "binance", "QQQUSDT")
    _seed_market(rc, "okx", "QQQUSDT")
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="QQQ", network="ETH", contract_address=addr)],
        "okx": [CoinEntry(coin="QQQ", network="ETH", contract_address=addr)],
        "lbank": [CoinEntry(coin="QQQ", network="erc20", contract_address="")],
    }, backfill_exchanges={"lbank"}, min_witnesses=1)
    assert "lbank" not in rc.lookup_contract("eth", addr)


# --------------------------------------------------------------------------- #
# Phase 2.5: price-fingerprint matching. A producer exchange's tradable symbol that
# its wallet API didn't cover is resolved to the right address by comparing its
# order-book mid-price to peers (same token => within 15%; collisions differ wildly).
# --------------------------------------------------------------------------- #
def test_canonical_address_empty_evm_only_native():
    # Empty EVM address resolves to the native sentinel ONLY for the chain's native coin
    # (or wrapped alias); any other address-less token is dropped, not collapsed onto 0x0.
    assert C.canonical_address("eth", "", "ETH") == C.EVM_NATIVE_ADDRESS
    assert C.canonical_address("eth", "", "WETH") == C.EVM_NATIVE_ADDRESS
    assert C.canonical_address("eth", "", "MANTA") is None
    assert C.canonical_address("bsc", "", "BNB") == C.EVM_NATIVE_ADDRESS
    assert C.canonical_address("bsc", "", "SENSO") is None
    assert C.canonical_address("arbitrum", "", "ETH") == C.EVM_NATIVE_ADDRESS


def test_rebuild_native_key_not_polluted(rc):
    _seed_market(rc, "binance", "ETHUSDT")
    _seed_market(rc, "bitmart", "ETHUSDT", "MANTAUSDT")
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="ETH", network="ETH", contract_address="")],       # native
        "bitmart": [
            CoinEntry(coin="ETH", network="ETH", contract_address=""),                # native
            CoinEntry(coin="MANTA", network="MANTA-ETH", contract_address=""),        # address-less token
        ],
    }, price_match=False)
    # native key has only ETH; the address-less MANTA is dropped (not on 0x0, nowhere)
    assert rc.lookup_contract("eth", C.EVM_NATIVE_ADDRESS) == {"binance": "ETH", "bitmart": "ETH"}


def test_canonical_network_verbose_and_prefix_forms():
    # mexc verbose Name(TOKEN)
    assert C.canonical_network("Ethereum(ERC20)") == "eth"
    assert C.canonical_network("BNB Smart Chain(BEP20)") == "bsc"
    assert C.canonical_network("Solana(SOL)") == "solana"
    assert C.canonical_network("Arbitrum One(ARB)") == "arbitrum"
    # bitmart / bybit oddities
    assert C.canonical_network("BSC_BNB") == "bsc"
    assert C.canonical_network("BASE-ETH") == "base"
    assert C.canonical_network("ARBI") == "arbitrum"


def test_canonical_network_non_soulscan_stays_x():
    for n in ["ArbitrumNova", "ARBITRUM_NOVA", "ARBINOVA", "Polygon(MATIC)",
              "Optimism", "Tron(TRC20)", "MATIC", "TON", "SUI", "BTC"]:
        assert C.canonical_network(n).startswith("x-"), n


def test_resolve_entry_strips_coin_prefix():
    # OKX '{COIN}-{CHAIN}' and coinex '{COIN}_{CHAIN}' -> the chain suffix canonicalizes.
    evm = "0x" + "a" * 40
    mint = "So11111111111111111111111111111111111111112"
    assert C.resolve_entry("AXS-ERC20", evm, "AXS")[0] == "eth"
    assert C.resolve_entry("AVNT-Base", evm, "AVNT")[0] == "base"
    assert C.resolve_entry("AAVE_BSC", evm, "AAVE")[0] == "bsc"
    assert C.resolve_entry("ANIME-Arbitrum One", evm, "ANIME")[0] == "arbitrum"
    assert C.resolve_entry("ASP-Solana", mint, "ASP") == ("solana", mint)
    # a non-coin-prefixed non-SoulScan chain stays x-* (not mis-stripped)
    assert C.resolve_entry("ArbitrumNova", evm, "FOO")[0].startswith("x-")


def test_price_match_resolves_and_disambiguates(rc):
    pepe = "0x6982508145454ce325ddbe47a25d4ec3d2311933"
    fake = "0x" + "f" * 40  # a same-ticker "PEPE" collision on another chain, 50x price
    _seed_market(rc, "binance", "PEPEUSDT")
    _seed_market(rc, "gateio", "PEPEUSDT")
    _seed_stream(rc, "binance", "PEPE", 2.97e-06)   # reference for the real PEPE (eth)
    _seed_stream(rc, "gateio", "PEPE", 1.5e-04)     # reference for the collision (50x)
    _seed_stream(rc, "okx", "PEPE", 2.98e-06)       # okx trades PEPE, no okx wallet entry
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="PEPE", network="ETH", contract_address=pepe)],
        "gateio": [CoinEntry(coin="PEPE", network="BSC", contract_address=fake)],
    }, price_match=True)
    assert rc.lookup_contract("eth", pepe).get("okx") == "PEPE"   # price-matched to real PEPE
    assert "okx" not in rc.lookup_contract("bsc", fake)           # NOT the 50x collision


def test_price_match_multichain_adds_all(rc):
    link_eth = "0x514910771af9ca656af840dff83e8264ecf986ca"
    link_bsc = "0xf8a0bf9cf54bb92f17374d9e9a321e6a111a51bd"
    _seed_market(rc, "binance", "LINKUSDT")
    _seed_market(rc, "gateio", "LINKUSDT")
    _seed_stream(rc, "binance", "LINK", 14.0)
    _seed_stream(rc, "gateio", "LINK", 14.0)
    _seed_stream(rc, "okx", "LINK", 14.05)   # same asset on both chains, same price
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="LINK", network="ETH", contract_address=link_eth)],
        "gateio": [CoinEntry(coin="LINK", network="BSC", contract_address=link_bsc)],
    }, price_match=True)
    assert rc.lookup_contract("eth", link_eth).get("okx") == "LINK"
    assert rc.lookup_contract("bsc", link_bsc).get("okx") == "LINK"


def test_price_match_fill_gaps_only(rc):
    a, b = "0x" + "a" * 40, "0x" + "b" * 40
    _seed_market(rc, "okx", "FOOUSDT")
    _seed_market(rc, "binance", "FOOUSDT")
    _seed_stream(rc, "okx", "FOO", 5.0)
    _seed_stream(rc, "binance", "FOO", 5.0)
    rc.rebuild_contract_index({
        "okx": [CoinEntry(coin="FOO", network="ETH", contract_address=a)],      # okx resolved via API
        "binance": [CoinEntry(coin="FOO", network="BSC", contract_address=b)],  # same ticker, same price
    }, price_match=True)
    assert rc.lookup_contract("eth", a).get("okx") == "FOO"
    assert "okx" not in rc.lookup_contract("bsc", b)  # already resolved -> price-match leaves it


def test_price_match_skips_stale_stream(rc):
    addr = "0x" + "c" * 40
    _seed_market(rc, "binance", "BARUSDT")
    _seed_stream(rc, "binance", "BAR", 3.0)
    _seed_stream(rc, "okx", "BAR", 3.0, ts_ms=int(time.time() * 1000) - 1_000_000)  # ~1000s old
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="BAR", network="ETH", contract_address=addr)],
    }, price_match=True, price_match_stream_max_age=300)
    assert "okx" not in (rc.lookup_contract("eth", addr) or {})  # stale okx price -> no match


def test_canonical_address_rejects_malformed():
    # Truncated / malformed addresses (e.g. OKX's 6-char masked ctAddr) are dropped, so they
    # never create a junk key the engine can't query. Valid addresses are kept (case-normalized).
    assert C.canonical_address("solana", TRUMP_MINT[-6:], "TRUMP") is None   # truncated mint stub
    assert C.canonical_address("solana", TRUMP_MINT, "TRUMP") == TRUMP_MINT  # full mint kept
    assert C.canonical_address("eth", "831ec7", "USDT") is None             # truncated EVM stub
    assert C.canonical_address("eth", "0x" + "a" * 40, "X") == "0x" + "a" * 40
    assert C.canonical_address("eth", "0X" + "A" * 40, "X") == "0x" + "a" * 40  # case-normalized
    assert C.canonical_address("bsc", "0x123", "X") is None                 # too-short EVM
    # non-engine x-* networks keep their address verbatim (not validated)
    assert C.canonical_address("x-tron", "TXYZ123", "USDT") == "TXYZ123"


def test_okx_truncated_address_recovered_by_price_match(rc):
    # OKX masks deposit-address ctAddr to the last 6 chars (TRUMP's mint -> "jfGiPN").
    # That stub must NOT become a key; OKX is instead recovered under the REAL mint by
    # price-matching its live order-book stream (the exact production TRUMP case).
    stub = TRUMP_MINT[-6:]
    _seed_market(rc, "binance", "TRUMPUSDT")
    _seed_market(rc, "okx", "TRUMPUSDT")
    _seed_stream(rc, "binance", "TRUMP", 1.87)
    _seed_stream(rc, "okx", "TRUMP", 1.87)
    rc.rebuild_contract_index({
        "binance": [CoinEntry(coin="TRUMP", network="SOL", contract_address=TRUMP_MINT)],
        "okx": [CoinEntry(coin="TRUMP", network="TRUMP-Solana", contract_address=stub)],
    }, price_match=True)
    assert rc.lookup_contract("solana", stub) in (None, {})              # no junk stub key
    real = rc.lookup_contract("solana", TRUMP_MINT)
    assert real.get("okx") == "TRUMP"                                    # recovered via price-match
    assert real.get("binance") == "TRUMP"
