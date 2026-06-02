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

from src.settings import cex_config as config
from src.settings.graceful_shut_down import TerminateSignal, sigterm_handler
from src.logger_handler.logger import setup_logger, get_logger
from src.cex.producer.core.backoff import RestartBackoff

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


def bootstrap_cex_worker(module_path: str, class_name: str) -> None:
    worker_name = f"cex-{class_name}"
    log_file = os.path.join(config.CEX_LOG_FOLDER, f"{worker_name}.log")

    setup_logger(logger_name=worker_name, log_file=log_file)
    worker_logger = get_logger(logger_name=worker_name)
    worker_logger.info(f"Worker process started. PID={os.getpid()}")

    try:
        module = importlib.import_module(module_path)
        connector_cls = getattr(module, class_name)
    except Exception as e:
        worker_logger.critical(f"Failed to import {module_path}.{class_name}: {e}", exc_info=True)
        return

    try:
        asyncio.run(_run_connector_loop(connector_cls, worker_logger))
    except KeyboardInterrupt:
        worker_logger.info("Worker received stop signal.")
    except Exception as e:
        worker_logger.critical(f"Critical worker failure: {e}", exc_info=True)


async def _run_connector_loop(connector_cls, logger) -> None:
    """Run a connector, restarting on soft-crash with exponential backoff."""
    backoff = RestartBackoff(base=5, cap=60)
    while True:
        started = time.monotonic()
        try:
            connector = connector_cls()
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
    """Return [(worker_name, module_path, class_name), ...] for every enabled
    (exchange, market_type) pair declared in the producer's EXCHANGES dict.
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
            worker_name = f"{exchange}_{market_type}"
            targets.append((worker_name, module_path, class_name))
    return targets


def _start_worker(worker_name: str, module_path: str, class_name: str, sup_logger):
    process = multiprocessing.Process(
        target=bootstrap_cex_worker,
        args=(module_path, class_name),
        name=f"CEXOrderbooks-{worker_name}",
        daemon=True,
    )
    process.start()
    sup_logger.info(f"Started {worker_name} (PID: {process.pid})")
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

    start_method = multiprocessing.get_start_method()
    if start_method != 'spawn':
        sup_logger.critical(f"Wrong start method: {start_method}. Must be 'spawn'. Exiting.")
        return

    targets = _discover_cex_targets()
    if not targets:
        sup_logger.critical("No enabled cex (exchange, market) pairs found. Exiting.")
        return

    sup_logger.info(f"Discovered {len(targets)} enabled worker targets: "
                    f"{[t[0] for t in targets]}")

    hung_timeout = MONITORING_CONFIG.get("hung_worker_timeout", 120)
    processes = {}
    targets_by_name = {name: (module, cls) for name, module, cls in targets}
    start_times = {}
    backoffs = {}
    next_restart_at = {}
    last_msgs = {}
    last_progress_at = {}

    def _spawn(worker_name):
        module_path, class_name = targets_by_name[worker_name]
        processes[worker_name] = _start_worker(worker_name, module_path, class_name, sup_logger)
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

    for worker_name, module_path, class_name in targets:
        _spawn(worker_name)

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

                exchange, market_type = worker_name.rsplit('_', 1)
                try:
                    ph = evaluate_pair(rc, exchange, market_type, hung_timeout)
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
