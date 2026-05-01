"""cex Orderbooks Supervisor.

Mirrors the shape of data_fetcher_supervisor.py but targets cex producer
connectors. Each enabled `(exchange, market_type)` pair runs as its own
multiprocessing.Process so a crashed plugin restarts independently.

Worker targets are passed as (module_path, class_name) strings so args are
trivially picklable under the `spawn` start method configured in
scripts/run_supervisor.py.
"""

import asyncio
import importlib
import multiprocessing
import os
import signal
import time

from src.settings import config
from src.settings.graceful_shut_down import TerminateSignal, sigterm_handler
from src.logger_handler.logger import setup_logger, get_logger


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
    while True:
        try:
            connector = connector_cls()
            await connector.start()
        except Exception as e:
            logger.error(
                f"[{connector_cls.__name__}] soft crash: {e}. Restart in 5s.",
                exc_info=True,
            )
            await asyncio.sleep(5)


def _discover_cex_targets() -> list[tuple[str, str, str]]:
    """Return [(worker_name, module_path, class_name), ...] for every enabled
    (exchange, market_type) pair declared in the producer's EXCHANGES dict.
    """
    from src.cex.producer.config import EXCHANGES

    targets: list[tuple[str, str, str]] = []
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

    processes: dict[str, multiprocessing.Process] = {}
    targets_by_name = {name: (module, cls) for name, module, cls in targets}

    for worker_name, module_path, class_name in targets:
        processes[worker_name] = _start_worker(worker_name, module_path, class_name, sup_logger)

    while True:
        try:
            time.sleep(5)

            for worker_name, process in list(processes.items()):
                if process.is_alive():
                    continue
                sup_logger.warning(
                    f"ALERT: {worker_name} (PID {process.pid}) died unexpectedly! "
                    f"exitcode={process.exitcode}. Restarting..."
                )
                process.join()
                module_path, class_name = targets_by_name[worker_name]
                processes[worker_name] = _start_worker(
                    worker_name, module_path, class_name, sup_logger
                )

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
