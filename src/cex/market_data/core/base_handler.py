#!/usr/bin/env python3
"""
Base Market Data Handler - Abstract base class for exchange market data fetchers

Eliminates code duplication by providing common functionality:
- Redis connection management
- Update loop with timing
- Error handling
- Configuration management
"""

# Fix Python path for imports
import sys
import os

import time
import redis
import json
import requests
import logging
import signal
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.cex.market_data.config import REDIS_CONFIG
from src.settings import cex_config as _sscfg
from src.logger_handler.logger import setup_logger, get_logger


# ============================================================================
# Shared Redis Connection Pool (Singleton)
# ============================================================================
# All handlers share this pool instead of creating individual connections.
# This reduces connection count from ~40 (one per handler) to a shared pool.

_redis_pool = None


def get_shared_redis_pool():
    """
    Get the shared Redis connection pool.
    Creates the pool on first call (lazy initialization).
    """
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool(
            host=REDIS_CONFIG['host'],
            port=REDIS_CONFIG['port'],
            db=REDIS_CONFIG.get('db', 0),
            password=REDIS_CONFIG.get('password'),
            decode_responses=REDIS_CONFIG.get('decode_responses', True),
            max_connections=50  # Shared pool for all ~40 handlers
        )
    return _redis_pool


class BaseMarketDataHandler(ABC):
    """
    Abstract base class for exchange market data handlers
    Provides common functionality and defines interface for exchange-specific implementations
    """

    def __init__(self, exchange_name: str, market_type: str):
        self.exchange_name = exchange_name
        self.market_type = market_type

        # Will be set by child classes
        self.api_endpoint = None
        self.redis_key = None
        self.update_interval = 5

        # Redis client
        self.redis_client = None

        # Shutdown handling
        self.shutdown_requested = False

        # Setup logging
        self.logger = self._setup_logging()

        # Setup signal handlers
        self._setup_signal_handlers()

        self.logger.info(f"Initialized {exchange_name} {market_type} market data handler")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for this handler via SoulScan's unified logger."""
        logger_name = f"MarketData-{self.exchange_name}_{self.market_type}"
        log_file = os.path.join(_sscfg.CEX_MARKET_DATA_LOG_FOLDER, f"{logger_name}.log")
        os.makedirs(_sscfg.CEX_MARKET_DATA_LOG_FOLDER, exist_ok=True)
        setup_logger(logger_name=logger_name, log_file=log_file)
        return get_logger(logger_name)

    def _setup_signal_handlers(self):
        """Per-handler signals are a no-op under the supervisor — the manager
        owns process-level signal handling and toggles `shutdown_requested`
        via stop_all_plugins(). Installing here would clobber sibling handlers'
        signal handlers (last-write-wins) and break under threads anyway
        (signal.signal only works on the main thread)."""
        if threading.current_thread() is not threading.main_thread():
            return
        # Standalone-only path: still register so a lone handler can Ctrl-C.
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating immediate shutdown...")
            self.shutdown_requested = True

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def initialize(self):
        """Initialize the handler - setup Redis connection using shared pool"""
        try:
            # Use shared connection pool instead of creating individual connections
            self.redis_client = redis.Redis(connection_pool=get_shared_redis_pool())
            self.redis_client.ping()
            self.logger.info(f"Successfully connected to Redis at {REDIS_CONFIG['host']}:{REDIS_CONFIG['port']} (shared pool)")
            return True
        except redis.ConnectionError as e:
            self.logger.error(f"Could not connect to Redis: {e}")
            return False

    def get_decimal_places(self, number_string: str) -> int:
        """Calculate number of decimal places in a string representation of a number"""
        if not isinstance(number_string, str) or '.' not in number_string:
            return 0
        return len(number_string.split('.')[-1])

    def update_redis_data(self):
        """
        Main update method - fetches data from API and stores in Redis.
        One retry with 0.5s backoff absorbs transient network blips that would
        otherwise spam the log on every flap.
        """
        try:
            self.logger.debug(f"Fetching data from {self.api_endpoint}")
            try:
                response = requests.get(self.api_endpoint, timeout=10)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"API request failed ({e}); retrying once after 0.5s")
                time.sleep(0.5)
                response = requests.get(self.api_endpoint, timeout=10)
                response.raise_for_status()

            parsed_data = self.parse_api_response(response.json())
            if not parsed_data:
                self.logger.warning("No data returned from API")
                return False

            count = self._store_data_in_redis(parsed_data)
            self.logger.info(f"Successfully updated {count} {self.market_type} symbols in Redis")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch data from API after retry: {e}")
            return False
        except json.JSONDecodeError:
            self.logger.error("Failed to decode idl from API response")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during update: {e}")
            return False

    def _store_data_in_redis(self, parsed_data: List[Dict[str, Any]]) -> int:
        """Store processed data in Redis using pipeline for efficiency"""
        if not parsed_data:
            return 0

        # Generate version timestamp (nanoseconds) for this update cycle
        version = time.time_ns()

        # transaction=True wraps delete + hsets + version in a MULTI/EXEC so a
        # concurrent reader sees either the old hash or the fully-rebuilt one,
        # never a half-deleted/partial state.
        pipe = self.redis_client.pipeline(transaction=True)
        pipe.delete(self.redis_key)  # Clear old data

        count = 0
        for symbol_data in parsed_data:
            symbol = symbol_data.get('symbol')
            data = symbol_data.get('data')

            if symbol and data:
                pipe.hset(self.redis_key, symbol, json.dumps(data))
                count += 1

        # Never blank a populated hash: if a non-empty-but-malformed API response yielded 0
        # valid symbols, abandon the pipeline (the queued DELETE never runs) so the existing
        # hash — the symbol universe the order-book fetcher reads — is preserved.
        if count == 0:
            self.logger.warning("0 valid symbols parsed; preserving existing hash (skip blanking)")
            return 0

        # Add version field to track data freshness
        pipe.hset(self.redis_key, '_version', version)

        pipe.execute()
        return count

    def run(self):
        """Main run loop - continuously fetch and update data"""
        self.logger.info(f"Starting {self.exchange_name} {self.market_type} market data handler")

        try:
            while not self.shutdown_requested:
                start_time = time.monotonic()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                self.logger.debug(f"[{timestamp}] Starting update cycle")
                success = self.update_redis_data()

                execution_time = time.monotonic() - start_time

                if success:
                    self.logger.debug(f"Update cycle finished in {execution_time:.2f} seconds")
                else:
                    self.logger.warning(f"Update cycle failed after {execution_time:.2f} seconds")

                # Poll-sleep so SIGTERM is observed within ~0.5s rather than
                # waiting out a full update_interval (relevant for slower
                # handlers like bitmart at update_interval=3).
                sleep_remaining = self.update_interval - execution_time
                while sleep_remaining > 0 and not self.shutdown_requested:
                    chunk = min(0.5, sleep_remaining)
                    time.sleep(chunk)
                    sleep_remaining -= chunk

        except KeyboardInterrupt:
            self.logger.info("Shutdown signal received")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        if self.redis_client:
            self.redis_client.close()
            self.logger.info("Closed Redis connection")
        self.logger.info("Market data handler stopped")

    # Abstract methods that exchange plugins must implement

    @abstractmethod
    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse exchange-specific API response format

        Args:
            response_data: Raw idl response from exchange API

        Returns:
            List of dictionaries with format:
            [
                {
                    'symbol': 'BTCUSDT',
                    'data': {
                        '24h_volume_usdt': '123456',
                        'best_bid': '50000.1',
                        'best_ask': '50000.2',
                        'lastPrice': '50000.15',
                        'dumpScale': 2  # or 'accuracy': '0.01' for OKX
                    }
                },
                ...
            ]
        """
        pass