import redis
import json
import networkx as nx
import time
import logging
import math

####################################
from src.Config import config, BasicSchemeAndTypeDict
from src.CEX.contract_address_cex_checker.service.lookup import lookup_mint
from src.CEX.CEXAPI import get_exchange_asks, get_exchange_bids
####################################

def create_graph(metadata: dict, state: dict) -> nx.Graph:
    G = nx.Graph()
    for pool, data in state.items():
        if pool not in metadata: continue

        mint0 = metadata.get(pool).get('mint0')
        mint1 = metadata.get(pool).get('mint1')
        if G.has_edge(mint0, mint1):
            G[mint0][mint1]['pools'].append(pool)
        else:
            G.add_edge(mint0, mint1, pools=[pool])

    return G

def get_active_metadata(redis_connection: redis.Redis, logger: logging.Logger = None) -> dict:
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

def get_active_state(redis_connection: redis.Redis, logger: logging.Logger = None) -> dict:
    if logger is None:
        logger = logging.getLogger(__name__)

    all_state = {}
    current_time = int(time.time())

    for active_market in config.ACTIVE_MARKETS:
        try:
            market, version = config.MARKETS.get(active_market).values()
            raw = redis_connection.get(config.POOLS_CURRENT_STATE_DICT_REDIS_KEY % (market, version))

            if not isinstance(raw, str):
                logger.warning(f"Pool state for {active_market} market {version} is not a string.")
                continue

            state = BasicSchemeAndTypeDict.PoolStateScheme(**json.loads(raw))

            if abs(current_time - state.ts) > config.POOL_STATE_DECAY_TIME:
                logger.warning(f"WARNING pool state for {active_market} market {version} is not fresh.")
                continue

            all_state |= state.pool_state
        except Exception as e:
            logger.error(f"Error occurred while processing pool state for {active_market}: {e}")

    return all_state

def get_all_DEX_active_tokens(redis_connection: redis.Redis, logger: logging.Logger = None) -> dict:
    if not logger:
        logger = logging.getLogger(__name__)

    metadata = get_active_metadata(redis_connection)
    state = get_active_state(redis_connection, logger=logger)

    mapped_tokens = {}
    for pool, data in metadata.items():
        if not state.get(pool): continue

        mint0 = data.get('mint0')
        mint1 = data.get('mint1')
        decimals0 = data.get('decimals0')
        decimals1 = data.get('decimals1')
        token0 = data.get('token0')
        token1 = data.get('token1')

        if not mint0 or not mint1 or not decimals0 or not decimals1 or not token0 or not token1:
            continue

        if mint0 not in mapped_tokens:
            mapped_tokens[mint0] = {
                'decimals': decimals0,
                'symbol': token0
            }
        if mint1 not in mapped_tokens:
            mapped_tokens[mint1] = {
                'decimals': decimals1,
                'symbol': token1
            }

    return mapped_tokens

def get_all_common_list_of_tokens(redis_connection: redis.Redis, logger: logging.Logger = None) -> list:
    common_tokens = []

    dex_tokens = get_all_DEX_active_tokens(redis_connection, logger=logger)

    for mint, data in dex_tokens.items():
        try:
            is_token_in_cex = lookup_mint(mint)
            if is_token_in_cex:
                common_tokens.append(mint)
        except Exception as e:
            logger.error(f"Failed to get common tokens for {mint}: {e}")


    return common_tokens

def get_all_common_dict_of_tokens(redis_connection: redis.Redis, logger: logging.Logger = None) -> dict:
    common_tokens = {}

    dex_tokens = get_all_DEX_active_tokens(redis_connection, logger=logger)
    for mint, data in dex_tokens.items():
        try:
            is_token_in_cex = lookup_mint(mint)
            if is_token_in_cex:
                common_tokens[mint] = data
        except Exception as e:
            logger.error(f"Failed to get common tokens for {mint}: {e}")

    return common_tokens

def break_tasks_in_chunks(worker_number, task_list: list):
    num_symbols = len(task_list)
    chunk_size = math.ceil(num_symbols / worker_number)
    if chunk_size == 0:
        return

    for i in range(0, num_symbols, chunk_size):
        yield task_list[i:i + chunk_size]

async def get_orderbook(exchange: str, symbol: str, mode: str) -> list[list[float]]:
    if mode == 'CEX->DEX':
        orderbook = await get_exchange_asks(exchange=exchange, symbol=symbol)
    elif mode == 'DEX->CEX':
        orderbook = await get_exchange_bids(exchange=exchange, symbol=symbol)
    else:
        raise ValueError(f'Invalid mode: {mode}')

    if orderbook is None:
        raise Exception(f'Failed to get orderbook for {exchange} {symbol} {mode}')

    return orderbook