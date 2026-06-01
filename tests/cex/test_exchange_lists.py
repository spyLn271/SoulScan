"""Exchange-list drift guard (single source of truth).

The order-book contract requires the Python producer's enabled exchanges and the
Rust consumer's SUPPORTED_CEX_LIST to agree — otherwise Python writes streams the
Rust engine never reads, or Rust queries streams that don't exist. This test
fails if they drift. The contract-address checker intentionally differs (it adds
`binance` for address resolution and omits the order-book-only exchanges); that
delta is asserted explicitly so an *unintended* change is still caught.
"""
import os
import re
import pytest

from src.cex.producer.config import get_enabled_exchanges

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUST_CONFIG = os.path.join(ROOT, "src", "engine", "rusted_engine", "src", "config.rs")


def _rust_cex_list():
    if not os.path.exists(RUST_CONFIG):
        return None
    txt = open(RUST_CONFIG).read()
    m = re.search(r"SUPPORTED_CEX_LIST[^=]*=\s*\[(.*?)\]", txt, re.S)
    if not m:
        return None
    return set(re.findall(r'"(\w+)"', m.group(1)))


def _contract_checker_exchanges():
    cfg = open(os.path.join(ROOT, "src", "cex", "contract_address_cex_checker",
                            "service", "config.py")).read()
    return set(re.findall(r'"(\w+)": ExchangeConfig', cfg))


def test_producer_matches_rust_orderbook_list():
    producer = set(get_enabled_exchanges())
    rust = _rust_cex_list()
    if rust is None:
        pytest.skip("Rust config.rs not found / SUPPORTED_CEX_LIST not parseable")
    assert producer == rust, (
        f"order-book exchange drift: producer-only={producer - rust}, "
        f"rust-only={rust - producer}. Keep producer EXCHANGES and Rust "
        f"SUPPORTED_CEX_LIST in sync (see RUST_CONTRACT_CHANGESPEC.md)."
    )


def test_contract_checker_delta_is_intentional():
    producer = set(get_enabled_exchanges())
    checker = _contract_checker_exchanges()
    # binance is address-resolution-only (not an order-book producer)
    assert "binance" in checker, "contract checker unexpectedly dropped binance"
    assert "binance" not in producer, "binance should not be an order-book producer"
    # exchanges the checker does NOT cover (documented gap): it can't resolve
    # addresses for these even though they produce order books.
    uncovered = producer - checker
    assert uncovered == {"bitmart", "lbank"}, (
        f"contract-checker coverage changed unexpectedly: now missing {uncovered} "
        f"(was {{'bitmart','lbank'}}). Update this assertion intentionally."
    )
