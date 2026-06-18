"""cex Orderbooks Supervisor.

Mirrors the shape of data_fetcher_supervisor.py but targets cex producer
connectors. Each enabled `(exchange, market_type)` pair runs as its own
multiprocessing.Process so a crashed plugin restarts independently.

Worker targets are passed as (module_path, class_name) strings so args are
trivially picklable under the `spawn` start method.

Hardening (additive, backward-compatible):
- Beyond crash detection, the supervisor reads the per-worker heartbeats the
  connectors publish to Redis (`health:{exchange}:{market_type}:*`) and restarts
  workers that are *alive but hung* — no fresh heartbeat past a warmup window, or
  a frozen message counter while symbols are active.
- Restarts are paced by a shared exponential-backoff-with-jitter so a
  crash-looping worker does not thrash.
- A Redis outage is treated as a Redis problem (logged), never as a reason to
  mass-restart workers.
"""

import asyncio
import importlib
import multiprocessing
import os
import signal
import time
from collections import namedtuple

from src.settings import cex_config as config
from src.settings.graceful_shut_down import TerminateSignal, sigterm_handler
from src.logger_handler.logger import setup_logger, get_logger
from src.cex.producer.core.backoff import RestartBackoff
from src.cex.producer.core.limits import (
    raise_fd_limit,
    acquire_singleton_lock,
    install_orphan_guards as _install_orphan_guards,
    set_pdeathsig as _set_pdeathsig,
)

# Heartbeat-based liveness is best-effort: if these imports or Redis are
# unavailable the supervisor still does crash-only supervision.
try:
    import redis as _redis
    from src.cex.producer.config import get_redis_config, MONITORING_CONFIG
    from src.cex.health import evaluate_pair
    _HEARTBEAT_AVAILABLE = True
except Exception:  # pragma: no cover - defensive
    _HEARTBEAT_AVAILABLE = False
    MONITORING_CONFIG = {}

CHECK_INTERVAL = 5
STARTUP_GRACE = 90   # seconds before a worker is eligible for hung-detection

# One spawned process. For an exchange with `workers: N > 1` the (exchange, market)
# pair fans out into N Targets (worker_id 0..N-1, num_workers=N) so the connector's
# built-in modulo symbol split (_filter_symbols_for_worker) spreads the load across
# processes. N<=1 keeps the legacy single-process shape (worker_id=None -> heartbeat
# key suffix 'none', no symbol filtering) so currently-healthy exchanges are unchanged.
Target = namedtuple(
    "Target", "name module_path class_name exchange market_type worker_id num_workers"
)


_SINGLETON_LOCK_FH = None  # module-level so the held lock isn't garbage-collected


def _acquire_singleton_lock(sup_logger) -> bool:
    """Refuse to start if another cex_orderbooks supervisor is already running
    (would spawn duplicate workers). See limits.acquire_singleton_lock."""
    global _SINGLETON_LOCK_FH
    lock_path = os.path.join(config.CEX_LOG_FOLDER, ".cex_orderbooks.lock")
    _SINGLETON_LOCK_FH = acquire_singleton_lock(lock_path, sup_logger, "cex_orderbooks supervisor")
    return _SINGLETON_LOCK_FH is not None


def bootstrap_cex_worker(module_path: str, class_name: str,
                         worker_id: int = None, num_workers: int = None) -> None:
    _install_orphan_guards()
    # Distinct logger/log-file per worker so the N processes of a multi-worker
    # exchange don't interleave into one file. worker_id=None keeps the legacy name.
    suffix = "" if worker_id is None else f"-w{worker_id}"
    worker_name = f"cex-{class_name}{suffix}"
    log_file = os.path.join(config.CEX_LOG_FOLDER, f"{worker_name}.log")

    setup_logger(logger_name=worker_name, log_file=log_file)
    worker_logger = get_logger(logger_name=worker_name)
    # Individual-connection exchanges (gateio ~2113, bybit ~530) need one socket
    # per symbol; raise the soft FD limit so the process can hold them all.
    soft, hard = raise_fd_limit()
    worker_logger.info(
        f"Worker process started. PID={os.getpid()} "
        f"worker_id={worker_id} num_workers={num_workers} "
        f"(RLIMIT_NOFILE soft={soft} hard={hard})"
    )

    try:
        module = importlib.import_module(module_path)
        connector_cls = getattr(module, class_name)
    except Exception as e:
        worker_logger.critical(f"Failed to import {module_path}.{class_name}: {e}", exc_info=True)
        return

    try:
        asyncio.run(_run_connector_loop(connector_cls, worker_logger, worker_id, num_workers))
    except KeyboardInterrupt:
        worker_logger.info("Worker received stop signal.")
    except Exception as e:
        worker_logger.critical(f"Critical worker failure: {e}", exc_info=True)


async def _run_connector_loop(connector_cls, logger, worker_id=None, num_workers=None) -> None:
    """Run a connector, restarting on soft-crash with exponential backoff."""
    backoff = RestartBackoff(base=5, cap=60)
    while True:
        started = time.monotonic()
        try:
            # worker_id=None -> single-process legacy call (monitors all symbols).
            if worker_id is None:
                connector = connector_cls()
            else:
                connector = connector_cls(worker_id=worker_id, num_workers=num_workers)
            await connector.start()
        except Exception as e:
            uptime = time.monotonic() - started
            backoff.note_uptime(uptime)  # a long run resets the curve
            delay = backoff.next_delay()
            logger.error(
                f"[{connector_cls.__name__}] soft crash after {uptime:.0f}s: {e}. "
                f"Restart in {delay:.0f}s.",
                exc_info=True,
            )
            await asyncio.sleep(delay)


def _discover_cex_targets() -> list:
    """Return a list of Target for every enabled (exchange, market_type) pair in the
    producer's EXCHANGES dict. A pair with `workers: N > 1` fans out into N Targets so
    its symbols are split across N processes (modulo distribution in the connector);
    N<=1 stays a single legacy process (worker_id=None).
    """
    from src.cex.producer.config import EXCHANGES

    targets = []
    for exchange, cfg in EXCHANGES.items():
        if not cfg.get('enabled', False):
            continue
        for market_type in ('spot', 'futures'):
            market_cfg = cfg.get(market_type, {})
            if not market_cfg.get('enabled', False):
                continue
            class_name = f"{exchange.title()}{market_type.title()}Connector"
            module_path = f"src.cex.producer.plugins.{exchange}_plugin"
            try:
                n = int(market_cfg.get('workers', 1) or 1)
            except (TypeError, ValueError):
                n = 1
            n = max(1, n)
            if n == 1:
                targets.append(Target(
                    f"{exchange}_{market_type}", module_path, class_name,
                    exchange, market_type, None, None,
                ))
            else:
                for i in range(n):
                    targets.append(Target(
                        f"{exchange}_{market_type}#{i}", module_path, class_name,
                        exchange, market_type, i, n,
                    ))
    return targets


def _start_worker(target: "Target", sup_logger):
    process = multiprocessing.Process(
        target=bootstrap_cex_worker,
        args=(target.module_path, target.class_name, target.worker_id, target.num_workers),
        name=f"CEXOrderbooks-{target.name}",
        daemon=True,
    )
    process.start()
    sup_logger.info(f"Started {target.name} (PID: {process.pid})")
    return process


def _make_redis():
    """Best-effort sync Redis client for heartbeat reads (short timeouts)."""
    if not _HEARTBEAT_AVAILABLE:
        return None
    try:
        cfg = get_redis_config()
        client = _redis.Redis(
            host=cfg["host"], port=cfg["port"], db=cfg.get("db", 0),
            password=cfg.get("password"), decode_responses=True,
            socket_connect_timeout=3, socket_timeout=3,
        )
        client.ping()
        return client
    except Exception:
        return None


def RUN_CEX_ORDERBOOKS() -> None:
    """Entry point for systemd / run_supervisor.py."""
    signal.signal(signal.SIGTERM, sigterm_handler)

    setup_logger(
        logger_name="cex-Orderbooks",
        log_file=os.path.join(config.CEX_LOG_FOLDER, "cex-Orderbooks.log"),
    )
    sup_logger = get_logger(logger_name="cex-Orderbooks")
    sup_logger.info("cex Orderbooks Supervisor started.")

    # Singleton guard: never run two supervisors at once (that spawns duplicate
    # workers — the duplicate-kucoin problem). Released automatically if we die.
    if not _acquire_singleton_lock(sup_logger):
        return

    # Raise the FD limit in the parent before spawning; children inherit it.
    soft, hard = raise_fd_limit()
    sup_logger.info(f"RLIMIT_NOFILE raised to soft={soft} hard={hard} (children inherit).")

    start_method = multiprocessing.get_start_method()
    if start_method != 'spawn':
        sup_logger.critical(f"Wrong start method: {start_method}. Must be 'spawn'. Exiting.")
        return

    targets = _discover_cex_targets()
    if not targets:
        sup_logger.critical("No enabled cex (exchange, market) pairs found. Exiting.")
        return

    sup_logger.info(f"Discovered {len(targets)} enabled worker targets: "
                    f"{[t.name for t in targets]}")

    hung_timeout = MONITORING_CONFIG.get("hung_worker_timeout", 120)
    processes = {}
    targets_by_name = {t.name: t for t in targets}
    start_times = {}
    backoffs = {}
    next_restart_at = {}
    last_msgs = {}
    last_progress_at = {}

    def _spawn(worker_name):
        target = targets_by_name[worker_name]
        processes[worker_name] = _start_worker(target, sup_logger)
        start_times[worker_name] = time.monotonic()
        last_progress_at[worker_name] = time.monotonic()
        last_msgs[worker_name] = 0
        backoffs.setdefault(worker_name, RestartBackoff(base=CHECK_INTERVAL, cap=60))

    def _restart(worker_name, reason):
        now = time.monotonic()
        if now < next_restart_at.get(worker_name, 0):
            return  # still inside this worker's backoff window
        bo = backoffs.setdefault(worker_name, RestartBackoff(base=CHECK_INTERVAL, cap=60))
        bo.note_uptime(now - start_times.get(worker_name, now))
        old = processes.get(worker_name)
        if old and old.is_alive():
            old.terminate()
            old.join(timeout=10)
            if old.is_alive():
                old.kill()
                old.join()
        elif old:
            old.join()
        _spawn(worker_name)
        delay = bo.next_delay()
        next_restart_at[worker_name] = time.monotonic() + delay
        sup_logger.warning(f"Restarted {worker_name} due to {reason}; "
                           f"next restart throttled ~{delay:.0f}s (attempt {bo.attempt})")

    for target in targets:
        _spawn(target.name)

    while True:
        try:
            time.sleep(CHECK_INTERVAL)
            now = time.monotonic()
            rc = _make_redis()  # None if Redis down -> crash-only supervision this cycle

            for worker_name, process in list(processes.items()):
                # 1) crash detection (always)
                if not process.is_alive():
                    sup_logger.warning(
                        f"ALERT: {worker_name} (PID {process.pid}) died unexpectedly! "
                        f"exitcode={process.exitcode}. Restarting..."
                    )
                    _restart(worker_name, "crash")
                    continue

                # 2) hung detection (only when Redis reachable + past warmup)
                if rc is None or (now - start_times.get(worker_name, now)) < STARTUP_GRACE:
                    continue

                target = targets_by_name[worker_name]
                try:
                    # Per-worker heartbeat (health:{ex}:{mt}:{worker_id}); for a single
                    # worker (worker_id=None) this reads the legacy ':none' key. A hung
                    # worker among N is detected and restarted on its own.
                    ph = evaluate_pair(rc, target.exchange, target.market_type,
                                       hung_timeout, worker_id=target.worker_id)
                except Exception as e:
                    sup_logger.debug(f"heartbeat read failed for {worker_name}: {e}")
                    continue

                if ph.total_msgs > last_msgs.get(worker_name, 0):
                    last_msgs[worker_name] = ph.total_msgs
                    last_progress_at[worker_name] = now

                if ph.heartbeats == 0:
                    _restart(worker_name, f"no heartbeat after {STARTUP_GRACE}s warmup")
                elif ph.fresh_heartbeats == 0:
                    _restart(worker_name, f"stale heartbeat (>{hung_timeout}s)")
                elif ph.active_symbols > 0 and (now - last_progress_at.get(worker_name, now)) > 2 * hung_timeout:
                    _restart(worker_name, "frozen message counter")

        except (KeyboardInterrupt, TerminateSignal):
            sup_logger.info("Supervisor stopping... terminating workers.")
            for process in processes.values():
                if process.is_alive():
                    process.terminate()

            for worker_name, process in processes.items():
                process.join(timeout=10)
                if process.is_alive():
                    sup_logger.warning(f"{worker_name} didn't stop gracefully. Killing...")
                    process.kill()
                    process.join()

            sup_logger.info("All workers stopped.")
            break

        except Exception as e:
            sup_logger.critical(f"Supervisor loop failure: {e}", exc_info=True)
