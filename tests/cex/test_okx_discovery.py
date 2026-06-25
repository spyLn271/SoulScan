"""OKX is discovered by the supervisor + market-data manager via the name convention (no registry edits)."""
from src.cex.supervisor import _discover as discover_ob
from src.cex.market_data.manager import _discover as discover_md, _make_handler


def test_supervisor_discovers_okx():
    by = {t.name: t for t in discover_ob(("spot", "futures"), exchanges=["okx"])}
    assert set(by) == {"okx_spot", "okx_futures"}
    assert by["okx_spot"].class_name == "OkxSpotConnector"
    assert by["okx_futures"].class_name == "OkxFuturesConnector"
    assert by["okx_spot"].module_path == "src.cex.plugins.okx"


def test_marketdata_discovers_okx():
    pairs = discover_md(("spot", "futures"), exchanges=["okx"])
    assert ("okx", "spot") in pairs and ("okx", "futures") in pairs
    hs = _make_handler("okx", "spot")
    assert type(hs).__name__ == "OkxSpotMarketData" and hs.redis_key == "spot-market-data:okx"
    hf = _make_handler("okx", "futures")
    assert type(hf).__name__ == "OkxFuturesMarketData" and hf.market_type == "futures"
