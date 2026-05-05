import asyncio
import multiprocessing
import os
import time
import logging
from typing import Union, Type
import signal

####################################
from src.dex.evm.data_fetcher.state.uniswap_v2 import UniswapV2StateFetcher
from src.dex.evm.data_fetcher.state.uniswap_v3 import UniswapV3StateFetcher
from src.dex.evm.data_fetcher.state.uniswap_v4 import UniswapV4StateFetcher
from src.dex.solana.data_fetcher import MeteoraDlmmState, RaydiumClmmState, RaydiumAmmState, OrcaClmmState
from src.dex.solana.data_fetcher import MeteoraDlmmMetadata, RaydiumClmmMetadata, RaydiumHybridAmmMetadata, OrcaClmmMetadata
from src.dex.evm.data_fetcher.metadata.coingecko_fetcher import CoingeckoEvmFetcher
from src.logger_handler.logger import setup_logger, get_logger
from src.settings import config
from src.settings.graceful_shut_down import TerminateSignal, sigterm_handler
####################################

STATE_CLASSES = (
    OrcaClmmState,
    RaydiumClmmState,
    RaydiumAmmState,
    MeteoraDlmmState,
    UniswapV2StateFetcher,
    UniswapV3StateFetcher,
    UniswapV4StateFetcher,
)

METADATA_CLASSES = (
    MeteoraDlmmMetadata,
    RaydiumClmmMetadata,
    RaydiumHybridAmmMetadata,
    OrcaClmmMetadata,
    CoingeckoEvmFetcher
)

ProviderClass = Union[
    Type[OrcaClmmState],
    Type[RaydiumClmmState],
    Type[RaydiumAmmState],
    Type[MeteoraDlmmState],
    Type[UniswapV2StateFetcher],
    Type[UniswapV3StateFetcher],
    Type[UniswapV4StateFetcher],
    Type[MeteoraDlmmMetadata],
    Type[RaydiumClmmMetadata],
    Type[RaydiumHybridAmmMetadata],
    Type[OrcaClmmMetadata],
    Type[CoingeckoEvmFetcher],
]


async def _run_async_ctxmgr(provider_cls: ProviderClass, logger: logging.Logger):
    while True:
        try:
            async with provider_cls() as instance:
                await instance.main()
        except (KeyboardInterrupt, TerminateSignal):
            raise
        except Exception as e:
            logger.error(
                f"[{provider_cls.__name__}] Soft Crash: {e}. Restarting in 5s...",
                exc_info=True,
            )
            await asyncio.sleep(5)


async def _run_async(provider_cls: ProviderClass, logger: logging.Logger):
    while True:
        try:
            instance = provider_cls()
            await instance.main()
        except (KeyboardInterrupt, TerminateSignal):
            raise
        except Exception as e:
            logger.error(
                f"[{provider_cls.__name__}] Soft Crash: {e}. Restarting in 5s...",
                exc_info=True,
            )
            await asyncio.sleep(5)


def _run_sync(provider_cls: ProviderClass, logger: logging.Logger):
    while True:
        try:
            instance = provider_cls()
            instance.main()
        except (KeyboardInterrupt, TerminateSignal):
            raise
        except Exception as e:
            logger.error(
                f"[{provider_cls.__name__}] Soft Crash: {e}. Restarting in 5s...",
                exc_info=True,
            )
            time.sleep(5)


def bootstrap_worker(provider_cls: ProviderClass):
    signal.signal(signal.SIGTERM, sigterm_handler)

    worker_name = f"data_fetcher-{provider_cls.__name__}"
    log_file_path = os.path.join(config.SUPERVISOR_LOG_FOLDER, f"{worker_name}.log")

    setup_logger(logger_name=worker_name, log_file=log_file_path)
    local_logger = get_logger(logger_name=worker_name)

    local_logger.info(f"Worker process started. PID: {os.getpid()}")

    try:
        if issubclass(provider_cls, METADATA_CLASSES):
            asyncio.run(_run_async_ctxmgr(provider_cls, local_logger))
        elif issubclass(provider_cls, STATE_CLASSES):
            if asyncio.iscoroutinefunction(provider_cls.main):
                asyncio.run(_run_async(provider_cls, local_logger))
            else:
                _run_sync(provider_cls, local_logger)
        else:
            raise TypeError(
                f"Provider class {provider_cls.__name__} is not recognized in STATE or METADATA lists."
            )
    except (KeyboardInterrupt, TerminateSignal):
        local_logger.info("Worker received stop signal.")
    except Exception as e:
        local_logger.critical(f"Critical Worker Failure: {e}", exc_info=True)


def start_worker_process(provider_cls: ProviderClass, logger: logging.Logger, sector_name: str, worker_name: str):
    p = multiprocessing.Process(
        target=bootstrap_worker,
        args=(provider_cls,),
        name=f"{sector_name}-{worker_name}",
    )
    p.start()
    logger.info(f"Started {worker_name} (PID: {p.pid})")
    return p


def RUN_DATA_FETCHERS(targets: dict[str, ProviderClass], logger_name: str, logger_file: str, sector_name):
    signal.signal(signal.SIGTERM, sigterm_handler)

    setup_logger(logger_name=logger_name,
                 log_file=os.path.join(config.SUPERVISOR_LOG_FOLDER, logger_file))
    logger = get_logger(logger_name=logger_name)
    logger.info(f'{logger_name} Supervisor started.')

    start_method = multiprocessing.get_start_method()
    if start_method != 'spawn':
        logger.critical(f"Wrong start method: {start_method}. Must be 'spawn'. Exiting.")
        return

    processes = {}
    last_restart: dict[str, float] = {}
    MIN_RESTART_INTERVAL = 5.0

    for name, cls in targets.items():
        p = start_worker_process(cls, logger=logger, sector_name=sector_name, worker_name=name)
        processes[name] = p

    while True:
        try:
            time.sleep(5)

            for name, p in list(processes.items()):
                if not p.is_alive():
                    last = last_restart.get(name, 0.0)
                    elapsed = time.time() - last
                    if elapsed < MIN_RESTART_INTERVAL:
                        wait = MIN_RESTART_INTERVAL - elapsed
                        logger.warning(
                            f"{name} crashed within {elapsed:.1f}s; backing off {wait:.1f}s"
                        )
                        time.sleep(wait)

                    logger.warning(f"ALERT: {name} (PID {p.pid}) died unexpectedly! Restarting...")
                    p.join()
                    new_p = start_worker_process(targets[name],
                                                 logger=logger,
                                                 sector_name=sector_name,
                                                 worker_name=name)
                    processes[name] = new_p
                    last_restart[name] = time.time()

        except (KeyboardInterrupt, TerminateSignal):
            logger.info("Supervisor stopping... terminating workers.")
            for p in processes.values():
                p.terminate()

            for name, p in processes.items():
                p.join(timeout=10)

                if p.is_alive():
                    logger.warning(f"{name} didn't stop gracefully. Killing...")
                    p.kill()
                    p.join()

            logger.info("All workers stopped.")
            break

        except Exception as e:
            logger.critical(f"Critical Worker Failure: {e}", exc_info=True)


def RUN_STATE_FETCHERS():
    targets = {
        "MeteoraDLMM_state_fetcher": MeteoraDlmmState,
        "OrcaCLMM_state_fetcher": OrcaClmmState,
        "RaydiumCLMM_state_fetcher": RaydiumClmmState,
        "RaydiumHybrid_state_fetcher": RaydiumAmmState,
        "UniswapV2_state_fetcher": UniswapV2StateFetcher,
        "UniswapV3_state_fetcher": UniswapV3StateFetcher,
        "UniswapV4_state_fetcher": UniswapV4StateFetcher,
    }
    logger_name = "data_fetcher-State"
    logger_file = "data_fetcher-State.log"
    sector_name = "StateFetcher"

    RUN_DATA_FETCHERS(
        targets=targets,
        logger_name=logger_name,
        logger_file=logger_file,
        sector_name=sector_name,
    )

def RUN_METADATA_FETCHERS():
    targets = {
        "MeteoraDLMM_metadata_fetcher": MeteoraDlmmMetadata,
        "OrcaCLMM_metadata_fetcher": OrcaClmmMetadata,
        "RaydiumCLMM_metadata_fetcher": RaydiumClmmMetadata,
        "RaydiumHybrid_metadata_fetcher": RaydiumHybridAmmMetadata,
        "CoingeckoEvm_metadata_fetcher": CoingeckoEvmFetcher,
    }
    logger_name = "data_fetcher-Metadata"
    logger_file = "data_fetcher-Metadata.log"
    sector_name = "MetadataFetcher"
    RUN_DATA_FETCHERS(
        targets=targets,
        logger_name=logger_name,
        logger_file=logger_file,
        sector_name=sector_name,
    )