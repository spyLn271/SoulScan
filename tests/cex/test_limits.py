"""Process lifecycle guards: PR_SET_PDEATHSIG availability + the flock singleton lock (the
duplicate-worker guard — the root cause of the duplicate-kucoin incident). Coverage restored after
the cex_v2->cex migration deleted the legacy test_supervision."""
import logging
import os
import signal

from src.cex.core.limits import set_pdeathsig, acquire_singleton_lock

_log = logging.getLogger("test.limits")


def test_set_pdeathsig_supported():
    assert set_pdeathsig(signal.SIGKILL) is True                 # linux prctl path available -> orphan guard works


def test_singleton_lock_rejects_second_holder(tmp_path):
    p = str(tmp_path / "sup.lock")
    fh = acquire_singleton_lock(p, _log, "test")
    try:
        assert fh is not None                                    # first instance acquires
        assert acquire_singleton_lock(p, _log, "test") is None   # second refused while held (no duplicate workers)
        assert open(p).read() == str(os.getpid())                # holder pid written to the lockfile
    finally:
        fh.close()


def test_singleton_lock_reacquirable_after_release(tmp_path):
    p = str(tmp_path / "sup.lock")
    fh = acquire_singleton_lock(p, _log, "test")
    assert fh is not None
    fh.close()                                                   # flock auto-releases on close (and on death)
    fh2 = acquire_singleton_lock(p, _log, "test")
    assert fh2 is not None                                       # now re-acquirable -> no stale lock after exit
    fh2.close()
