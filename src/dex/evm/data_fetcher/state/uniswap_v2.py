import redis
import time
import json
import logging
import asyncio
import signal

####################################
from src.settings.graceful_shut_down import sigterm_handler
from src.settings.basic_schemes import PoolState
from src.dex.evm.data_fetcher.state.fetcher_skeleton import FetcherSkeleton
from src.dex.evm.uniswap.v2 import UniswapV2
from src.dex.evm.type_dict import MetadataDict
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


def save_pool_state(
        pool_state: PoolState,
        network: Network,
        version: Version,
        dex: DEX,
        logger: logging.Logger,
        redis_con: redis.Redis
):
    logger.info(f"Saving pool state for {network} {dex} {version}...")

    if not pool_state["pool_state"]:
        logger.info(f"No pool states to save for {network} {dex} {version}")
        return

    try:
        redis_con.set(POOLS_STATE_DICT_REDIS_KEY % (network, dex, version), json.dumps(pool_state))
        logger.info(f"Saved {len(pool_state['pool_state'])} pool states for {network} {dex} {version}")
    except Exception as e:
        logger.error(f"Error saving pool state for {network} {dex} {version}: {e}", exc_info=True)


async def uniswap_v2_network_fetcher(network: Network):
    setup_logger(
        log_file=EVM_FETCHER_LOG_FILE,
        logger_name=f"uniswap_v2_{network}_fetcher"
    )

    logger = get_logger(f"uniswap_v2_{network}_fetcher")

    logger.info(f"Starting Uniswap V2 network fetcher for {network}...")


    _config = get_config()

    redis_con = redis.Redis(
        host=_config.REDIS.HOST,
        port=_config.REDIS.PORT,
        decode_responses=True
    )

    metadata: dict[str, MetadataDict] = get_metadata(
        network=network,
        dex="uniswap",
        version="v2",
        redis_con=redis_con,
        logger=logger
    )
    metadata_fetched_time = int(time.time())
    logger.info(f"Initial metadata loaded for {network} v2: {len(metadata)} pools")

    async with UniswapV2(network=network, dex="uniswap") as uniV2:
        logger.info(f"Entering V2 fetch loop for {network}")
        while True:
            try:
                if int(time.time()) - metadata_fetched_time > _config.METADATA_DECAY_PERIOD:
                    logger.info(f"Metadata decay period elapsed for {network} v2; refreshing")
                    metadata = get_metadata(
                        network=network,
                        dex="uniswap",
                        version="v2",
                        redis_con=redis_con,
                        logger=logger
                    )
                    metadata_fetched_time = int(time.time())
                    logger.info(f"Metadata refreshed for {network} v2: {len(metadata)} pools")

                pool_state = await uniV2.fetch_reserves(list(metadata.keys()))

                save_pool_state(
                    pool_state=PoolState(
                        pool_state=pool_state,
                        ts=int(time.time())
                    ),
                    network=network,
                    version="v2",
                    dex="uniswap",
                    logger=logger,
                    redis_con=redis_con
                )

            except Exception as e:
                logger.error(f"Error occurred while fetching: {e}", exc_info=True)


            finally:
                await asyncio.sleep(0.5)


def uniswap_v3_bootstrap_worker(network: Network):
    signal.signal(signal.SIGTERM, sigterm_handler)
    asyncio.run(uniswap_v2_network_fetcher(network=network))




class UniswapV2StateFetcher(FetcherSkeleton):
    def __init__(self):
        setup_logger(
            log_file=EVM_SKELETON_LOG_FILE,
            logger_name="uniswap_v2_state_fetcher"
        )

        super().__init__(
            logger=get_logger("uniswap_v2_state_fetcher"),
            dex="uniswap",
            version="v2",
            func=uniswap_v3_bootstrap_worker
        )