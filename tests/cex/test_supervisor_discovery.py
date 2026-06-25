"""Supervisor target discovery + per-worker hung detection. Covers: single-worker default (no shard
ids), multi-worker fan-out (an exchange with workers:N -> N modulo-shards #0..#N-1, the kucoin-futures
sharding the connector's `i % num_workers == worker_id` split depends on), and _worker_health's
(exists, fresh) decision driving restart. Coverage restored after the migration deleted the legacy
test_supervision (which imported the now-removed src.cex.producer + src.supervisors.cex_supervisor)."""
import json

from src.cex.config import EXCHANGES, get_heartbeat_key
from src.cex.supervisor import _discover, _worker_health


def test_single_worker_targets_have_no_shard_ids():
    targets = {t.name: t for t in _discover(exchanges=["binance"])}
    assert {"binance_spot", "binance_futures"} <= set(targets)
    t = targets["binance_spot"]
    assert t.worker_id is None and t.num_workers is None         # single process -> connector not distributed
    assert t.module_path == "src.cex.plugins.binance"            # the dynamic-loader path
    assert t.class_name == "BinanceSpotConnector"


def test_multi_worker_fans_out_per_config():
    n = int(EXCHANGES["kucoin"]["futures"]["workers"])           # keyed off config (the only workers>1 leg, =4)
    assert n > 1
    fut = [t for t in _discover(exchanges=["kucoin"]) if t.market_type == "futures"]
    assert len(fut) == n
    assert sorted(t.worker_id for t in fut) == list(range(n))    # worker ids 0..n-1, no gaps/dupes
    assert all(t.num_workers == n for t in fut)                  # propagated -> shard math intact
    assert {t.name for t in fut} == {f"kucoin_futures#{i}" for i in range(n)}
    assert all(t.module_path == "src.cex.plugins.kucoin"
               and t.class_name == "KucoinFuturesConnector" for t in fut)
    spot = [t for t in _discover(exchanges=["kucoin"]) if t.market_type == "spot"]
    assert len(spot) == 1 and spot[0].worker_id is None and spot[0].name == "kucoin_spot"


def test_discover_respects_market_and_exchange_filters():
    assert all(t.market_type == "spot" for t in _discover(markets=("spot",)))
    assert {t.exchange for t in _discover(exchanges=["okx"])} == {"okx"}


class _FakeRC:
    """Minimal redis stand-in: _worker_health only does rc.get(key)."""
    def __init__(self, mapping): self._m = mapping
    def get(self, k): return self._m.get(k)


def test_worker_health_fresh_stale_missing_malformed():
    ex, mt, wid, hung, now = "binance", "spot", None, 120, 1_000_000.0
    key = get_heartbeat_key(ex, mt, wid)
    fresh = _FakeRC({key: json.dumps({"ts": int(now * 1000)})})
    assert _worker_health(fresh, ex, mt, wid, hung, now) == (True, True)
    stale = _FakeRC({key: json.dumps({"ts": int((now - hung - 10) * 1000)})})
    assert _worker_health(stale, ex, mt, wid, hung, now) == (True, False)   # >hung_timeout old -> restart
    assert _worker_health(_FakeRC({}), ex, mt, wid, hung, now) == (False, False)      # no key -> "no heartbeat"
    assert _worker_health(_FakeRC({key: "{bad"}), ex, mt, wid, hung, now) == (True, False)  # corrupt -> stale
