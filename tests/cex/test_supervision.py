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


def test_healthcheck_exit_codes(rc, monkeypatch):
    import src.cex.healthcheck as hcmod
    monkeypatch.setattr(hcmod, "_redis_client", lambda: rc)
    assert hcmod.main(["--quiet"]) == 1
    from src.cex.health import enabled_pairs
    for ex, mt in enabled_pairs():
        _put_hb(rc, ex, mt, 0)
    assert hcmod.main(["--quiet"]) == 0
