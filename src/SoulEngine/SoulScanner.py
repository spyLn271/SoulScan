import redis
import logging
import pydantic
import os
import time
import multiprocessing
import signal

####################################
from src.Config import config
from src.Config.GracefullShutDown import TerminateSignal, sigterm_handler
from src.SoulEngine.SoulHelper import (get_all_common_dict_of_tokens,
                                       break_dict_in_chunks)
from src.SoulEngine.SoulComparer import start_comparer
from src.LoggerHandler.logger import setup_logger, get_logger
####################################

class ScannerConfig(pydantic.BaseModel):
    logger_name: str = "Scanner"
    logger_file: str = "Scanner.log"
    worker_number: int = 5
    sleep_interval: int = 1
    token_list_update_interval: int = 60
    network: str = "Solana"
    dex: str = "Jupiter"

class Scanner:
    def __init__(self, conf: ScannerConfig):
        self.conf = conf

        setup_logger(logger_name=conf.logger_name,
                     log_file=os.path.join(config.SCANNER_LOG_FOLDER, conf.logger_file))
        self.logger = get_logger(conf.logger_name)

        self.logger.info(f"Scanner initialized. Config: {conf.model_dump()}")

        self.r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
        self.queue = multiprocessing.JoinableQueue()

        self.cache = {}
        self.workers = {}

    def _get_target_tokens(self) -> dict:
        """

        :return: {
                    "ZBCNpuD7YMXzTHB2fhGkGi78MNsHGLRXUhRewNRm9RU": {
                        "decimals": 6,
                        "symbol": "ZBCN"
                    },
                    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {
                        "decimals": 6,
                        "symbol": "USDC"
                    },
                    ...
                }
        """

        cached_data: dict = self.cache.get('target_tokens', {})
        if cached_data:
            cached_time: int = cached_data.get('time', 0)
            cached_tokens: dict = cached_data.get('tokens')

            if (cached_time + self.conf.token_list_update_interval > time.time() and
                    isinstance(cached_tokens, dict)):
                return cached_tokens

        target_tokens = get_all_common_dict_of_tokens(self.r)
        self.cache['target_tokens'] = {
            'time': time.time(),
            'tokens': target_tokens
        }

        return target_tokens

    def assign_task(self):
        target_tokens = self._get_target_tokens()
        generator = break_dict_in_chunks(worker_number=self.conf.worker_number, dict_to_break=target_tokens)
        for chunk in generator:
            self.queue.put(chunk)

    def _init_workers(self) -> bool:
        number_of_started_workers = 0
        worker_index = 0

        brute_stop = 0
        MAX_ATTEMPTS = self.conf.worker_number + 10

        while number_of_started_workers < self.conf.worker_number:
            try:
                w_name = f'Scanner_Worker_{worker_index}'

                worker = multiprocessing.Process(target=start_comparer,
                                                 args=(
                                                     self.conf.dex,
                                                     self.conf.network,
                                                     self.queue,
                                                 ),
                                                 name=w_name,
                                                 daemon=True)
                worker.start()
                self.logger.info(f"Started {w_name} (PID: {worker.pid})")

                self.workers[w_name] = worker

                number_of_started_workers += 1
                worker_index += 1

            except Exception as e:
                self.logger.error(f"Worker {worker_index} initialization failed. Exception: {e}")
                time.sleep(1)

            brute_stop += 1
            if brute_stop >= MAX_ATTEMPTS:
                self.logger.critical(
                    f"Critical Fail: Could only start {number_of_started_workers}/{self.conf.worker_number} workers.")
                return False

        return True

    def _shutdown_workers(self):
        for name, worker in self.workers.items():
            if worker.is_alive():
                worker.terminate()

        for name, worker in self.workers.items():
            worker.join(timeout=10)
            if worker.is_alive():
                worker.kill()
                worker.join()

        self.logger.info("All workers stopped.")

    def _restart_dead_worker(self, w_name) -> bool:
        try:
            worker = multiprocessing.Process(target=start_comparer,
                                             args=(
                                                 self.conf.dex,
                                                 self.conf.network,
                                                 self.queue,
                                             ),
                                             name=w_name,
                                             daemon=True)
            worker.start()
            self.logger.info(f"Restarted {w_name} (PID: {worker.pid})")

            self.workers[w_name] = worker
        except Exception as e:
            self.logger.error(f"Worker {w_name} restart failed. Exception: {e}")
            return False

        return True

    def _check_workers_health(self):
        for w_name, worker in list(self.workers.items()):
            if not worker.is_alive():
                self.logger.warning(f"{w_name} is dead. Restarting...")
                worker.join()
                self._restart_dead_worker(w_name)

    def start(self):
        signal.signal(signal.SIGTERM, sigterm_handler)

        are_workers_initialized = self._init_workers()
        if not are_workers_initialized:
            self.logger.critical("Critical Fail: Could not start any workers.")
            raise Exception("Critical Fail: Could not start any workers.")

        while True:
            try:
                self.assign_task()
                time.sleep(self.conf.sleep_interval)
                self._check_workers_health()

            except (KeyboardInterrupt, TerminateSignal):
                self.logger.info("Shutdown signal received. Stopping workers...")
                self._shutdown_workers()
                break

            except Exception as e:
                self.logger.error(f"Supervisor Loop Error: {e}")
                time.sleep(1)