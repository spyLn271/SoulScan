"""BingX is discovered by the supervisor + market-data manager via the name convention."""
from src.cex_v2.supervisor import _discover as discover_ob
from src.cex_v2.market_data.manager import _discover as discover_md, _make_handler


def test_supervisor_discovers_bingx():
    by = {t.name: t for t in discover_ob(("spot", "futures"), exchanges=["bingx"])}
    assert set(by) == {"bingx_spot", "bingx_futures"}
    assert by["bingx_spot"].class_name == "BingxSpotConnector"
    assert by["bingx_futures"].class_name == "BingxFuturesConnector"
    assert by["bingx_spot"].module_path == "src.cex_v2.plugins.bingx"


def test_marketdata_discovers_bingx():
    pairs = discover_md(("spot", "futures"), exchanges=["bingx"])
    assert ("bingx", "spot") in pairs and ("bingx", "futures") in pairs
    hs = _make_handler("bingx", "spot")
    assert type(hs).__name__ == "BingxSpotMarketData" and hs.redis_key == "spot-market-data:bingx"
    hf = _make_handler("bingx", "futures")
    assert type(hf).__name__ == "BingxFuturesMarketData" and hf.market_type == "futures"
