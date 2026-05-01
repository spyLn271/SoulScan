import redis
import json
import networkx as nx
import time
import logging

####################################
from src.settings import config, basic_schemes
####################################

def create_graph(
        metadata: dict,
        state: dict
) -> nx.Graph:
    G = nx.Graph()
    for pool, data in state.items():
        if pool not in metadata: continue

        a = metadata.get(pool, {}).get('mint0') or metadata.get(pool, {}).get('addr0')
        b = metadata.get(pool, {}).get('mint1') or metadata.get(pool, {}).get('addr1')

        if G.has_edge(a, b):
            G[a][b]['pools'].append(pool)
        else:
            G.add_edge(a, b, pools=[pool])

    return G

def get_active_metadata(
        redis_connection: redis.Redis,
        logger: logging.Logger = None
) -> dict:
    if logger is None:
        logger = logging.getLogger(__name__)

    all_metadata = {}
    for active_market in config.ACTIVE_MARKETS:
        try:

            market, version = config.MARKETS.get(active_market).values()
            raw = redis_connection.get(config.REDIS_METADATA_KEY % (market, version))

            if not isinstance(raw, str):
                logger.warning(f'Pool metadata fo market {market} version {version} not a string')
                continue

            metadata = json.loads(raw)
            all_metadata |= metadata

        except Exception as e:
            logger.error(f"Failed to get metadata for {active_market}: {e}")

    return all_metadata

def get_active_state(
        redis_connection: redis.Redis,
        logger: logging.Logger = None
) -> dict:
    if logger is None:
        logger = logging.getLogger(__name__)

    all_state = {}

    for active_market in config.ACTIVE_MARKETS:
        current_time = int(time.time())
        try:
            market, version = config.MARKETS.get(active_market).values()
            raw = redis_connection.get(config.POOLS_STATE_DICT_REDIS_KEY % (market, version))

            if not isinstance(raw, str):
                logger.warning(f"Pool state for {active_market} market {version} is not a string.")
                continue

            state = basic_schemes.PoolStateScheme(**json.loads(raw))

            if abs(current_time - state.ts) > config.POOL_STATE_DECAY_TIME:
                logger.warning(f"WARNING pool state for {active_market} market {version} is not fresh."
                               f" Current time: {current_time}, state time: {state.ts}, decay time: {config.POOL_STATE_DECAY_TIME}"
                               f" Difference: {abs(current_time - state.ts)}")
                continue

            all_state |= state.pool_state
        except Exception as e:
            logger.error(f"Error occurred while processing pool state for {active_market}: {e}")

    return all_state