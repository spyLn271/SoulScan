import hashlib
from typing import Dict, Optional, Set, Tuple
import redis
import json
import networkx as nx
import time
import logging
import math

####################################
from src.Config import config, BasicSchemeAndTypeDict
from src.Config.config import MINIMAL_PROFIT
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

def break_dict_in_chunks(worker_number, dict_to_break: dict):
    items = list(dict_to_break.items())
    chunk_size = math.ceil(len(items) / worker_number)
    if chunk_size == 0:
        return
    for i in range(0, len(items), chunk_size):
        yield dict(items[i:i + chunk_size])

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

class CexDexSignalManager:
    CEX_DEX_OPPORTUNITIES_KEY = 'cex-dex-opportunities'
    CEX_DEX_EVENTS_KEY = 'cex-dex-events'

    STREAM_MAX_LEN = 1000

    def __init__(self, redis_client: redis.Redis, dex: str, network: str, logger: logging.Logger):
        self.redis_client = redis_client
        self.logger = logger
        self.dex = dex
        self.network = network
        self.active_signals: Dict[str, Tuple[str, float]] = {}

    def _create_composite_key(self, cex: str, mode: str, token_pair: str) -> str:
        return f"{self.dex}:{self.network}:{cex.upper()}:{mode}:{token_pair}"

    @staticmethod
    def _create_unique_id(composite_key: str, hash_suffix: str) -> str:
        return f"{composite_key}:{hash_suffix}"

    @staticmethod
    def _generate_short_hash(composite_key: str) -> str:
        return hashlib.md5(composite_key.encode()).hexdigest()[:4].upper()

    def _get_id(self, composite_key: str) -> str:
        if composite_key in self.active_signals:
            unique_id, _ = self.active_signals[composite_key]
            self.active_signals[composite_key] = (unique_id, time.time())
            return unique_id
        else:
            hash_suffix = self._generate_short_hash(composite_key)
            unique_id = self._create_unique_id(composite_key, hash_suffix)
            self.active_signals[composite_key] = (unique_id, time.time())
            self.logger.info(f"New CEX-DEX signal created: {unique_id}")
            return unique_id

    def _upsert_signal(self, unique_id: str, payload: dict) -> None:
        json_data = json.dumps(payload)

        self.redis_client.hset(self.CEX_DEX_OPPORTUNITIES_KEY, unique_id, json_data)

        self.redis_client.xadd(self.CEX_DEX_EVENTS_KEY, {
            'action': 'upsert',
            'unique_id': unique_id,
            'data': json_data
        }, maxlen=self.STREAM_MAX_LEN)

    def _remove_signal(self, unique_id: str) -> None:
        self.redis_client.hdel(self.CEX_DEX_OPPORTUNITIES_KEY, unique_id)

        self.redis_client.xadd(
            self.CEX_DEX_EVENTS_KEY,
            {
                'action': 'remove',
                'unique_id': unique_id,
                'data': ''
            },
            maxlen=self.STREAM_MAX_LEN,
        )

    def finalize_signal(
            self,
            cex: str,
            mode: str,
            base: str,
            quote: str,
            base_address: str,
            quote_address: str,
            best_swap: dict,
            order_number: int,
    ) -> Optional[str]:
        profit = best_swap.get('profit', 0)
        if profit < MINIMAL_PROFIT:
            return None

        token_pair = f"{base}{quote}"
        composite_key = self._create_composite_key(cex, mode, token_pair)
        unique_id = self._get_id(composite_key)

        payload = {
            'unique_id': unique_id,
            'timestamp': int(time.time()),
            'dex': self.dex,
            'network': self.network,
            'cex': cex.upper(),
            'mode': mode,
            'token_pair': token_pair,
            'profit': profit,
            'target_token': base,
            'target_address': base_address,
            'base_token': quote,
            'base_address': quote_address,
            'CEX_amountIn': best_swap.get('CEX_amountIn'),
            'CEX_amountOut': best_swap.get('CEX_amountOut'),
            'DEX_amountIn': best_swap.get('DEX_amountIn'),
            'DEX_amountOut': best_swap.get('DEX_amountOut'),
            'order_number': order_number,
            'CEX_start_price': best_swap.get('CEX_start_price'),
            'CEX_end_price': best_swap.get('CEX_end_price'),
        }

        self._upsert_signal(unique_id, payload)
        self.logger.debug(f"Upserted signal: {unique_id} profit={profit}")

        return composite_key

    def garbage_collect(self, current_keys: Set[str]) -> int:
        stale_count = 0

        for composite_key, (unique_id, _) in list(self.active_signals.items()):
            if composite_key not in current_keys:
                self._remove_signal(unique_id)
                del self.active_signals[composite_key]
                self.logger.info(f"Garbage collected: {unique_id}")
                stale_count += 1

        return stale_count

    def clear_all(self) -> int:
        count = self.redis_client.hlen(self.CEX_DEX_OPPORTUNITIES_KEY)
        if count > 0:
            self.redis_client.delete(self.CEX_DEX_OPPORTUNITIES_KEY)
            self.logger.info(f"Cleared {count} stale CEX-DEX signals")

        self.active_signals.clear()

        return count

    def get_active_count(self) -> int:
        return len(self.active_signals)

    def get_redis_count(self) -> int:
        return self.redis_client.hlen(self.CEX_DEX_OPPORTUNITIES_KEY)