import multiprocessing
import os
import time
import logging
import signal

####################################
from src.settings.config import Network
from src.logger_handler.logger import setup_logger, get_logger
from src.settings import config
from src.engine.osr import OnlineSmartRouter, OnlineSmartRouterConfigScheme
from src.settings.graceful_shut_down import TerminateSignal, sigterm_handler
####################################

# OnlineSmartRouter Supervisor
class OnlineSmartRouterSupervisor:
    CHECK_INTERVAL = 5

    def __init__(self, network: Network):
        self.network = network
        self.conf = OnlineSmartRouterConfigScheme(network=network)

        self.osr_process_name = f"osr.{network}"
        self.logger_name = f"osr.supervisor.{network}"
        self.log_file = os.path.join(
            config.SUPERVISOR_LOG_FOLDER, f"{self.logger_name}.log"
        )

    def _start_online_smart_router(self):
        osr = OnlineSmartRouter(self.conf)
        osr.start()

    def _start_osr(self, logger: logging.Logger, attempt: int):
        p = multiprocessing.Process(
            target=self._start_online_smart_router,
            name=self.osr_process_name,
        )
        p.start()
        start_time = time.time()
        logger.info(
            f"Started {self.osr_process_name} (PID: {p.pid}, attempt #{attempt})"
        )
        return p, start_time

    def RUN_ONLINE_SMART_ROUTER(self):
        signal.signal(signal.SIGTERM, sigterm_handler)

        setup_logger(logger_name=self.logger_name, log_file=self.log_file)
        logger = get_logger(logger_name=self.logger_name)

        logger.info(
            f"OSR Supervisor started. PID={os.getpid()}, network={self.network}, "
            f"worker_number={self.conf.worker_number}"
        )

        start_method = multiprocessing.get_start_method()
        if start_method != 'spawn':
            logger.critical(
                f"Wrong start method: {start_method}. Must be 'spawn'. Exiting."
            )
            return

        osr_worker: multiprocessing.Process | None = None
        osr_started_at: float = 0.0
        restart_count = 0

        while True:
            try:
                if osr_worker is None:
                    osr_worker, osr_started_at = self._start_osr(
                        logger, attempt=restart_count + 1
                    )
                elif not osr_worker.is_alive():
                    lifetime = time.time() - osr_started_at
                    exitcode = osr_worker.exitcode
                    dead_pid = osr_worker.pid
                    osr_worker.join()
                    restart_count += 1
                    logger.warning(
                        f"ALERT: {self.osr_process_name} (PID {dead_pid}) "
                        f"died unexpectedly! exitcode={exitcode}, "
                        f"lifetime={lifetime:.1f}s, restart_count={restart_count}. "
                        f"Restarting..."
                    )
                    osr_worker, osr_started_at = self._start_osr(
                        logger, attempt=restart_count + 1
                    )

            except (KeyboardInterrupt, TerminateSignal):
                logger.info(
                    f"Shutdown signal received. Stopping {self.osr_process_name}..."
                )
                if osr_worker is not None and osr_worker.is_alive():
                    osr_worker.terminate()
                    osr_worker.join(timeout=10)
                    if osr_worker.is_alive():
                        logger.warning(
                            f"{self.osr_process_name} didn't stop gracefully. Killing..."
                        )
                        osr_worker.kill()
                        osr_worker.join()
                logger.info("OSR Supervisor stopped.")
                break

            except Exception as e:
                logger.error(f"Supervisor error: {e}", exc_info=True)

            time.sleep(self.CHECK_INTERVAL)


class SolanaOSRSupervisor(OnlineSmartRouterSupervisor):
    def __init__(self):
        super().__init__("solana")


class EthereumOSRSupervisor(OnlineSmartRouterSupervisor):
    def __init__(self):
        super().__init__("eth")


class BinanceOSRSupervisor(OnlineSmartRouterSupervisor):
    def __init__(self):
        super().__init__("bsc")


class ArbitrumOSRSupervisor(OnlineSmartRouterSupervisor):
    def __init__(self):
        super().__init__("arbitrum")


class BaseOSRSupervisor(OnlineSmartRouterSupervisor):
    def __init__(self):
        super().__init__("base")