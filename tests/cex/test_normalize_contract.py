"""Regression guard: base-class hooks that the base calls SYNCHRONOUSLY must not
be overridden as `async` in any plugin.

gateio originally declared `_normalize_symbol_for_redis` as `async`, but the base
class calls it synchronously (in start(), _write_gap_markers, cleanup,
stop_monitoring_removed_symbols). The async override returned an un-awaited
coroutine that was then handed to Redis, aborting gateio startup -> 0 messages.
This test fails if any plugin reintroduces an async override of a sync-contract hook.
"""
import glob
import os
import re
import inspect
import importlib

import pytest

# hooks the base class invokes WITHOUT await -> overrides must be sync
SYNC_CONTRACT_HOOKS = ["_normalize_symbol_for_redis"]

PLUGINS = [
    ("bybit", "BybitSpotConnector"), ("okx", "OkxSpotConnector"),
    ("mexc", "MexcSpotConnector"), ("gateio", "GateioSpotConnector"),
    ("bingx", "BingxSpotConnector"), ("bitget", "BitgetSpotConnector"),
    ("bitmart", "BitmartSpotConnector"), ("coinex", "CoinexSpotConnector"),
    ("htx", "HtxSpotConnector"), ("lbank", "LbankSpotConnector"),
]


@pytest.mark.parametrize("mod,cls", PLUGINS)
def test_sync_contract_hooks_are_not_async(mod, cls):
    m = importlib.import_module(f"src.cex.producer.plugins.{mod}_plugin")
    C = getattr(m, cls)
    for hook in SYNC_CONTRACT_HOOKS:
        fn = getattr(C, hook, None)
        if fn is None:
            continue  # not overridden -> fine
        assert not inspect.iscoroutinefunction(fn), (
            f"{mod}.{hook} is async but the base class calls it synchronously; "
            f"make it a plain `def` (see gateio fix)."
        )


def test_base_call_sites_remain_sync():
    """Documents the invariant: if someone makes a base call site `await`, this
    test should be updated together with the hook contract. Currently all call
    sites are sync."""
    bc = open(os.path.join(os.path.dirname(__file__), "..", "..",
                           "src", "cex", "producer", "core", "base_connector.py")).read()
    awaited = re.findall(r"await\s+self\._normalize_symbol_for_redis\(", bc)
    assert not awaited, f"base now awaits _normalize_symbol_for_redis ({len(awaited)}x); update the contract test"


def test_gateio_normalizes_underscore_format():
    m = importlib.import_module("src.cex.producer.plugins.gateio_plugin")
    conn = m.GateioSpotConnector()
    assert conn._normalize_symbol_for_redis("BTC_USDT") == "BTCUSDT"
    assert conn._normalize_symbol_for_redis("ETH_USDC") == "ETHUSDC"
