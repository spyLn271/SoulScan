import asyncio
import multiprocessing
import os
import signal
import time

from src.settings import config
from src.settings.graceful_shut_down import TerminateSignal, sigterm_handler
from src.logger_handler.logger import setup_logger, get_logger
from src.cex.core.limits import install_orphan_guards, acquire_singleton_lock


WORKER_NAME = "cex-Contracts"
_SINGLETON_LOCK_FH = None


def bootstrap_cex_contracts_worker() -> None:
    install_orphan_guards()
    os.makedirs(config.CEX_CONTRACTS_LOG_FOLDER, exist_ok=True)
    log_file = os.path.join(config.CEX_CONTRACTS_LOG_FOLDER, f"{WORKER_NAME}.log")

    setup_logger(logger_name="", log_file=log_file)
    worker_logger = get_logger(WORKER_NAME)
    worker_logger.info(f"Worker process started. PID={os.getpid()}")

    try:
        asyncio.run(_run_updater_with_restart(worker_logger))
    except KeyboardInterrupt:
        worker_logger.info("Worker received stop signal.")
    except Exception as e:
        worker_logger.critical(f"Critical worker failure: {e}", exc_info=True)


async def _run_updater_with_restart(logger) -> None:
    from src.cex.contract_address_cex_checker.service.updater import UpdaterService

    while True:
        try:
            service = UpdaterService()
            await service.run_forever()
            logger.info("UpdaterService.run_forever() returned cleanly. Restart in 5s.")
        except Exception as e:
            logger.error(f"UpdaterService soft crash: {e}. Restart in 5s.", exc_info=True)
        await asyncio.sleep(5)


def _start_worker(sup_logger):
    process = multiprocessing.Process(
        target=bootstrap_cex_contracts_worker,
        name=f"CEXContracts-{WORKER_NAME}",
        daemon=True,
    )
    process.start()
    sup_logger.info(f"Started {WORKER_NAME} (PID: {process.pid})")
    return process


def RUN_CEX_CONTRACTS() -> None:
    signal.signal(signal.SIGTERM, sigterm_handler)

    os.makedirs(config.CEX_CONTRACTS_LOG_FOLDER, exist_ok=True)
    setup_logger(
        logger_name="cex-Contracts-Supervisor",
        log_file=os.path.join(config.CEX_CONTRACTS_LOG_FOLDER, "cex-Contracts-Supervisor.log"),
    )
    sup_logger = get_logger("cex-Contracts-Supervisor")
    sup_logger.info("cex Contracts Supervisor started.")

    global _SINGLETON_LOCK_FH
    _SINGLETON_LOCK_FH = acquire_singleton_lock(
        os.path.join(config.CEX_CONTRACTS_LOG_FOLDER, ".cex_contracts.lock"),
        sup_logger, "cex_contracts supervisor",
    )
    if _SINGLETON_LOCK_FH is None:
        return

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
