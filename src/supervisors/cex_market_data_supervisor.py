"""cex Market Data Handlers Supervisor.

Wraps the existing `MarketDataManager` (which fans out to ~25 daemon threads,
one per enabled (exchange, market_type) pair) inside a single multiprocessing
child. Threading is preserved so all handlers share one redis.ConnectionPool.

The supervisor itself owns process-level signal handling, automatic respawn,
and the systemd-friendly graceful-shutdown contract that the rest of SoulScan
already speaks.
"""

import asyncio
import multiprocessing
import os
import signal
import time

from src.settings import cex_config as config
from src.settings.graceful_shut_down import TerminateSignal, sigterm_handler
from src.logger_handler.logger import setup_logger, get_logger


WORKER_NAME = "cex-MarketData"


def bootstrap_cex_market_data_worker() -> None:
    log_file = os.path.join(config.CEX_MARKET_DATA_LOG_FOLDER, f"{WORKER_NAME}.log")
    os.makedirs(config.CEX_MARKET_DATA_LOG_FOLDER, exist_ok=True)
    setup_logger(logger_name=WORKER_NAME, log_file=log_file)
    worker_logger = get_logger(logger_name=WORKER_NAME)
    worker_logger.info(f"Worker process started. PID={os.getpid()}")

    try:
        asyncio.run(_run_manager_with_restart(worker_logger))
    except KeyboardInterrupt:
        worker_logger.info("Worker received stop signal.")
    except Exception as e:
        worker_logger.critical(f"Critical worker failure: {e}", exc_info=True)


async def _run_manager_with_restart(logger) -> None:
    from src.cex.market_data.manager import MarketDataManager

    while True:
        try:
            manager = MarketDataManager()
            await manager.run()
            logger.info("MarketDataManager.run() returned cleanly. Restart in 5s.")
        except Exception as e:
            logger.error(f"MarketDataManager soft crash: {e}. Restart in 5s.", exc_info=True)
        await asyncio.sleep(5)


def _start_worker(sup_logger):
    process = multiprocessing.Process(
        target=bootstrap_cex_market_data_worker,
        name=f"CEXMarketData-{WORKER_NAME}",
        daemon=True,
    )
    process.start()
    sup_logger.info(f"Started {WORKER_NAME} (PID: {process.pid})")
    return process


def RUN_CEX_MARKET_DATA() -> None:
    """Entry point for systemd / run_supervisor.py."""
    signal.signal(signal.SIGTERM, sigterm_handler)

    os.makedirs(config.CEX_MARKET_DATA_LOG_FOLDER, exist_ok=True)
    setup_logger(
        logger_name="cex-MarketData-Supervisor",
        log_file=os.path.join(config.CEX_MARKET_DATA_LOG_FOLDER, "cex-MarketData-Supervisor.log"),
    )
    sup_logger = get_logger(logger_name="cex-MarketData-Supervisor")
    sup_logger.info("cex Market Data Supervisor started.")

    start_method = multiprocessing.get_start_method()
    if start_method != 'spawn':
        sup_logger.critical(f"Wrong start method: {start_method}. Must be 'spawn'. Exiting.")
        return

    process = _start_worker(sup_logger)

    while True:
        try:
            time.sleep(5)

            if process.is_alive():
                continue

            sup_logger.warning(
                f"ALERT: {WORKER_NAME} (PID {process.pid}) died unexpectedly! "
                f"exitcode={process.exitcode}. Restarting..."
            )
            process.join()
            process = _start_worker(sup_logger)

        except (KeyboardInterrupt, TerminateSignal):
            sup_logger.info("Supervisor stopping... terminating worker.")
            if process.is_alive():
                process.terminate()
            process.join(timeout=10)
            if process.is_alive():
                sup_logger.warning(f"{WORKER_NAME} didn't stop gracefully. Killing...")
                process.kill()
                process.join()
            sup_logger.info("Worker stopped.")
            break

        except Exception as e:
            sup_logger.critical(f"Supervisor loop failure: {e}", exc_info=True)
