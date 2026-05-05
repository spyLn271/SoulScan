import multiprocessing
import time
import logging
import asyncio
import signal
from typing import Callable, Awaitable

####################################
from src.settings.graceful_shut_down import TerminateSignal, sigterm_handler
from src.settings.config import (
    Network,
    DEX,
    Version,
    EVM_NETWORKS
)
####################################



class FetcherSkeleton:
    def __init__(self, logger: logging.Logger, dex: DEX, version: Version, func: Callable[[Network], None]):
        self.logger = logger
        self.dex = dex
        self.version = version
        self.func = func

        self.workers: dict[Network, multiprocessing.Process] = {}
        self.last_restart: dict[Network, float] = {}
        self.MIN_RESTART_INTERVAL = 5.0


    def start_worker(self, network: Network) -> multiprocessing.Process:
        self.logger.info(f"Starting {self.dex} {self.version} state fetcher for {network}...")

        worker = multiprocessing.Process(
            target=self.func,
            args=(network, ),
            name=f"{self.dex}_{self.version}_{network}",
        )
        worker.start()

        self.logger.info(f"Started {self.dex} {self.version} state fetcher for {network} (PID: {worker.pid})")

        return worker

    def _init_workers(self):
        self.logger.info(
            f"Initializing {self.dex} {self.version} workers for {len(EVM_NETWORKS)} networks: {EVM_NETWORKS}"
        )
        for network in EVM_NETWORKS:
            self.workers[network] = self.start_worker(network)
        self.logger.info(f"All {self.dex} {self.version} workers initialized: {len(self.workers)}")

    def _shutdown_workers(self):
        for name, worker in self.workers.items():
            if worker.is_alive():
                self.logger.info(f"Terminating worker {name} (PID: {worker.pid})")
                worker.terminate()

        for name, worker in self.workers.items():
            worker.join(timeout=10)
            if worker.is_alive():
                self.logger.warning(f"Worker {name} did not exit; killing")
                worker.kill()
                worker.join()

        self.logger.info("All workers stopped.")

    def main(self):
        self.logger.info(f"Starting {self.dex} {self.version} supervisor (PID: {multiprocessing.current_process().pid})")
        signal.signal(signal.SIGTERM, sigterm_handler)

        self._init_workers()
        self.logger.info(f"{self.dex} {self.version} supervisor entering main loop")

        while True:
            try:
                for network, worker in self.workers.items():
                    if not worker.is_alive():
                        last = self.last_restart.get(network, 0.0)
                        elapsed = time.time() - last

                        if elapsed < self.MIN_RESTART_INTERVAL:
                            wait = self.MIN_RESTART_INTERVAL - elapsed
                            self.logger.warning(
                                f"{self.dex} {self.version} worker for {network} crashed within "
                                f"{elapsed:.1f}s; backing off {wait:.1f}s"
                            )
                            time.sleep(wait)


                        self.logger.warning(
                            f"{self.dex} {self.version} worker for {network} is dead. Restarting..."
                        )
                        worker.join()
                        self.workers[network] = self.start_worker(network)
                        self.last_restart[network] = time.time()

            except (KeyboardInterrupt, TerminateSignal):
                self.logger.info("Shutdown signal received. Stopping workers...")
                self._shutdown_workers()
                break

            except Exception as e:
                self.logger.error(f"Error occurred in main loop: {e}", exc_info=True)
                time.sleep(0.5)

            time.sleep(1)