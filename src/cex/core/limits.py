import ctypes
import fcntl
import os
import resource
import signal
import threading
import time

_DEFAULT_TARGET = 1_048_576
_PR_SET_PDEATHSIG = 1


def raise_fd_limit():
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    target = _DEFAULT_TARGET if hard == resource.RLIM_INFINITY else hard
    if soft < target:
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
        except (ValueError, OSError):
            pass

    return resource.getrlimit(resource.RLIMIT_NOFILE)


def set_pdeathsig(sig: int) -> bool:
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        return libc.prctl(_PR_SET_PDEATHSIG, ctypes.c_ulong(sig)) == 0
    except Exception:
        return False


def install_orphan_guards() -> None:
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
    fh = open(lock_path, "a+")
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
