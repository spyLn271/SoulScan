import redis
import json
import networkx as nx
import time
import logging

####################################
from src.settings import config, basic_schemes
from src.settings.config import ACTIVE_NETWORK_MARKETS, MARKETS
from src.settings.config import Network
####################################

def create_graph(
        metadata: dict,
        state: dict
) -> nx.Graph:
    G = nx.Graph()
    for pool, data in state.items():
        if pool not in metadata: continue

        a = metadata.get(pool, {}).get('mint0')
        b = metadata.get(pool, {}).get('mint1')

        if G.has_edge(a, b):
            G[a][b]['pools'].append(pool)
        else:
            G.add_edge(a, b, pools=[pool])

    return G

def get_network_active_metadata(
        network: Network,
        redis_connection: redis.Redis,
        logger: logging.Logger = None
) -> dict:
    if logger is None:
        logger = logging.getLogger(__name__)

    all_metadata = {}
    for market in ACTIVE_NETWORK_MARKETS.get(network):
        try:
            market, version, _network = MARKETS.get(market).values()
            raw = redis_connection.get(config.REDIS_METADATA_KEY % (network, market, version))
            if not isinstance(raw, str):
                logger.warning(f'Pool metadata for market {market} version {version} not a string')
                continue
            metadata = json.loads(raw)
            all_metadata |= metadata

        except Exception as e:
            logger.error(f"Failed to get metadata for {market}: {e}", exc_info=True)

    return all_metadata


def get_network_active_state(
        network: Network,
        redis_connection: redis.Redis,
        logger: logging.Logger = None
) -> dict:
    _config = config.get_config()

    if logger is None:
        logger = logging.getLogger(__name__)

    all_state = {}

    for market in ACTIVE_NETWORK_MARKETS.get(network):
        try:
            current_ts = int(time.time())

            market, version, _network = MARKETS.get(market).values()

            if (market == "uniswap" or market == "pancakeswap" or market == "sushiswap") and (version == "v3" or version == "v4"):
                raw_slot = redis_connection.hget(
                    name=config.POOLS_STATE_DICT_REDIS_KEY % (network, market, version),
                    key=config.ENV_CLMM_SLOT_KEY
                )
                raw_ticks = redis_connection.hget(
                    name=config.POOLS_STATE_DICT_REDIS_KEY % (network, market, version),
                    key=config.ENV_CLMM_TICKS_KEY
                )

                if raw_slot and raw_ticks:
                    slot_state = json.loads(raw_slot)
                    ticks_state = json.loads(raw_ticks)

                    slots_data = slot_state["pool_state"]
                    ticks_data = ticks_state["pool_state"]

                    ts_slot = slot_state["ts"]
                    ts_ticks = ticks_state["ts"]

                    if current_ts - ts_ticks > _config.POOL_STATE_DECAY_TIME:
                        logger.warning(f"Ticks for {market} version {version} are too old, network {network}")
                        continue
                    elif current_ts - ts_slot > _config.POOL_STATE_DECAY_TIME:
                        logger.warning(f"Slot for {market} version {version} is too old, network {network}")
                        continue

                    state = {}
                    for pool, slot_data in slots_data.items():
                        ticks = ticks_data.get(pool)

                        if not ticks:
                            logger.warning(f"No ticks for {pool} in {market} version {version}, network {network}")
                            continue

                        state[pool] = {
                            "slot": slot_data,
                            "ticks": ticks
                        }

                    all_state |= state
                else:
                    logger.warning(f"No state for {market} version {version}, network {network}")

                continue

            raw = redis_connection.get(config.POOLS_STATE_DICT_REDIS_KEY % (network, market, version))
            if not isinstance(raw, str):
                logger.warning(f'Pool state for market {market} version {version} not a string')
                continue

            state = json.loads(raw)

            if current_ts - state["ts"] > _config.POOL_STATE_DECAY_TIME:
                logger.warning(f"State for {market} version {version} is too old, network {network}")
                continue

            all_state |= state["pool_state"]

        except Exception as e:
            logger.error(f"Failed to get state for {market}: {e}", exc_info=True)
            continue


    return all_state