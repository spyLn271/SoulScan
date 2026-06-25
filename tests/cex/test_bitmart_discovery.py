"""BitMart is discovered by the supervisor + market-data manager via the name convention."""
from src.cex.supervisor import _discover as discover_ob
from src.cex.market_data.manager import _discover as discover_md, _make_handler


def test_supervisor_discovers_bitmart():
    by = {t.name: t for t in discover_ob(("spot", "futures"), exchanges=["bitmart"])}
    assert set(by) == {"bitmart_spot", "bitmart_futures"}
    assert by["bitmart_spot"].class_name == "BitmartSpotConnector"
    assert by["bitmart_futures"].class_name == "BitmartFuturesConnector"
    assert by["bitmart_spot"].module_path == "src.cex.plugins.bitmart"


def test_marketdata_discovers_bitmart():
    pairs = discover_md(("spot", "futures"), exchanges=["bitmart"])
    assert ("bitmart", "spot") in pairs and ("bitmart", "futures") in pairs
    hs = _make_handler("bitmart", "spot")
    assert type(hs).__name__ == "BitmartSpotMarketData" and hs.redis_key == "spot-market-data:bitmart"
    hf = _make_handler("bitmart", "futures")
    assert type(hf).__name__ == "BitmartFuturesMarketData" and hf.market_type == "futures"
