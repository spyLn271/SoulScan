import asyncio
import json
import redis.asyncio as redis
from typing import Dict, List, Optional
import logging

from src.CEX.stream_watcher_function import SUPPORTED_EXCHANGES

class OrderbookAggregator:
    """
    High-performance orderbook aggregator that fetches data from all exchanges concurrently
    P.S DO NOT FORGET TO CHANGE PORT TO DEFAULT
    """

    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0):
        """
        Initialize the aggregator

        Args:
            redis_host: Redis server hostname
            redis_port: Redis server port
            redis_db: Redis database number
        """
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.redis_client = None

    async def _ensure_connection(self):
        """Ensure Redis connection is established"""
        if not self.redis_client:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_keepalive=True
            )
            await self.redis_client.ping()

    def _build_stream_key(self, exchange: str, market_type: str, symbol: str) -> str:
        return f"stream:orderbook:{exchange.lower()}:{market_type.lower()}:{symbol.upper()}"

    def _parse_orderbook_data(self, data: Dict[str, str]) -> Optional[Dict[str, any]]:
        """Parse orderbook data from Redis stream"""
        try:
            return {
                'timestamp_ms': int(data.get('timestamp_ms', 0)),
                'symbol': data.get('symbol', ''),
                'bids': json.loads(data.get('bids', '[]')),
                'asks': json.loads(data.get('asks', '[]'))
            }
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logging.error(f"Failed to parse orderbook data: {e}")
            return None

    async def _get_exchange_orderbook(self, exchange: str, symbol: str) -> Optional[Dict[str, any]]:
        """Get orderbook data for a single exchange"""
        try:
            # Try both spot and futures markets for exchanges that support both
            market_types = SUPPORTED_EXCHANGES.get(exchange, [])

            for market_type in market_types:
                stream_key = self._build_stream_key(exchange, market_type, symbol)

                try:
                    # Get latest message from stream
                    messages = await self.redis_client.xrevrange(stream_key, count=1)

                    if messages:
                        message_id, data = messages[0]
                        parsed_data = self._parse_orderbook_data(data)

                        if parsed_data and (parsed_data['bids'] or parsed_data['asks']):
                            parsed_data.update({
                                'exchange': exchange,
                                'market_type': market_type,
                                'stream_key': stream_key
                            })
                            return parsed_data

                except Exception as e:
                    logging.debug(f"No data in {stream_key}: {e}")
                    continue

            return None

        except Exception as e:
            logging.error(f"Error fetching orderbook for {exchange}: {e}")
            return None

    async def get_all_orderbooks(self, symbol: str) -> Dict[str, Dict[str, any]]:
        """
        Get orderbook data from all exchanges concurrently

        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')

        Returns:
            Dictionary with exchange names as keys and orderbook data as values
        """
        await self._ensure_connection()

        # Create tasks for all exchanges
        tasks = []
        for exchange in SUPPORTED_EXCHANGES.keys():
            task = asyncio.create_task(self._get_exchange_orderbook(exchange, symbol))
            tasks.append((exchange, task))

        # Collect results
        results = {}
        for exchange, task in tasks:
            try:
                orderbook_data = await task
                if orderbook_data:
                    results[exchange] = orderbook_data
            except Exception as e:
                logging.error(f"Task failed for {exchange}: {e}")

        return results

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None


_aggregator = None


async def _get_aggregator() -> OrderbookAggregator:
    global _aggregator
    if _aggregator is None:
        _aggregator = OrderbookAggregator()
    return _aggregator


async def get_all_exchange_asks(symbol: str) -> Dict[str, List[List[float]]]:
    aggregator = await _get_aggregator()
    orderbooks = await aggregator.get_all_orderbooks(symbol)

    asks_data = {}
    for exchange, orderbook in orderbooks.items():
        if orderbook and orderbook.get('asks'):
            asks = orderbook['asks']
            if asks and isinstance(asks[0], (list, tuple)) and len(asks[0]) >= 2:
                asks_data[exchange] = [[float(ask[0]), float(ask[1])] for ask in asks]
                asks_data[exchange].sort(key=lambda x: x[0])  # Sort by price

    return asks_data


async def get_all_exchange_bids(symbol: str) -> Dict[str, List[List[float]]]:
    aggregator = await _get_aggregator()
    orderbooks = await aggregator.get_all_orderbooks(symbol)

    bids_data = {}
    for exchange, orderbook in orderbooks.items():
        if orderbook and orderbook.get('bids'):
            bids = orderbook['bids']
            if bids and isinstance(bids[0], (list, tuple)) and len(bids[0]) >= 2:
                bids_data[exchange] = [[float(bid[0]), float(bid[1])] for bid in bids]
                bids_data[exchange].sort(key=lambda x: x[0], reverse=True)  # Sort by price desc

    return bids_data


async def get_all_exchange_orderbooks(symbol: str) -> Dict[str, Dict[str, List[List[float]]]]:
    aggregator = await _get_aggregator()
    orderbooks = await aggregator.get_all_orderbooks(symbol)

    formatted_data = {}
    for exchange, orderbook in orderbooks.items():
        if orderbook:
            exchange_data = {}

            # Process bids
            if orderbook.get('bids'):
                bids = orderbook['bids']
                if bids and isinstance(bids[0], (list, tuple)) and len(bids[0]) >= 2:
                    exchange_data['bids'] = [[float(bid[0]), float(bid[1])] for bid in bids]
                    exchange_data['bids'].sort(key=lambda x: x[0], reverse=True)

            # Process asks
            if orderbook.get('asks'):
                asks = orderbook['asks']
                if asks and isinstance(asks[0], (list, tuple)) and len(asks[0]) >= 2:
                    exchange_data['asks'] = [[float(ask[0]), float(ask[1])] for ask in asks]
                    exchange_data['asks'].sort(key=lambda x: x[0])

            if exchange_data:
                formatted_data[exchange] = exchange_data

    return formatted_data


# ============================================================
# Single Exchange Functions
# ============================================================

async def get_exchange_asks(exchange: str, symbol: str) -> Optional[List[List[float]]]:
    """
    Get asks from a specific exchange.

    Args:
        exchange: Exchange name (e.g., 'binance', 'bybit')
        symbol: Trading symbol (e.g., 'BTCUSDT')

    Returns:
        List of [price, amount] sorted by price ascending, or None if not available
    """
    aggregator = await _get_aggregator()
    await aggregator._ensure_connection()

    orderbook = await aggregator._get_exchange_orderbook(exchange, symbol)

    if orderbook and orderbook.get('asks'):
        asks = orderbook['asks']
        if asks and isinstance(asks[0], (list, tuple)) and len(asks[0]) >= 2:
            result = [[float(ask[0]), float(ask[1])] for ask in asks]
            result.sort(key=lambda x: x[0])  # Sort by price ascending
            return result

    return None


async def get_exchange_bids(exchange: str, symbol: str) -> Optional[List[List[float]]]:
    """
    Get bids from a specific exchange.

    Args:
        exchange: Exchange name (e.g., 'binance', 'bybit')
        symbol: Trading symbol (e.g., 'BTCUSDT')

    Returns:
        List of [price, amount] sorted by price descending, or None if not available
    """
    aggregator = await _get_aggregator()
    await aggregator._ensure_connection()

    orderbook = await aggregator._get_exchange_orderbook(exchange, symbol)

    if orderbook and orderbook.get('bids'):
        bids = orderbook['bids']
        if bids and isinstance(bids[0], (list, tuple)) and len(bids[0]) >= 2:
            result = [[float(bid[0]), float(bid[1])] for bid in bids]
            result.sort(key=lambda x: x[0], reverse=True)  # Sort by price descending
            return result

    return None


async def get_exchange_orderbook(exchange: str, symbol: str) -> Optional[Dict[str, List[List[float]]]]:
    """
    Get full orderbook (bids and asks) from a specific exchange.

    Args:
        exchange: Exchange name (e.g., 'binance', 'bybit')
        symbol: Trading symbol (e.g., 'BTCUSDT')

    Returns:
        Dict with 'bids' and 'asks' keys, or None if not available
    """
    aggregator = await _get_aggregator()
    await aggregator._ensure_connection()

    orderbook = await aggregator._get_exchange_orderbook(exchange, symbol)

    if not orderbook:
        return None

    result = {}

    if orderbook.get('bids'):
        bids = orderbook['bids']
        if bids and isinstance(bids[0], (list, tuple)) and len(bids[0]) >= 2:
            result['bids'] = [[float(bid[0]), float(bid[1])] for bid in bids]
            result['bids'].sort(key=lambda x: x[0], reverse=True)

    if orderbook.get('asks'):
        asks = orderbook['asks']
        if asks and isinstance(asks[0], (list, tuple)) and len(asks[0]) >= 2:
            result['asks'] = [[float(ask[0]), float(ask[1])] for ask in asks]
            result['asks'].sort(key=lambda x: x[0])

    return result if result else None


# Cleanup function
async def cleanup_aggregator():
    global _aggregator
    try:
        if _aggregator:
            await _aggregator.close()
            _aggregator = None
    except Exception as e:
        logging.error(f"Cleanup failed for {_aggregator}: {e}")


