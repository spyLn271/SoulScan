#!/usr/bin/env python3
"""
cex_v2 market-data manager — single process, one thread per enabled (exchange, market) handler.
Singleton flock (no duplicate market-data processes), clean shutdown, per-handler restart on crash.
Atomic MULTI/EXEC writes mean a daemon thread killed mid-cycle never leaves a partial hash.

Run: python -m src.cex_v2.market_data.manager
"""
import importlib
import logging
import signal
import threading
import time

from src.cex_v2.config import MARKET_DATA, METRICS, metrics_offset
from src.cex_v2.core.backoff import RestartBackoff
from src.cex_v2.core.limits import acquire_singleton_lock
from src.cex_v2.observability import setup_logging
from src.cex_v2.observability import metrics as _metrics

log = logging.getLogger("cexv2.md.manager")

def _lock_path(markets, exchanges) -> str:
    mk = "-".join(sorted(markets))
    ex = "all" if not exchanges else "-".join(sorted(exchanges))
    return f"/tmp/.cex_v2_marketdata_{mk}_{ex}.lock"


def _discover(markets=("spot", "futures"), exchanges=None):
    pairs = []
    for ex, cfg in MARKET_DATA.items():
        if exchanges and ex not in exchanges:
            continue
        for mt, mc in cfg.items():
            if mt not in markets:
                continue
            if mc.get("enabled", True):
                pairs.append((ex, mt))
    return pairs


def _make_handler(exchange, market_type):
    mod = importlib.import_module(f"src.cex_v2.market_data.handlers.{exchange}")
    cls = getattr(mod, f"{exchange.title()}{market_type.title()}MarketData")
    return cls()


class MarketDataManager:
    def __init__(self):
        self.stop = threading.Event()
        self.handlers = {}
        self.threads = {}

    def _run_handler(self, name, exchange, market_type):
        backoff = RestartBackoff(base=5, cap=60)
        while not self.stop.is_set():
            started = time.monotonic()
            h = None
            try:
                h = _make_handler(exchange, market_type)
                if not h.initialize():
                    time.sleep(backoff.next_delay()); continue
                self.handlers[name] = h
                h.run()  # loops until shutdown_requested
                if self.stop.is_set():
                    break
                log.warning("%s handler returned unexpectedly; restarting", name)
            except Exception as e:
                log.error("%s handler crashed: %s", name, e, exc_info=True)
            finally:
                # ALWAYS release the handler's httpx.Client + redis before re-creating it; otherwise
                # a crash-looping handler leaks keep-alive sockets per restart (httpx has no __del__).
                if h is not None:
                    try:
                        h.cleanup()
                    except Exception:
                        pass
            backoff.note_uptime(time.monotonic() - started)
            if not self.stop.is_set():
                time.sleep(backoff.next_delay())

    def start(self, pairs):
        for ex, mt in pairs:
            name = f"{ex}_{mt}"
            t = threading.Thread(target=self._run_handler, args=(name, ex, mt), name=f"md-{name}", daemon=True)
            self.threads[name] = t
            t.start()
            log.info("started market-data handler %s", name)

    def shutdown(self):
        self.stop.set()
        for h in self.handlers.values():
            h.shutdown_requested = True
        for t in self.threads.values():
            t.join(timeout=8)
        for h in self.handlers.values():   # belt-and-suspenders: close resources of any handler whose
            try:                           # thread didn't reach its own cleanup (join timeout)
                h.cleanup()
            except Exception:
                pass


_LOCK_FH = None


def RUN(markets=("spot", "futures"), exchanges=None):
    """Run the market-data manager for the selected market types + exchanges."""
    global _LOCK_FH
    # per-exchange-selection log file (marketdata_<ex>.log) so separate md managers don't share one file
    setup_logging("marketdata", exchange="-".join(exchanges) if exchanges else None)
    if METRICS["enabled"]:
        md_off = min((metrics_offset(e) for e in exchanges), default=0) if exchanges else 0
        _metrics.start_metrics_server(METRICS["md_base"] + md_off, addr=METRICS["bind_host"])  # ob uses base+1..
    sel = f"markets={','.join(markets)} exchanges={'all' if not exchanges else ','.join(exchanges)}"
    _LOCK_FH = acquire_singleton_lock(_lock_path(markets, exchanges), log, f"cex_v2 market-data manager [{sel}]")
    if _LOCK_FH is None:
        return
    mgr = MarketDataManager()

    def _sig(*_):
        log.info("shutdown signal; stopping handlers")
        mgr.stop.set()

    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)

    pairs = _discover(markets, exchanges)
    if not pairs:
        log.critical("no enabled market-data pairs for %s; exiting", sel)
        return
    log.info("cex_v2 market-data manager [%s]: %d handlers %s", sel, len(pairs), [f"{e}_{m}" for e, m in pairs])
    mgr.start(pairs)
    try:
        while not mgr.stop.is_set():
            time.sleep(0.5)
    finally:
        mgr.shutdown()
        log.info("market-data manager stopped")


if __name__ == "__main__":
    RUN()
