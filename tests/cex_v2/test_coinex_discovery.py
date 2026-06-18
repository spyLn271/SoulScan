"""CoinEx is discovered by the supervisor + market-data manager via the name convention."""
from src.cex_v2.supervisor import _discover as discover_ob
from src.cex_v2.market_data.manager import _discover as discover_md, _make_handler


def test_supervisor_discovers_coinex():
    by = {t.name: t for t in discover_ob(("spot", "futures"), exchanges=["coinex"])}
    assert set(by) == {"coinex_spot", "coinex_futures"}
    assert by["coinex_spot"].class_name == "CoinexSpotConnector"
    assert by["coinex_futures"].class_name == "CoinexFuturesConnector"
    assert by["coinex_spot"].module_path == "src.cex_v2.plugins.coinex"


def test_marketdata_discovers_coinex():
    pairs = discover_md(("spot", "futures"), exchanges=["coinex"])
    assert ("coinex", "spot") in pairs and ("coinex", "futures") in pairs
    hs = _make_handler("coinex", "spot")
    assert type(hs).__name__ == "CoinexSpotMarketData" and hs.redis_key == "spot-market-data:coinex"
    hf = _make_handler("coinex", "futures")
    assert type(hf).__name__ == "CoinexFuturesMarketData" and hf.market_type == "futures"
