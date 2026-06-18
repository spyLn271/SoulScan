"""MEXC (spot only — futures is a separate API, disabled) is discovered by the name convention."""
from src.cex_v2.supervisor import _discover as discover_ob
from src.cex_v2.market_data.manager import _discover as discover_md, _make_handler


def test_supervisor_discovers_mexc_spot_only():
    by = {t.name: t for t in discover_ob(("spot", "futures"), exchanges=["mexc"])}
    assert set(by) == {"mexc_spot"}                            # futures disabled -> not discovered
    assert by["mexc_spot"].class_name == "MexcSpotConnector"
    assert by["mexc_spot"].module_path == "src.cex_v2.plugins.mexc"


def test_marketdata_discovers_mexc_spot_only():
    pairs = discover_md(("spot", "futures"), exchanges=["mexc"])
    assert ("mexc", "spot") in pairs and ("mexc", "futures") not in pairs
    hs = _make_handler("mexc", "spot")
    assert type(hs).__name__ == "MexcSpotMarketData" and hs.redis_key == "spot-market-data:mexc"
