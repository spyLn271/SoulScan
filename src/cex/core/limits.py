#!/usr/bin/env python3
"""
Process limits + lifecycle guards (carried over from the legacy helper — built and verified in
production this rebuild: SIGKILL the supervisor -> all workers die, 0 orphans).

  - raise_fd_limit():          soft RLIMIT_NOFILE -> hard, so a process can hold thousands of sockets.
  - install_orphan_guards():   a worker can never outlive its supervisor (PDEATHSIG + watchdog).
  - acquire_singleton_lock():  two instances of a supervisor can't run at once (flock).
"""
import ctypes
import fcntl
import os
import resource
import signal
import threading
import time

_DEFAULT_TARGET = 1_048_576
_PR_SET_PDEATHSIG = 1  # from <sys/prctl.h>


def raise_fd_limit():
    """Raise soft RLIMIT_NOFILE up to the hard limit (best-effort). Returns (soft, hard)."""
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    target = _DEFAULT_TARGET if hard == resource.RLIM_INFINITY else hard
    if soft < target:
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
        except (ValueError, OSError):
            pass
    return resource.getrlimit(resource.RLIMIT_NOFILE)


def set_pdeathsig(sig: int) -> bool:
    """Kernel sends `sig` to THIS process when its parent dies — fires even on SIGKILL/crash
    (a clean exit can't run, so multiprocessing daemon=True alone does NOT prevent orphans)."""
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        return libc.prctl(_PR_SET_PDEATHSIG, ctypes.c_ulong(sig)) == 0
    except Exception:
        return False


def install_orphan_guards() -> None:
    """Run inside every spawned worker so it can never outlive its supervisor:
      1) PR_SET_PDEATHSIG(SIGKILL) — kernel kills us the instant the supervisor dies.
      2) watchdog thread that exits if our parent changes (covers the arm race / reparenting)."""
    set_pdeathsig(signal.SIGKILL)
    orig_ppid = os.getppid()
    if orig_ppid == 1:
        os._exit(0)

    def _watch():
        while True:
            try:
                if os.getppid() != orig_ppid:
                    os._exit(0)
            except Exception:
                pass
            time.sleep(2)

    threading.Thread(target=_watch, name="orphan-watchdog", daemon=True).start()


def acquire_singleton_lock(lock_path: str, logger, label: str = "supervisor"):
    """Exclusive flock so two instances can't run (which would spawn duplicate workers). Returns
    the held file handle (CALLER must keep a reference), or None if another instance holds it.
    flock auto-releases on death (even SIGKILL), so a crash never leaves a stale lock."""
    fh = open(lock_path, "a+")  # 'a+' so we don't truncate the holder's pidfile on open
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, IOError):
        fh.close()
        logger.critical("Another %s already holds %s — refusing to start a second instance "
                        "(would create duplicate workers).", label, lock_path)
        return None
    fh.seek(0)
    fh.truncate(0)
    fh.write(str(os.getpid()))
    fh.flush()
    return fh
