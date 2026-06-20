"""Bitget is discovered by the supervisor + market-data manager via the name convention (no registry edits)."""
from src.cex.supervisor import _discover as discover_ob
from src.cex.market_data.manager import _discover as discover_md, _make_handler


def test_supervisor_discovers_bitget():
    by = {t.name: t for t in discover_ob(("spot", "futures"), exchanges=["bitget"])}
    assert set(by) == {"bitget_spot", "bitget_futures"}
    assert by["bitget_spot"].class_name == "BitgetSpotConnector"
    assert by["bitget_futures"].class_name == "BitgetFuturesConnector"
    assert by["bitget_spot"].module_path == "src.cex.plugins.bitget"


def test_marketdata_discovers_bitget():
    pairs = discover_md(("spot", "futures"), exchanges=["bitget"])
    assert ("bitget", "spot") in pairs and ("bitget", "futures") in pairs
    hs = _make_handler("bitget", "spot")
    assert type(hs).__name__ == "BitgetSpotMarketData" and hs.redis_key == "spot-market-data:bitget"
    hf = _make_handler("bitget", "futures")
    assert type(hf).__name__ == "BitgetFuturesMarketData" and hf.market_type == "futures"
