#!/usr/bin/env python3
"""
Universal Redis Stream Watcher Function
For consuming orderbook data from various cryptocurrency exchanges
"""

import asyncio
import json
import redis.asyncio as redis
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Union, List, Tuple

from src.logger_handler.logger import get_logger

# Supported exchanges and their market types
SUPPORTED_EXCHANGES = {
    'bybit': ['spot', 'futures'],
    'okx': ['spot', 'futures'],
    'kucoin': ['spot', 'futures'],
    'gateio': ['spot', 'futures'],
    'mexc': ['spot'],
    'bingx': ['spot'],
    'bitget': ['spot'],
    'bitmart': ['spot'],
    'coinex': ['spot'],
    'htx': ['spot'],
    'lbank': ['spot']
}


from src.settings import cex_config as _sscfg


class StreamWatcher:
    """Universal stream watcher for cryptocurrency exchange orderbook data."""

    def __init__(self, redis_host: str = None, redis_port: int = None,
                 redis_db: int = 0):
        redis_host = redis_host if redis_host is not None else _sscfg.REDIS_HOST
        redis_port = redis_port if redis_port is not None else _sscfg.REDIS_PORT
        """
        Initialize the stream watcher

        Args:
            redis_host: Redis server hostname
            redis_port: Redis server port
            redis_db: Redis database number
        """
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.redis_client = None
        self.logger = get_logger("cex-StreamWatcher")

    async def connect(self):
        """Connect to Redis server"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True
            )
            await self.redis_client.ping()
            self.logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            return False

    async def disconnect(self):
        """Disconnect from Redis server"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

    def _build_stream_key(self, exchange: str, market_type: str, symbol: str) -> str:
        """
        Build Redis stream key based on exchange, market type, and symbol

        Args:
            exchange: Exchange name (e.g., 'bybit', 'okx')
            market_type: Market type ('spot' or 'futures')
            symbol: Trading symbol (e.g., 'BTC-USDT')

        Returns:
            Redis stream key string
        """
        return f"stream:orderbook:{exchange.lower()}:{market_type.lower()}:{symbol.upper()}"

    def _validate_params(self, exchange: str, market_type: str) -> bool:
        """
        Validate exchange and market type parameters

        Args:
            exchange: Exchange name
            market_type: Market type

        Returns:
            True if valid, False otherwise
        """
        exchange = exchange.lower()
        market_type = market_type.lower()

        if exchange not in SUPPORTED_EXCHANGES:
            self.logger.error(f"Unsupported exchange: {exchange}")
            self.logger.info(f"Supported exchanges: {list(SUPPORTED_EXCHANGES.keys())}")
            return False

        if market_type not in SUPPORTED_EXCHANGES[exchange]:
            self.logger.error(f"Exchange {exchange} does not support {market_type} markets")
            self.logger.info(f"Supported markets for {exchange}: {SUPPORTED_EXCHANGES[exchange]}")
            return False

        return True

    def _parse_orderbook_data(self, data: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Parse orderbook data from Redis stream

        Args:
            data: Raw data from Redis stream

        Returns:
            Parsed orderbook data or None if parsing fails
        """
        try:
            parsed_data = {
                'timestamp_ms': int(data.get('timestamp_ms', 0)),
                'symbol': data.get('symbol', ''),
                'bids': json.loads(data.get('bids', '[]')),
                'asks': json.loads(data.get('asks', '[]'))
            }

            # Add datetime object for convenience
            if parsed_data['timestamp_ms']:
                parsed_data['datetime'] = datetime.fromtimestamp(parsed_data['timestamp_ms'] / 1000)

            return parsed_data

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self.logger.error(f"Failed to parse orderbook data: {e}")
            self.logger.debug(f"Raw data: {data}")
            return None

    async def get_latest_orderbook(self, exchange: str, market_type: str,
                                   symbol: str, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """
        Get the latest orderbook data from Redis stream

        Args:
            exchange: Exchange name (e.g., 'bybit', 'okx')
            market_type: Market type ('spot' or 'futures')
            symbol: Trading symbol (e.g., 'BTC-USDT')
            timeout: Maximum time to wait for data in seconds

        Returns:
            Latest orderbook data dictionary or None if not available
        """
        if not self._validate_params(exchange, market_type):
            return None

        if not self.redis_client:
            if not await self.connect():
                return None

        stream_key = self._build_stream_key(exchange, market_type, symbol)

        try:
            messages = await asyncio.wait_for(
                self.redis_client.xrevrange(stream_key, count=1),
                timeout=timeout,
            )

            if not messages:
                self.logger.warning(f"No data found in stream: {stream_key}")
                return None

            # Extract the latest message
            message_id, data = messages[0]
            parsed_data = self._parse_orderbook_data(data)

            if parsed_data:
                parsed_data['stream_key'] = stream_key
                parsed_data['message_id'] = message_id
                parsed_data['exchange'] = exchange.lower()
                parsed_data['market_type'] = market_type.lower()

            return parsed_data

        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout waiting for data from stream: {stream_key}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading from stream {stream_key}: {e}")
            return None

    async def watch_stream(self, exchange: str, market_type: str, symbol: str,
                           callback: Callable[[Dict[str, Any]], None],
                           start_from_latest: bool = True) -> None:
        """
        Continuously watch a Redis stream and call callback for new messages

        Args:
            exchange: Exchange name (e.g., 'bybit', 'okx')
            market_type: Market type ('spot' or 'futures')
            symbol: Trading symbol (e.g., 'BTC-USDT')
            callback: Function to call with each new orderbook update
            start_from_latest: If True, start from latest message, else from beginning
        """
        if not self._validate_params(exchange, market_type):
            return

        if not self.redis_client:
            if not await self.connect():
                return

        stream_key = self._build_stream_key(exchange, market_type, symbol)
        last_id = '$' if start_from_latest else '0'

        self.logger.info(f"Starting to watch stream: {stream_key}")

        while True:
            try:
                # Read from stream, blocking until new messages arrive
                response = await self.redis_client.xread(
                    {stream_key: last_id},
                    count=100,
                    block=0  # Block indefinitely
                )

                if not response:
                    continue

                # Process each message
                messages = response[0][1]
                for message_id, data in messages:
                    parsed_data = self._parse_orderbook_data(data)

                    if parsed_data:
                        parsed_data['stream_key'] = stream_key
                        parsed_data['message_id'] = message_id
                        parsed_data['exchange'] = exchange.lower()
                        parsed_data['market_type'] = market_type.lower()

                        # Call the callback function
                        await callback(parsed_data) if asyncio.iscoroutinefunction(callback) else callback(parsed_data)

                    # Update last_id to continue from this point
                    last_id = message_id

            except redis.exceptions.ConnectionError as e:
                self.logger.error(f"Redis connection lost: {e}")
                self.logger.info("Attempting to reconnect in 5 seconds...")
                await asyncio.sleep(5)
                if not await self.connect():
                    break
            except Exception as e:
                self.logger.error(f"Unexpected error while watching stream: {e}")
                break

    async def list_active_streams(self) -> Dict[str, List[str]]:
        """
        List all active orderbook streams in Redis

        Returns:
            Dictionary mapping exchanges to their active streams
        """
        if not self.redis_client:
            if not await self.connect():
                return {}

        try:
            # Get all keys matching the orderbook stream pattern
            pattern = "stream:orderbook:*"
            keys = await self.redis_client.keys(pattern)

            streams_by_exchange = {}

            for key in keys:
                # Parse the key: stream:orderbook:exchange:market_type:symbol
                parts = key.split(':')
                if len(parts) >= 5:
                    exchange = parts[2]
                    market_type = parts[3]
                    symbol = parts[4]

                    if exchange not in streams_by_exchange:
                        streams_by_exchange[exchange] = []

                    streams_by_exchange[exchange].append(f"{market_type}:{symbol}")

            return streams_by_exchange

        except Exception as e:
            self.logger.error(f"Error listing active streams: {e}")
            return {}


# Convenience functions for direct use
async def get_latest_orderbook(exchange: str, market_type: str, symbol: str,
                               redis_host: str = "localhost", redis_port: int = 6379) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get latest orderbook data

    Args:
        exchange: Exchange name (e.g., 'bybit', 'okx')
        market_type: Market type ('spot' or 'futures')
        symbol: Trading symbol (e.g., 'BTC-USDT')
        redis_host: Redis server hostname
        redis_port: Redis server port

    Returns:
        Latest orderbook data dictionary or None
    """
    watcher = StreamWatcher(redis_host, redis_port)
    try:
        return await watcher.get_latest_orderbook(exchange, market_type, symbol)
    finally:
        await watcher.disconnect()


async def watch_orderbook_stream(exchange: str, market_type: str, symbol: str,
                                 callback: Callable[[Dict[str, Any]], None],
                                 redis_host: str = "localhost", redis_port: int = 6379,
                                 start_from_latest: bool = True) -> None:
    """
    Convenience function to watch orderbook stream

    Args:
        exchange: Exchange name (e.g., 'bybit', 'okx')
        market_type: Market type ('spot' or 'futures')
        symbol: Trading symbol (e.g., 'BTC-USDT')
        callback: Function to call with each new orderbook update
        redis_host: Redis server hostname
        redis_port: Redis server port
        start_from_latest: If True, start from latest message
    """
    watcher = StreamWatcher(redis_host, redis_port)
    try:
        await watcher.watch_stream(exchange, market_type, symbol, callback, start_from_latest)
    finally:
        await watcher.disconnect()