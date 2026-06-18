"""Bybit is discovered by the supervisor + market-data manager via the name convention (no registry edits)."""
from src.cex_v2.supervisor import _discover as discover_ob
from src.cex_v2.market_data.manager import _discover as discover_md, _make_handler


def test_supervisor_discovers_bybit():
    by = {t.name: t for t in discover_ob(("spot", "futures"), exchanges=["bybit"])}
    assert set(by) == {"bybit_spot", "bybit_futures"}
    assert by["bybit_spot"].class_name == "BybitSpotConnector"
    assert by["bybit_futures"].class_name == "BybitFuturesConnector"
    assert by["bybit_spot"].module_path == "src.cex_v2.plugins.bybit"


def test_marketdata_discovers_bybit():
    pairs = discover_md(("spot", "futures"), exchanges=["bybit"])
    assert ("bybit", "spot") in pairs and ("bybit", "futures") in pairs
    hs = _make_handler("bybit", "spot")
    assert type(hs).__name__ == "BybitSpotMarketData" and hs.redis_key == "spot-market-data:bybit"
    hf = _make_handler("bybit", "futures")
    assert type(hf).__name__ == "BybitFuturesMarketData" and hf.market_type == "futures"
