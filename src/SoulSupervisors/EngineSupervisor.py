import multiprocessing
import os
import time
import logging
from typing import Union, Type
import signal

####################################
from src.LoggerHandler.logger import setup_logger, get_logger
from src.Config import config
from src.SoulEngine.SmartRouter.OnlineSmartRouter import OnlineSmartRouter, OnlineSmartRouterConfigScheme
from src.Config.GracefullShutDown import TerminateSignal, sigterm_handler
####################################

# OnlineSmartRouter Supervisor
class OSRSupervisor:
    osr_process_name = "OnlineSmartRouter"
    CHECK_INTERVAL = 5

    @staticmethod
    def _start_online_smart_router():
        conf = OnlineSmartRouterConfigScheme()
        osr = OnlineSmartRouter(conf)
        osr.start()

    def _start_osr(self, logger: logging.Logger):
        p = multiprocessing.Process(
            target=self._start_online_smart_router,
            name=OSRSupervisor.osr_process_name,
        )
        p.start()
        logger.info(f"Started OnlineSmartRouter (PID: {p.pid})")
        return p

    def RUN_ONLINE_SMART_ROUTER(self):
        signal.signal(signal.SIGTERM, sigterm_handler)

        logger_name = "OSRSupervisor"
        log_file = os.path.join(config.LOG_MAIN_FOLDER, f"{logger_name}.log")
        setup_logger(logger_name=logger_name, log_file=log_file)
        logger = get_logger(logger_name=logger_name)

        start_method = multiprocessing.get_start_method()
        if start_method != 'spawn':
            logger.critical(f"Wrong start method: {start_method}. Must be 'spawn'. Exiting.")
            return

        osr_worker: multiprocessing.Process = None

        while True:
            try:
                if osr_worker is None:
                    osr_worker = self._start_osr(logger)
                elif not osr_worker.is_alive():
                    logger.error("OnlineSmartRouter died. Restarting...")
                    osr_worker.join()
                    osr_worker = self._start_osr(logger)

            except (KeyboardInterrupt, TerminateSignal):
                logger.info("Shutdown signal received. Stopping OnlineSmartRouter...")
                if osr_worker is not None and osr_worker.is_alive():
                    osr_worker.terminate()
                    osr_worker.join(timeout=10)
                    if osr_worker.is_alive():
                        logger.warning("OnlineSmartRouter didn't stop gracefully. Killing...")
                        osr_worker.kill()
                        osr_worker.join()
                logger.info("OSRSupervisor stopped.")
                break

            except Exception as e:
                logger.error(f"Supervisor error: {e}")

            time.sleep(self.CHECK_INTERVAL)
