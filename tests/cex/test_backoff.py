"""RestartBackoff: exponential growth + cap, jitter bounds, note_uptime reset, should_give_up.
Restart-stability core used by the OB supervisor (_run / restart) and the market-data circuit
breaker; coverage restored after the cex_v2->cex migration deleted the legacy test_supervision/
test_reliability (which imported the now-removed producer paths)."""
from src.cex.core.backoff import RestartBackoff


def test_grows_exponentially_and_caps():
    bo = RestartBackoff(base=5, cap=60, factor=2, jitter=0.0)
    assert [bo.next_delay() for _ in range(6)] == [5, 10, 20, 40, 60, 60]   # jitter=0 -> raw; caps at 60


def test_jitter_within_bounds():
    bo = RestartBackoff(base=10, cap=100, factor=2, jitter=0.3)
    for expected_raw in (10, 20, 40, 80, 100, 100):
        d = bo.next_delay()                                       # raw + uniform(0, raw*jitter)
        assert expected_raw <= d <= expected_raw * 1.3


def test_note_uptime_resets_only_above_threshold():
    bo = RestartBackoff(base=5, reset_after=30, jitter=0.0)
    bo.next_delay(); bo.next_delay()
    assert bo.attempt == 2
    bo.note_uptime(29)                                            # below reset_after -> keep climbing
    assert bo.attempt == 2
    bo.note_uptime(30)                                            # >= reset_after -> reset
    assert bo.attempt == 0
    assert bo.next_delay() == 5                                   # back to base


def test_should_give_up_after_max_attempts():
    bo = RestartBackoff(base=1, jitter=0.0, max_attempts=3)
    assert bo.should_give_up() is False
    for _ in range(3):
        bo.next_delay()
    assert bo.should_give_up() is True


def test_no_give_up_when_max_attempts_none():
    bo = RestartBackoff(jitter=0.0)                               # default max_attempts=None
    for _ in range(100):
        bo.next_delay()
    assert bo.should_give_up() is False
