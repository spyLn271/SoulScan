import threading
from typing import Callable, Awaitable
import redis
import time
import json
import logging
import asyncio
import copy
import signal

####################################
from src.settings.basic_schemes import PoolState
from src.settings.graceful_shut_down import sigterm_handler
from src.dex.evm.data_fetcher.state.fetcher_skeleton import FetcherSkeleton
from src.dex.evm.uniswap.v3 import UniswapV3
from src.dex.evm.type_dict import SlotDict
from src.logger_handler.logger import setup_logger, get_logger
from src.dex.tools.helpers.evm.helper import get_metadata
from src.settings.config import (
    get_config,
    Network,
    DEX,
    Version,
    POOLS_STATE_DICT_REDIS_KEY,
    EVM_FETCHER_LOG_FILE,
    EVM_SKELETON_LOG_FILE,
)
####################################


_SLOT_DATA: dict[str, SlotDict] = {}

_lock = threading.Lock()

def get_slot_data() -> dict[str, SlotDict]:
    with _lock:
        return copy.deepcopy(_SLOT_DATA)

def set_slot_data(data: dict[str, SlotDict]) -> None:
    with _lock:
        global _SLOT_DATA
        _SLOT_DATA = data


NetworkFetcher = Callable[[Network], Awaitable[None]]
def async_booster(network: Network, func: NetworkFetcher):
    asyncio.run(func(network))


def save_pool_state(
        pool_state: PoolState,
        network: Network,
        version: Version,
        dex: DEX,
        field: str,
        logger: logging.Logger,
        redis_con: redis.Redis
):
    logger.info(f"Saving pool state for {network} {dex} {version}...")

    try:
        redis_con.hset(
            name=POOLS_STATE_DICT_REDIS_KEY % (network, dex, version),
            key=field,
            value=json.dumps(pool_state)
        )
        logger.info(f"Saved {len(pool_state['pool_state'])} pool states for {network} {dex} {version}, with a key: {field}.")
    except Exception as e:
        logger.error(f"Error saving pool state for {network} {dex} {version}: {e}", exc_info=True)


async def uniswap_v3_slot_fetcher(network: Network):
    _config = get_config()

    setup_logger(
        log_file=EVM_FETCHER_LOG_FILE,
        logger_name=f"uniswap_v3_{network}_fetcher",
    )

    logger = get_logger(f"uniswap_v3_{network}_fetcher")
    logger.info(f"Starting Uniswap V3 slot fetcher for {network}...")

    redis_con = redis.Redis(
        host=_config.REDIS.HOST,
        port=_config.REDIS.PORT,
        decode_responses=True
    )

    metadata = get_metadata(
        network=network,
        dex="uniswap",
        version="v3",
        redis_con=redis_con,
        logger=logger
    )
    metadata_fetched_time = int(time.time())
    logger.info(f"[slot] initial metadata loaded for {network} v3: {len(metadata)} pools")

    async with UniswapV3(network=network, dex="uniswap") as univ3:
        logger.info(f"[slot] entering fetch loop for {network}")
        while True:
            try:
                if int(time.time()) - metadata_fetched_time > _config.METADATA_DECAY_PERIOD:
                    logger.info(f"[slot] metadata decay period elapsed for {network}; refreshing")
                    metadata = get_metadata(
                        network=network,
                        dex="uniswap",
                        version="v3",
                        redis_con=redis_con,
                        logger=logger
                    )
                    metadata_fetched_time = int(time.time())
                    logger.info(f"[slot] metadata refreshed for {network} v3: {len(metadata)} pools")


                slot_data = await univ3.fetch_slot0_data(metadata=metadata)
                set_slot_data(slot_data)

                save_pool_state(
                    pool_state=PoolState(
                        pool_state=slot_data,
                        ts=int(time.time())
                    ),
                    network=network,
                    version="v3",
                    dex="uniswap",
                    field="slot",
                    logger=logger,
                    redis_con=redis_con
                )

            except Exception as e:
                logger.error(f"Error occurred while fetching slot data: {e}", exc_info=True)


            finally:
                await asyncio.sleep(0.1)


async def uniswap_v3_tick_fetcher(network: Network):
    _config = get_config()

    setup_logger(
        log_file=EVM_FETCHER_LOG_FILE,
        logger_name=f"uniswap_v3_{network}_fetcher",
    )

    logger = get_logger(f"uniswap_v3_{network}_fetcher")
    logger.info(f"Starting Uniswap V3 tick fetcher for {network}...")

    redis_con = redis.Redis(
        host=_config.REDIS.HOST,
        port=_config.REDIS.PORT,
        decode_responses=True
    )

    logger.info(f"[ticks] waiting for first slot data for {network}...")
    while not get_slot_data():
        await asyncio.sleep(0.1)
    logger.info(f"[ticks] slot data ready for {network}; continuing")

    metadata = get_metadata(
        network=network,
        dex="uniswap",
        version="v3",
        redis_con=redis_con,
        logger=logger
    )
    metadata_fetched_time = int(time.time())
    logger.info(f"[ticks] initial metadata loaded for {network} v3: {len(metadata)} pools")

    async with UniswapV3(network=network, dex="uniswap") as univ3:
        logger.info(f"[ticks] entering fetch loop for {network}")
        while True:
            try:
                if int(time.time()) - metadata_fetched_time > _config.METADATA_DECAY_PERIOD:
                    logger.info(f"[ticks] metadata decay period elapsed for {network}; refreshing")
                    metadata = get_metadata(
                        network=network,
                        dex="uniswap",
                        version="v3",
                        redis_con=redis_con,
                        logger=logger
                    )
                    metadata_fetched_time = int(time.time())
                    logger.info(f"[ticks] metadata refreshed for {network} v3: {len(metadata)} pools")

                slot_data = get_slot_data()

                ticks_liq = await univ3.fetch_ticks_liquidity(
                    metadata=metadata,
                    slot0_data=slot_data
                )

                save_pool_state(
                    pool_state=PoolState(
                        pool_state=ticks_liq,
                        ts=int(time.time())
                    ),
                    network=network,
                    version="v3",
                    dex="uniswap",
                    field="ticks",
                    logger=logger,
                    redis_con=redis_con
                )

            except Exception as e:
                logger.error(f"Error occurred while fetching ticks liquidity: {e}", exc_info=True)


def uniswap_v3_fetcher(network: Network):
    signal.signal(signal.SIGTERM, sigterm_handler)

    setup_logger(
        log_file=EVM_FETCHER_LOG_FILE,
        logger_name=f"uniswap_v3_{network}_fetcher",
    )
    logger = get_logger(f"uniswap_v3_{network}_fetcher")
    logger.info(f"V3 bootstrap: spawning slot+ticks threads for {network}")

    slot_thread = threading.Thread(target=async_booster, args=(network, uniswap_v3_slot_fetcher), daemon=True)
    ticks_thread = threading.Thread(target=async_booster, args=(network, uniswap_v3_tick_fetcher), daemon=True)
    slot_thread.start()
    ticks_thread.start()
    logger.info(f"V3 bootstrap: threads started for {network} (slot TID: {slot_thread.ident}, ticks TID: {ticks_thread.ident})")

    while slot_thread.is_alive() and ticks_thread.is_alive():
        time.sleep(5)

    logger.error(
        f"V3 bootstrap: thread died for {network} "
        f"(slot alive={slot_thread.is_alive()}, ticks alive={ticks_thread.is_alive()}); raising to restart process"
    )
    raise RuntimeError(f"slot or ticks thread for {network} died; restarting process")


class UniswapV3StateFetcher(FetcherSkeleton):
    def __init__(self):
        setup_logger(
            log_file=EVM_SKELETON_LOG_FILE,
            logger_name="uniswap_v3_state_fetcher"
        )

        super().__init__(
            logger=get_logger("uniswap_v3_state_fetcher"),
            dex="uniswap",
            version="v3",
            func=uniswap_v3_fetcher
        )
