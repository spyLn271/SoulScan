#!/usr/bin/env python3
"""
cex_v2 order-book supervisor — clean rebuild.

Spawns one process per (exchange, market, worker) from cex_v2.config.EXCHANGES (an exchange with
workers:N fans out into N processes that modulo-split symbols). Built-in from day one:
  - orphan guards in every worker (PDEATHSIG + watchdog) -> no worker outlives the supervisor;
  - a flock singleton -> two supervisors can't run (no duplicate workers);
  - per-worker hung detection (its heartbeat expired/stale -> restart just that worker);
  - exponential-backoff restarts.

Run: python -m src.cex.supervisor
"""
import asyncio
import importlib
import json
import logging
import multiprocessing
import os
import signal
import time
from collections import namedtuple

import redis as _redis

from src.cex.config import EXCHANGES, MONITORING, METRICS, get_redis_config, get_heartbeat_key
from src.cex.core.limits import raise_fd_limit, install_orphan_guards, acquire_singleton_lock
from src.cex.core.backoff import RestartBackoff
from src.cex.observability import setup_logging
from src.cex.observability import metrics as _metrics

log = logging.getLogger("cexv2.supervisor")

Target = namedtuple("Target", "name exchange market_type worker_id num_workers module_path class_name")


def _lock_path(markets, exchanges) -> str:
    mk = "-".join(sorted(markets))
    ex = "all" if not exchanges else "-".join(sorted(exchanges))
    return f"/tmp/.cex_v2_orderbook_{mk}_{ex}.lock"


def _discover(markets=("spot", "futures"), exchanges=None) -> list:
    targets = []
    for exchange, cfg in EXCHANGES.items():
        if not cfg.get("enabled", False):
            continue
        if exchanges and exchange not in exchanges:
            continue
        for mt in ("spot", "futures"):
            if mt not in markets:
                continue
            mc = cfg.get(mt, {})
            if not mc.get("enabled", False):
                continue
            cls = f"{exchange.title()}{mt.title()}Connector"
            mod = f"src.cex.plugins.{exchange}"
            try:
                n = max(1, int(mc.get("workers", 1) or 1))
            except (TypeError, ValueError):
                n = 1
            if n == 1:
                targets.append(Target(f"{exchange}_{mt}", exchange, mt, None, None, mod, cls))
            else:
                for i in range(n):
                    targets.append(Target(f"{exchange}_{mt}#{i}", exchange, mt, i, n, mod, cls))
    return targets


def bootstrap_worker(module_path: str, class_name: str, worker_id, num_workers,
                     exchange=None, market=None, metrics_port=None) -> None:
    """Child entrypoint (spawned). Installs orphan guards + per-worker logging + fast event loop +
    a /metrics server, then runs the connector with restart."""
    install_orphan_guards()
    raise_fd_limit()
    setup_logging("orderbook", exchange, market, worker_id)
    suffix = "" if worker_id is None else f"-w{worker_id}"
    wlog = logging.getLogger(f"cexv2.worker.{class_name}{suffix}")
    try:
        import uvloop
        uvloop.install()
        wlog.info("uvloop event loop enabled")
    except Exception as e:
        wlog.warning("uvloop unavailable (%s); falling back to the default asyncio loop", e)
    if metrics_port:
        _metrics.start_metrics_server(metrics_port, enabled=METRICS["enabled"], addr=METRICS["bind_host"])
    try:
        cls = getattr(importlib.import_module(module_path), class_name)
    except Exception as e:
        wlog.critical("import %s.%s failed: %s", module_path, class_name, e)
        return
    backoff = RestartBackoff(base=5, cap=60)
    try:
        asyncio.run(_run(cls, worker_id, num_workers, backoff, wlog))
    except KeyboardInterrupt:
        pass


async def _run(cls, worker_id, num_workers, backoff, wlog):
    while True:
        started = time.monotonic()
        conn = None
        try:
            conn = cls() if worker_id is None else cls(worker_id=worker_id, num_workers=num_workers)
            await conn.start()
        except Exception as e:
            backoff.note_uptime(time.monotonic() - started)
            d = backoff.next_delay()
            wlog.error("soft crash: %s. restart in %.0fs", e, d, exc_info=True)
            await asyncio.sleep(d)
        finally:
            # release the prior connector's redis (+ signal its tasks) before re-creating it, so a
            # repeatedly-failing worker doesn't accrue redis connections across restarts
            if conn is not None:
                try:
                    await conn.cleanup()
                except Exception:
                    pass


def _spawn(t: Target, metrics_port=None):
    p = multiprocessing.Process(target=bootstrap_worker,
                                args=(t.module_path, t.class_name, t.worker_id, t.num_workers,
                                      t.exchange, t.market_type, metrics_port),
                                name=f"cexv2-{t.name}", daemon=True)
    p.start()
    log.info("started %s (pid %s, metrics :%s)", t.name, p.pid, metrics_port or "off")
    return p


def _worker_health(rc, ex, mt, worker_id, hung_timeout, now):
    """(exists, fresh) for one worker's heartbeat key."""
    raw = rc.get(get_heartbeat_key(ex, mt, worker_id))
    if not raw:
        return False, False
    try:
        hb = json.loads(raw)
    except (ValueError, TypeError):
        return True, False
    return True, (now - hb.get("ts", 0) / 1000.0) <= hung_timeout


def RUN(markets=("spot", "futures"), exchanges=None):
    """Run the order-book supervisor for the selected market types + exchanges.
    markets: subset of ('spot','futures'). exchanges: allowlist of names, or None=all enabled."""
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    setup_logging("supervisor")
    soft, hard = raise_fd_limit()
    sel = f"markets={','.join(markets)} exchanges={'all' if not exchanges else ','.join(exchanges)}"
    log.info("cex_v2 orderbook supervisor starting [%s] (RLIMIT_NOFILE soft=%s hard=%s)", sel, soft, hard)

    lock = acquire_singleton_lock(_lock_path(markets, exchanges), log, f"cex_v2 orderbook supervisor [{sel}]")
    if lock is None:
        return

    if multiprocessing.get_start_method(allow_none=True) != "spawn":
        try:
            multiprocessing.set_start_method("spawn", force=True)
        except RuntimeError:
            pass

    targets = _discover(markets, exchanges)
    if not targets:
        log.critical("no enabled cex_v2 targets for %s; exiting", sel)
        return
    log.info("discovered %d worker targets: %s", len(targets), [t.name for t in targets])

    # Deterministic /metrics port per worker, assigned from the FULL registry order (NOT just this run's
    # subset) so a per-exchange supervisor gives a target the same port a combined run would — two
    # per-exchange supervisors never collide, no env knob needed. md uses md_base+offset (below).
    base = METRICS["port_base"]
    metrics_ports = {}
    if METRICS["enabled"]:
        all_targets = _discover(("spot", "futures"), exchanges=None)
        port_of = {t.name: base + 1 + i for i, t in enumerate(all_targets)}
        if base + len(all_targets) >= METRICS["md_base"]:
            log.critical("too many targets (%d) for the OB metrics band [%d..%d); OB metrics disabled",
                         len(all_targets), base + 1, METRICS["md_base"])
        else:
            metrics_ports = {t.name: port_of[t.name] for t in targets if t.name in port_of}

    hung_timeout = MONITORING["hung_worker_timeout"]
    grace = MONITORING["startup_grace"]
    check = MONITORING["check_interval"]
    by_name = {t.name: t for t in targets}
    procs, start_times, backoffs, next_restart = {}, {}, {}, {}

    def spawn(name):
        procs[name] = _spawn(by_name[name], metrics_ports.get(name))
        start_times[name] = time.monotonic()
        backoffs.setdefault(name, RestartBackoff(base=check, cap=60))

    def restart(name, reason):
        now = time.monotonic()
        if now < next_restart.get(name, 0):
            return
        bo = backoffs.setdefault(name, RestartBackoff(base=check, cap=60))
        bo.note_uptime(now - start_times.get(name, now))
        old = procs.get(name)
        if old and old.is_alive():
            old.terminate(); old.join(timeout=10)
            if old.is_alive():
                old.kill(); old.join()
        spawn(name)
        next_restart[name] = time.monotonic() + bo.next_delay()
        log.warning("restarted %s: %s", name, reason)

    for t in targets:
        spawn(t.name)

    rc = None  # persistent health-check client (reused across ticks; recreated only on failure)
    try:
        while True:
            time.sleep(check)
            now_m = time.monotonic()
            try:
                if rc is None:
                    rc = _redis.Redis(**get_redis_config(), socket_connect_timeout=3, socket_timeout=3,
                                      client_name="cexv2:supervisor")
                rc.ping()
            except Exception:
                if rc is not None:
                    try:
                        rc.close()
                    except Exception:
                        pass
                rc = None
            now = time.time()
            for name, p in list(procs.items()):
                if not p.is_alive():
                    restart(name, f"crash (exitcode={p.exitcode})")
                    continue
                if rc is None or (now_m - start_times.get(name, now_m)) < grace:
                    continue
                t = by_name[name]
                exists, fresh = _worker_health(rc, t.exchange, t.market_type, t.worker_id, hung_timeout, now)
                if not exists:
                    restart(name, "no heartbeat (expired)")
                elif not fresh:
                    restart(name, f"stale heartbeat (>{hung_timeout}s)")
    except KeyboardInterrupt:
        log.info("supervisor stopping; terminating workers")
        for p in procs.values():
            if p.is_alive():
                p.terminate()
        for p in procs.values():
            p.join(timeout=5)
            if p.is_alive():
                p.kill()


if __name__ == "__main__":
    RUN()
