"""Backoff helper, heartbeat health evaluation, and the healthcheck CLI."""
import json
import time
import pytest
import fakeredis

from src.cex.producer.core.backoff import RestartBackoff
from src.cex.health import evaluate_pair
from src.cex.producer.config import get_heartbeat_key


def test_backoff_grows_caps_and_resets():
    bo = RestartBackoff(base=5, cap=60, factor=2, jitter=0.0, reset_after=30)
    delays = [bo.next_delay() for _ in range(6)]
    assert delays[:4] == [5, 10, 20, 40]
    assert delays[4] == 60 and delays[5] == 60
    bo.note_uptime(10)
    assert bo.attempt == 6
    bo.note_uptime(45)
    assert bo.attempt == 0
    assert bo.next_delay() == 5


def test_backoff_jitter_within_bounds():
    bo = RestartBackoff(base=10, cap=100, factor=2, jitter=0.3)
    assert 10 <= bo.next_delay() <= 13


def test_backoff_give_up():
    bo = RestartBackoff(base=1, max_attempts=3)
    for _ in range(3):
        bo.next_delay()
    assert bo.should_give_up()


@pytest.fixture
def rc():
    return fakeredis.FakeStrictRedis(decode_responses=True)


def _put_hb(rc, ex, mt, wid, **over):
    hb = {"ts": int(time.time() * 1000), "msgs": 100, "active_symbols": 50,
          "redis_backpressured": False, "monitoring_healthy": True,
          "current_proxy": "socks5://x:1", "proxy_rotations": 0, "schema_version": 1}
    hb.update(over)
    rc.set(get_heartbeat_key(ex, mt, wid), json.dumps(hb))


def test_fresh_heartbeat_is_healthy(rc):
    _put_hb(rc, "bybit", "spot", 0)
    ph = evaluate_pair(rc, "bybit", "spot", hung_timeout=120)
    assert ph.healthy and ph.fresh_heartbeats == 1 and ph.active_symbols == 50


def test_stale_heartbeat_is_unhealthy(rc):
    _put_hb(rc, "bybit", "spot", 0, ts=int((time.time() - 600) * 1000))
    ph = evaluate_pair(rc, "bybit", "spot", hung_timeout=120)
    assert not ph.healthy and ph.heartbeats == 1 and ph.fresh_heartbeats == 0


def test_no_heartbeat_is_unhealthy(rc):
    ph = evaluate_pair(rc, "bybit", "spot", hung_timeout=120)
    assert not ph.healthy and ph.heartbeats == 0


def test_backpressure_marks_unhealthy(rc):
    _put_hb(rc, "okx", "spot", 0, redis_backpressured=True)
    ph = evaluate_pair(rc, "okx", "spot", hung_timeout=120)
    assert not ph.healthy and ph.backpressured


def test_multiple_workers_one_fresh_is_healthy(rc):
    _put_hb(rc, "gateio", "spot", 0, ts=int((time.time() - 600) * 1000))
    _put_hb(rc, "gateio", "spot", 1)
    ph = evaluate_pair(rc, "gateio", "spot", hung_timeout=120)
    assert ph.healthy and ph.heartbeats == 2 and ph.fresh_heartbeats == 1


def test_evaluate_pair_per_worker_isolates_one_hung_worker(rc):
    # Multi-worker supervisor restarts a SINGLE hung worker among N. The aggregate
    # ('*') view stays healthy (worker 1 fresh), but the per-worker view of worker 0
    # must report it hung so the supervisor restarts just that process.
    _put_hb(rc, "gateio", "spot", 0, ts=int((time.time() - 600) * 1000))  # hung
    _put_hb(rc, "gateio", "spot", 1)                                      # fresh
    agg = evaluate_pair(rc, "gateio", "spot", hung_timeout=120)
    assert agg.healthy and agg.heartbeats == 2  # aggregate hides the one hung worker
    w0 = evaluate_pair(rc, "gateio", "spot", hung_timeout=120, worker_id=0)
    assert w0.heartbeats == 1 and w0.fresh_heartbeats == 0 and not w0.healthy
    w1 = evaluate_pair(rc, "gateio", "spot", hung_timeout=120, worker_id=1)
    assert w1.healthy and w1.fresh_heartbeats == 1


def test_legacy_single_worker_health_key(rc):
    # worker_id=None reads the legacy ':none' heartbeat key (unchanged behavior for
    # single-process exchanges like kucoin/binance).
    _put_hb(rc, "kucoin", "spot", "none")
    ph = evaluate_pair(rc, "kucoin", "spot", hung_timeout=120, worker_id=None)
    assert ph.healthy and ph.heartbeats == 1


def test_discover_fans_out_by_workers_config():
    # The supervisor must honor the per-exchange `workers` config: an exchange with
    # workers:N spawns N processes (worker_id 0..N-1, num_workers=N); workers<=1 (or
    # unset, e.g. kucoin) stays a single legacy process (worker_id=None).
    from src.supervisors.cex_supervisor import _discover_cex_targets
    from src.cex.producer.config import EXCHANGES
    targets = _discover_cex_targets()
    by_ex = {}
    for t in targets:
        by_ex.setdefault((t.exchange, t.market_type), []).append(t)

    g = by_ex[("gateio", "spot")]
    expected_n = int(EXCHANGES["gateio"]["spot"].get("workers", 1))
    assert len(g) == expected_n and expected_n > 1
    assert sorted(t.worker_id for t in g) == list(range(expected_n))
    assert all(t.num_workers == expected_n for t in g)
    assert all(t.name == f"gateio_spot#{t.worker_id}" for t in g)

    # kucoin has no `workers` -> single legacy process (worker_id None, plain name).
    k = by_ex[("kucoin", "spot")]
    assert len(k) == 1 and k[0].worker_id is None and k[0].name == "kucoin_spot"


def test_supervisor_pdeathsig_supported():
    # The kernel parent-death signal is the primary orphan guard (workers die when
    # the supervisor dies, even on SIGKILL). Must be available on the deploy kernel.
    import signal as _sig
    import src.supervisors.cex_supervisor as sup
    assert sup._set_pdeathsig(_sig.SIGKILL) is True


def test_supervisor_singleton_lock_rejects_second(tmp_path, monkeypatch):
    # Two supervisors at once spawn duplicate workers (the duplicate-kucoin cause).
    # The flock singleton must let the first in and refuse the second.
    import logging
    import src.supervisors.cex_supervisor as sup
    monkeypatch.setattr(sup.config, "CEX_LOG_FOLDER", str(tmp_path))
    log = logging.getLogger("test-sup")
    saved = sup._SINGLETON_LOCK_FH
    sup._SINGLETON_LOCK_FH = None
    try:
        assert sup._acquire_singleton_lock(log) is True    # first instance acquires
        assert sup._acquire_singleton_lock(log) is False   # second instance refused
    finally:
        if sup._SINGLETON_LOCK_FH:
            sup._SINGLETON_LOCK_FH.close()
        sup._SINGLETON_LOCK_FH = saved


def test_healthcheck_exit_codes(rc, monkeypatch):
    import src.cex.healthcheck as hcmod
    monkeypatch.setattr(hcmod, "_redis_client", lambda: rc)
    assert hcmod.main(["--quiet"]) == 1
    from src.cex.health import enabled_pairs
    for ex, mt in enabled_pairs():
        _put_hb(rc, ex, mt, 0)
    assert hcmod.main(["--quiet"]) == 0
