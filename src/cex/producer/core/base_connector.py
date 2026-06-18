#!/usr/bin/env python3
"""
Base Exchange Connector - Core class that eliminates code duplication

This class contains all the common functionality shared across exchange implementations:
- Redis connection management
- Error reporting and recovery
- Symbol management and filtering
- WebSocket connection lifecycle
- Orderbook data processing and storage
- Logging and monitoring

Exchange-specific plugins inherit from this class and only implement:
- Message parsing (parse_message)
- Subscription logic (subscribe_to_symbols)
- Connection-specific behavior (get_websocket_url, etc.)
"""

import asyncio
import inspect
import json
import logging
import random
import signal
import sys
import time
import traceback
import websockets
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any, Union, Tuple
import redis.asyncio as redis

from src.cex.producer.core.socks5_websocket import connect_with_proxy_config
from src.cex.producer.core.redis_manager import RedisManager

from src.cex.producer.config import (
    get_exchange_config, get_redis_config, get_stream_key,
    get_error_queue_key, get_heartbeat_key, ACCEPTABLE_QUOTE_ASSETS,
    MONITORING_CONFIG, STREAM_CONFIG
)


class StaleStreamError(Exception):
    """Raised when no orderbook data is received within the stale_stream_timeout period"""
    def __init__(self, timeout_seconds: int, last_data_time: float):
        self.timeout_seconds = timeout_seconds
        self.last_data_time = last_data_time
        elapsed = time.time() - last_data_time if last_data_time > 0 else timeout_seconds
        super().__init__(f"No orderbook data received for {elapsed:.1f}s (timeout: {timeout_seconds}s)")


def parse_worker_args(description: str = 'Exchange Connector') -> Tuple[Optional[int], Optional[int]]:
    """
    Standard argparse for worker distribution.
    Call this in plugin main() functions.

    Args:
        description: Description for the argument parser

    Returns:
        Tuple of (worker_id, num_workers), both None if not in distributed mode

    Example usage in plugin main():
        from src.cex.producer.core.base_connector import parse_worker_args
        worker_id, num_workers = parse_worker_args('MyExchange Connector')
        connector = MyExchangeConnector(worker_id=worker_id, num_workers=num_workers)
    """
    import argparse
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--worker-id', type=int, default=None,
                        help='Worker ID (0-based index) for distributed mode')
    parser.add_argument('--num-workers', type=int, default=None,
                        help='Total number of workers for distributed mode')
    args = parser.parse_args()

    # Validate - both must be provided together
    if (args.worker_id is None) != (args.num_workers is None):
        print("Error: --worker-id and --num-workers must be used together")
        print("Example: python plugin.py --worker-id 0 --num-workers 4")
        sys.exit(1)

    if args.worker_id is not None:
        if args.worker_id < 0 or args.worker_id >= args.num_workers:
            print(f"Error: --worker-id must be between 0 and {args.num_workers - 1}")
            sys.exit(1)

    return args.worker_id, args.num_workers


class BaseExchangeConnector(ABC):
    """
    Base class for all exchange connectors. Handles 80%+ of common functionality.
    """

    def __init__(self, exchange_name: str, market_type: str = 'spot',
                 worker_id: int = None, num_workers: int = None):
        """
        Initialize base connector with exchange configuration

        Args:
            exchange_name: Name of the exchange (e.g., 'bybit', 'okx')
            market_type: Market type ('spot' or 'futures')
            worker_id: Worker ID (0-based) for distributed mode, None for single process
            num_workers: Total number of workers for distributed mode, None for single process
        """
        self.exchange_name = exchange_name.lower()
        self.market_type = market_type.lower()

        # Worker distribution configuration
        self.worker_id = worker_id
        self.num_workers = num_workers
        self.is_distributed = worker_id is not None and num_workers is not None

        # Get configuration
        self.config = get_exchange_config(self.exchange_name)
        if not self.config:
            raise ValueError(f"No configuration found for exchange: {exchange_name}")

        self.market_config = self.config.get(market_type, {})
        if not self.market_config.get('enabled', False):
            raise ValueError(f"{market_type} market not enabled for {exchange_name}")

        # Redis connection
        self.redis_client: Optional[redis.Redis] = None

        # Connection management
        self.connection_type = self.market_config.get('connection_type', 'individual')
        self.symbols_per_connection = self.market_config.get('symbols_per_connection', 1)
        self.ping_interval = self.market_config.get('ping_interval')

        # State management
        self.active_symbols: Set[str] = set()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.shutdown_event = asyncio.Event()
        self.last_symbol_timestamps: Dict[str, int] = {}  # last RECEIVE time (ms) per symbol
        # Wall-clock of each symbol's last orderbook write — used only for the
        # observability `stale_symbols` heartbeat metric (NOT to inactivate symbols:
        # an unchanged order book is still valid; the consumer age-checks per-entry
        # timestamp_ms). For batched exchanges "active" means the batch connection
        # is alive, so this surfaces symbols whose own book has gone quiet.
        self.last_symbol_update_wall: Dict[str, float] = {}
        self.stale_symbol_age = self.market_config.get(
            'stale_symbol_age', MONITORING_CONFIG.get('stale_symbol_age', 120)
        )

        # Dynamic symbol monitoring
        self.currently_monitored_symbols: Set[str] = set()
        self.symbol_monitoring_task: Optional[asyncio.Task] = None
        self.symbol_check_interval = 30  # Check for symbol changes every 30 seconds

        # Reconnection settings
        self.reconnect_delay_base = self.market_config.get('reconnect_delay_base', 2.0)
        self.reconnect_delay_max = self.market_config.get('reconnect_delay_max', 60.0)

        # Global connection delay (for rate limiting across workers)
        self.initial_connection_delay = self.market_config.get('initial_connection_delay', 0)

        # Orderbook normalization setting (can be overridden by exchanges)
        self.requires_orderbook_normalization = True

        # Stale stream detection (timeout in seconds, 0 to disable)
        self.stale_stream_timeout = self.market_config.get(
            'stale_stream_timeout',
            MONITORING_CONFIG.get('stale_stream_timeout', 60)
        )

        # Connection-failure tolerance: the engine trades on active∧¬inactive set
        # membership (no per-entry age-check), so keep symbols active + their streams
        # intact through TRANSIENT reconnects and only mark inactive + delete streams
        # after this many CONSECUTIVE failures (a genuinely lost connection).
        # consecutive_failures resets to 0 on any successful (re)connect.
        self.cleanup_after_failures = self.market_config.get(
            'cleanup_after_failures',
            MONITORING_CONFIG.get('cleanup_after_failures', 3)
        )

        # Reliability state (P1)
        self.max_consecutive_parse_errors = MONITORING_CONFIG.get('max_consecutive_parse_errors', 10)
        self._schema_version = STREAM_CONFIG.get('schema_version', 1)
        self._backpressure_max_streams = STREAM_CONFIG.get('backpressure_max_streams', 5000)
        self._pending_xadds: Dict[str, Dict[str, Any]] = {}   # stream_key -> newest redis_data
        self._redis_backpressured = False
        self._messages_processed = 0
        self._monitoring_healthy = True
        self._monitor_consecutive_failures = 0
        self.ping_tasks: Dict[str, asyncio.Task] = {}
        self.health_task: Optional[asyncio.Task] = None
        # Does this plugin's parse_message accept the connection's symbol list?
        try:
            self._parse_takes_symbols = 'symbols' in inspect.signature(self.parse_message).parameters
        except (TypeError, ValueError):
            self._parse_takes_symbols = False

        # Setup logging
        self.logger = self._setup_logging()

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

        # Initialize proxy manager (will be created when needed)
        self._proxy_manager = None

        if self.is_distributed:
            self.logger.info(f"Initialized {self.exchange_name} {market_type} connector - Worker {worker_id + 1}/{num_workers}")
        else:
            self.logger.info(f"Initialized {self.exchange_name} {market_type} connector")

    def _setup_logging(self) -> logging.Logger:
        """
        Get logger for this exchange connector

        Logger should already be configured by exchange_manager with dedicated file handler.
        If running standalone, fallback to basic logging.
        """
        from .logging_setup import get_logger_for_connector

        logger = get_logger_for_connector(self.exchange_name, self.market_type)
        return logger

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            # Set shutdown event to trigger cleanup
            self.shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _retry_redis_operation(self, operation, max_retries=3, base_delay=0.1):
        """
        Retry Redis operations with exponential backoff

        Handles transient Redis pool exhaustion errors by retrying with increasing delays.
        Useful for high-concurrency exchanges like Gate.io.

        Args:
            operation: Async callable to execute
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds (doubles each retry)

        Returns:
            Result of the operation
        """
        last_error = None
        delay = base_delay

        for attempt in range(max_retries + 1):
            try:
                return await operation()
            except Exception as e:
                error_msg = str(e).lower()
                # Retry transient pool-exhaustion AND transient network errors so
                # brief Redis blips self-heal before the no-silent-loss buffer is used.
                retryable = (
                    'too many connections' in error_msg
                    or 'connection pool' in error_msg
                    or 'timeout' in error_msg
                    or 'connection reset' in error_msg
                    or 'connection closed' in error_msg
                    or isinstance(e, (ConnectionError, TimeoutError, asyncio.TimeoutError))
                )
                if retryable:
                    last_error = e
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                        delay *= 2  # Exponential backoff
                        continue
                # For other errors, raise immediately
                raise

        # If we exhausted all retries, raise the last error
        if last_error:
            raise last_error

    async def initialize(self):
        """Initialize Redis connection and other resources"""
        await self._connect_redis()

        # Load and apply manual proxy configuration if set
        await self._load_manual_proxy_config()

        # Initialize proxy manager if needed
        if self.config.get('proxy', {}).get('use_proxy', False):
            from .proxy_manager import ProxyManager

            # Use filtered proxy config if manual selection is active
            # Pass worker_id to offset proxy selection across workers
            if hasattr(self, '_filtered_proxy_config'):
                self._proxy_manager = ProxyManager(self.exchange_name, self.config['proxy'], self._filtered_proxy_config, worker_id=self.worker_id)
            else:
                self._proxy_manager = ProxyManager(self.exchange_name, self.config['proxy'], worker_id=self.worker_id)

    async def _connect_redis(self):
        """Establish Redis connection using shared connection pool"""
        try:
            # Use shared Redis connection pool instead of creating individual connections
            self.redis_client = await RedisManager.get_client()
            self.logger.info("Connected to Redis using shared connection pool")
        except Exception as e:
            self.logger.error(f"Failed to get Redis client from shared pool: {e}")
            raise

    async def _load_manual_proxy_config(self):
        """Load manual proxy configuration from Redis and apply to exchange config"""
        try:
            from .manual_proxy_config import get_manual_proxy_config, apply_manual_proxy_to_config

            # Get manual proxy config from Redis
            manual_config = await get_manual_proxy_config(
                self.redis_client,
                self.exchange_name,
                self.market_type
            )

            if manual_config:
                selection = manual_config.get('selection', [])
                self.logger.info(f"✓ Manual proxy configuration applied from admin panel: {selection}")

                # Apply manual config to exchange config
                self.config = apply_manual_proxy_to_config(manual_config, self.config)

                # Store filtered proxy config if it was set
                if '_filtered_proxy_config' in self.config:
                    self._filtered_proxy_config = self.config['_filtered_proxy_config']

                    # Log detailed proxy information with IPs
                    proxy_details = []
                    for proxy in self._filtered_proxy_config:
                        exit_ip = proxy.get('exit_ip', 'unknown')
                        proxy_details.append(f"{proxy['protocol']}://{proxy['host']}:{proxy['port']} (exit IP: {exit_ip})")

                    self.logger.info(f"✓ Using {len(self._filtered_proxy_config)} proxies from admin panel: {', '.join(proxy_details)}")
            else:
                self.logger.debug("No manual proxy configuration found, using default config")

        except Exception as e:
            self.logger.error(f"Error loading manual proxy config: {e}")
            # Don't fail initialization if manual proxy config fails to load
            # Fall back to default config

    async def start(self):
        """Start the exchange connector with dynamic symbol monitoring"""
        self.logger.info(f"Starting {self.exchange_name} {self.market_type} connector...")

        try:
            await self.initialize()

            # Get initial symbols to monitor
            symbols = await self.get_symbols_to_monitor()

            # Filter symbols for this worker if running in distributed mode
            symbols = self._filter_symbols_for_worker(symbols)

            if not symbols:
                self.logger.warning("No symbols to monitor, exiting...")
                return

            # Initialize currently monitored symbols
            self.currently_monitored_symbols = set(symbols)

            # Initialize all symbols as inactive first (they will be marked active when data flows)
            self.logger.info(f"Initializing {len(symbols)} symbols as inactive...")
            for symbol in symbols:
                # Normalize symbol for Redis if the exchange has a custom format (e.g., Gate.io uses BTC_USDT)
                # This ensures consistency between initialization and data processing
                if hasattr(self, '_normalize_symbol_for_redis'):
                    normalized_symbol = self._normalize_symbol_for_redis(symbol)
                    await self._mark_symbol_inactive(normalized_symbol)
                    self.logger.debug(f"Marking {symbol} as inactive (normalized: {normalized_symbol})")
                else:
                    await self._mark_symbol_inactive(symbol)

            self.logger.info(f"Starting with {len(symbols)} symbols: {symbols[:10]}{'...' if len(symbols) > 10 else ''}")

            # Start dynamic symbol monitoring task
            self.symbol_monitoring_task = asyncio.create_task(self._monitor_symbol_changes())

            # Start health/heartbeat + backpressure-drain loop
            self.health_task = asyncio.create_task(self._health_and_drain_loop())

            # Start monitoring based on connection type
            if self.connection_type == 'individual':
                await self._start_individual_connections(symbols)
            elif self.connection_type == 'batched':
                await self._start_batched_connections(symbols)
            else:
                raise ValueError(f"Unknown connection type: {self.connection_type}")

        except Exception as e:
            self.logger.error(f"Failed to start connector: {e}", exc_info=True)
            await self.report_error([], "StartupError", str(e), traceback.format_exc())
        finally:
            await self.cleanup()

    async def _start_individual_connections(self, symbols: List[str]):
        """Start individual WebSocket connections for each symbol"""
        # Calculate worker-aware delays for global rate limiting
        base_delay = self.initial_connection_delay
        if base_delay > 0 and self.is_distributed:
            # Effective delay between this worker's connections (so workers interleave)
            effective_delay = base_delay * self.num_workers
            # Initial offset so workers start at different times
            initial_offset = base_delay * self.worker_id
            await asyncio.sleep(initial_offset)
            self.logger.info(f"Worker {self.worker_id}: starting after {initial_offset:.2f}s offset, {effective_delay:.2f}s between connections")
        elif base_delay > 0:
            effective_delay = base_delay
        else:
            effective_delay = 0.01  # Default 10ms

        for i, symbol in enumerate(symbols):
            if self.shutdown_event.is_set():
                break

            task = asyncio.create_task(self._handle_symbol_connection(symbol))
            self.active_tasks[symbol] = task

            # Add delay between connection attempts
            if i > 0:
                await asyncio.sleep(effective_delay)

        # Wait for shutdown or tasks to complete
        try:
            await self.shutdown_event.wait()
        except Exception as e:
            self.logger.error(f"Error in individual connections: {e}")

    async def _start_batched_connections(self, symbols: List[str]):
        """Start batched WebSocket connections"""
        # Split symbols into batches
        batches = self._create_symbol_batches(symbols)

        self.logger.info(f"Creating {len(batches)} batch connections for {len(symbols)} symbols (max {self.symbols_per_connection} per connection)")

        # Calculate worker-aware delays for global rate limiting
        base_delay = self.initial_connection_delay
        if base_delay > 0 and self.is_distributed:
            # Effective delay between this worker's batches (so workers interleave)
            effective_delay = base_delay * self.num_workers
            # Initial offset so workers start at different times
            initial_offset = base_delay * self.worker_id
            await asyncio.sleep(initial_offset)
            self.logger.info(f"Worker {self.worker_id}: starting after {initial_offset:.2f}s offset, {effective_delay:.2f}s between batches")
        elif base_delay > 0:
            effective_delay = base_delay
        else:
            effective_delay = 0.5  # Default 500ms

        for batch_id, batch_symbols in enumerate(batches):
            if self.shutdown_event.is_set():
                break

            self.logger.info(f"Starting batch {batch_id + 1}/{len(batches)} with {len(batch_symbols)} symbols")
            task = asyncio.create_task(self._handle_batch_connection(batch_id, batch_symbols))
            self.active_tasks[f"batch_{batch_id}"] = task

            # Delay between batch starts to avoid overwhelming the exchange
            if batch_id < len(batches) - 1:  # Don't delay after the last batch
                await asyncio.sleep(effective_delay)

        self.logger.info(f"Created {len(self.active_tasks)} batch connection tasks")

        # Wait for shutdown
        try:
            await self.shutdown_event.wait()
        except Exception as e:
            self.logger.error(f"Error in batched connections: {e}")

    def _create_symbol_batches(self, symbols: List[str]) -> List[List[str]]:
        """Split symbols into batches for batch connections"""
        batches = []
        for i in range(0, len(symbols), self.symbols_per_connection):
            batch = symbols[i:i + self.symbols_per_connection]
            batches.append(batch)
        return batches

    async def _handle_symbol_connection(self, symbol: str):
        """Handle WebSocket connection for a single symbol"""
        consecutive_failures = 0
        reconnect_delay = self.reconnect_delay_base

        while not self.shutdown_event.is_set():
            try:
                self.logger.info(f"[{symbol}] Connecting (failures: {consecutive_failures})...")

                # Get connection parameters (with proxy if needed)
                ws_url = await self.get_websocket_url(symbol)
                connect_kwargs = await self.get_connection_kwargs(symbol)

                # Extract proxy configuration for SOCKS5 support
                proxy_config = None
                if self._proxy_manager:
                    proxy_config = await self._proxy_manager.get_connection_params(symbol)

                websocket = await connect_with_proxy_config(ws_url, proxy_config, **connect_kwargs)
                try:
                    self.logger.info(f"[{symbol}] Connected successfully")
                    consecutive_failures = 0
                    reconnect_delay = self.reconnect_delay_base

                    # Subscribe to symbol (symbols will be marked active when data is received)
                    try:
                        await self.subscribe_to_symbols(websocket, [symbol])
                    except Exception as sub_error:
                        # Mark symbol as inactive if subscription fails
                        await self._mark_symbol_inactive(symbol)
                        await self.report_error([symbol], "SubscriptionFailed", f"Failed to subscribe to {symbol}: {str(sub_error)}")
                        self.logger.error(f"[{symbol}] Subscription failed: {sub_error}")
                        raise  # Re-raise to trigger connection retry or cleanup

                    # Reconnect gap marker so consumers reset per-stream state
                    await self._write_gap_markers([symbol])

                    # Start ping task if needed (tracked so cleanup cancels it)
                    ping_task = None
                    if self.ping_interval:
                        ping_task = asyncio.create_task(self._ping_task(websocket, symbol))
                        self.ping_tasks[symbol] = ping_task

                    # Handle messages
                    try:
                        await self._handle_messages(websocket, [symbol])
                    finally:
                        if ping_task:
                            ping_task.cancel()
                            self.ping_tasks.pop(symbol, None)
                finally:
                    # Always close the websocket
                    await websocket.close()

            except Exception as e:
                consecutive_failures += 1
                await self._handle_connection_error(symbol, e, consecutive_failures)

                # Rotate to a different proxy before the next reconnect
                if self._proxy_manager:
                    await self._proxy_manager.rotate_on_disconnect(symbol)

                if not self.shutdown_event.is_set():
                    capped = min(reconnect_delay, self.reconnect_delay_max)
                    # Jitter prevents a fleet-wide thundering-herd after shared outages.
                    await asyncio.sleep(capped + random.uniform(0, capped * 0.3))
                    reconnect_delay *= 2

    async def _handle_batch_connection(self, batch_id: int, symbols: List[str]):
        """Handle WebSocket connection for a batch of symbols"""
        consecutive_failures = 0
        reconnect_delay = self.reconnect_delay_base
        batch_name = f"batch_{batch_id}"

        while not self.shutdown_event.is_set():
            try:
                self.logger.info(f"[{batch_name}] Connecting with {len(symbols)} symbols...")

                # Get connection parameters
                ws_url = await self.get_websocket_url()
                connect_kwargs = await self.get_connection_kwargs()

                # Extract proxy configuration for SOCKS5 support
                proxy_config = None
                if self._proxy_manager:
                    proxy_config = await self._proxy_manager.get_connection_params()

                websocket = await connect_with_proxy_config(ws_url, proxy_config, **connect_kwargs)
                try:
                    self.logger.info(f"[{batch_name}] Connected successfully")
                    consecutive_failures = 0
                    reconnect_delay = self.reconnect_delay_base

                    # Subscribe to symbols (symbols will be marked active when data is received)
                    try:
                        await self.subscribe_to_symbols(websocket, symbols)
                    except Exception as sub_error:
                        # Mark all symbols in batch as inactive if subscription fails
                        for symbol in symbols:
                            await self._mark_symbol_inactive(symbol)
                        await self.report_error(symbols, "SubscriptionFailed", f"Failed to subscribe to batch {batch_name}: {str(sub_error)}")
                        self.logger.error(f"[{batch_name}] Batch subscription failed: {sub_error}")
                        raise  # Re-raise to trigger connection retry or cleanup

                    # Reconnect gap markers so consumers reset per-stream state
                    await self._write_gap_markers(symbols)

                    # Start ping task if needed (tracked so cleanup cancels it)
                    ping_task = None
                    if self.ping_interval:
                        ping_task = asyncio.create_task(self._ping_task(websocket, batch_name))
                        self.ping_tasks[batch_name] = ping_task

                    # Handle messages
                    try:
                        await self._handle_messages(websocket, symbols)
                    finally:
                        if ping_task:
                            ping_task.cancel()
                            self.ping_tasks.pop(batch_name, None)
                finally:
                    # Always close the websocket
                    await websocket.close()

            except Exception as e:
                consecutive_failures += 1

                # Handle batch connection error with proper symbol cleanup
                error_type = type(e).__name__
                error_msg = str(e)

                self.logger.error(f"[{batch_name}] Connection error ({consecutive_failures}): {error_msg}")

                # Report error for all symbols in this batch
                await self.report_error(symbols, error_type, error_msg, traceback.format_exc())

                # Keep symbols active + streams intact through transient reconnects; only
                # cleanup (mark inactive + delete streams) after sustained failure, so the
                # engine's tradeable set (active∧¬inactive) doesn't flap on brief blips.
                if consecutive_failures >= self.cleanup_after_failures:
                    await self._cleanup_symbols_on_failure(symbols)
                    self.logger.warning(f"Cleaned up batch {batch_name} ({len(symbols)} symbols) after {consecutive_failures} consecutive failures")

                # Handle proxy failover if configured
                if self._proxy_manager and consecutive_failures >= 3:
                    await self._proxy_manager.handle_connection_failure(error_type, None)

                # Rotate to a different proxy before the next reconnect
                if self._proxy_manager:
                    await self._proxy_manager.rotate_on_disconnect()

                if not self.shutdown_event.is_set():
                    capped = min(reconnect_delay, self.reconnect_delay_max)
                    await asyncio.sleep(capped + random.uniform(0, capped * 0.3))
                    reconnect_delay *= 2

    async def _handle_messages(self, websocket, symbols: List[str]):
        """Handle incoming WebSocket messages with stale-stream detection.

        Reads with a per-recv timeout so a dead socket (no bytes for
        stale_stream_timeout seconds) is detected and reconnected instead of
        blocking forever. Control messages (ping/pong/acks) go through the
        overridable handle_control_message() hook and count as liveness.
        Consecutive parse errors past a threshold force a reconnect.
        """
        last_data_time = time.time()
        consecutive_parse_errors = 0
        timeout = self.stale_stream_timeout if (self.stale_stream_timeout and self.stale_stream_timeout > 0) else None
        recv_timeout = min(timeout, MONITORING_CONFIG.get('recv_poll_timeout', 10)) if timeout else None

        try:
            while not self.shutdown_event.is_set():
                try:
                    if recv_timeout is not None:
                        message = await asyncio.wait_for(websocket.recv(), timeout=recv_timeout)
                    else:
                        message = await websocket.recv()
                except asyncio.TimeoutError:
                    if timeout and (time.time() - last_data_time) > timeout:
                        raise StaleStreamError(timeout, last_data_time)
                    continue

                last_data_time = time.time()  # any byte = socket alive

                try:
                    if await self.handle_control_message(websocket, message):
                        continue
                except Exception as ctrl_err:
                    self.logger.debug(f"control message handler error: {ctrl_err}")

                try:
                    if self._parse_takes_symbols:
                        parsed_data = await self.parse_message(message, symbols)
                    else:
                        parsed_data = await self.parse_message(message)
                    if parsed_data:
                        await self._process_orderbook_data(parsed_data)
                    consecutive_parse_errors = 0
                except Exception as e:
                    consecutive_parse_errors += 1
                    self.logger.error(f"Error processing message: {e}")
                    await self.report_error(symbols, "MessageProcessingError", str(e))
                    if consecutive_parse_errors >= self.max_consecutive_parse_errors:
                        self.logger.error(f"{consecutive_parse_errors} consecutive parse errors; reconnecting")
                        raise

        except websockets.exceptions.ConnectionClosed:
            self.logger.info("WebSocket connection closed")
            raise
        except StaleStreamError as e:
            self.logger.warning(str(e))
            raise
        except Exception as e:
            self.logger.error(f"Error in message handling: {e}")
            raise

    async def handle_control_message(self, websocket, message) -> bool:
        """Optionally handle a transport/control message (ping/pong, acks).
        Return True if it was a control message and must NOT be parsed as an
        orderbook (still counts as liveness). Default: no-op."""
        return False

    async def _process_orderbook_data(self, data: Dict[str, Any]):
        """Process and store orderbook data with timestamp validation"""
        try:
            symbol = data.get('symbol')
            if not symbol:
                self.logger.warning("Received orderbook data without symbol")
                return
            # Canonical uppercase form so the stream key, the entry's symbol field, and the
            # active/inactive sets all agree (the engine joins active∧¬inactive to the stream).
            symbol = self._normalize_symbol_for_redis(symbol)

            # Exchange-provided event time. For some venues this is the book *generation*
            # time, which can lag by minutes/hours for illiquid books (e.g. okx) or arrive
            # out of order — so we keep it for information but DO NOT gate on it. The engine
            # judges freshness by active-set membership, and messages on a single socket
            # already arrive in order, so the latest received message is the freshest book.
            # (Gating on event time previously dropped fresh re-broadcasts whose generation
            # time went backwards, silently wedging those books.)
            timestamp_ms = data.get('timestamp_ms', int(time.time() * 1000))
            recv_ts_ms = int(time.time() * 1000)  # true receive time — the honest "last update"
            self.last_symbol_timestamps[symbol] = recv_ts_ms

            # Store in Redis stream
            stream_key = get_stream_key(self.exchange_name, self.market_type, symbol)

            # Get bids and asks from data
            bids = data.get('bids', [])
            asks = data.get('asks', [])

            # Normalize orderbook data if required
            if self.requires_orderbook_normalization:
                bids, asks = self._normalize_orderbook(bids, asks)

            # Coerce every level to [float, float] so every exchange's stream
            # has the same numeric shape — Rust readers can deserialize as
            # [f64, f64] without per-exchange string/number branching.
            bids = self._coerce_levels_to_floats(bids)
            asks = self._coerce_levels_to_floats(asks)

            # schema_version is additive — the Rust reader ignores unknown stream
            # fields and reads the rest by name.
            redis_data = {
                'timestamp_ms': timestamp_ms,
                'recv_ts_ms': recv_ts_ms,
                'symbol': symbol,
                'bids': json.dumps(bids),
                'asks': json.dumps(asks),
                'worker_id': str(self.worker_id) if self.worker_id is not None else 'none',
                'schema_version': self._schema_version,
            }

            # No-silent-loss write: retry transients, else buffer (collapse-to-newest).
            await self._store_redis_data(stream_key, redis_data)
            self._messages_processed += 1
            self.last_symbol_update_wall[symbol] = time.time()  # for stale_symbols metric

            # Only mark symbol active if not already tracked (reduces Redis ops from 3 to 1 per message)
            if symbol not in self.active_symbols:
                await self._mark_symbol_active(symbol)

        except Exception as e:
            self.logger.error(f"Error storing orderbook data: {e}")
            await self.report_error([data.get('symbol', 'unknown')], "StorageError", str(e))

    def _coerce_levels_to_floats(self, levels: List[List]) -> List[List[float]]:
        """Normalize every [price, qty, ...] entry to [float, float]. Drops any
        level whose price or qty cannot be parsed (rather than mixing a malformed
        row into an otherwise numeric stream). Trailing fields (e.g. order count)
        are discarded — readers only need price and qty."""
        if not levels:
            return []
        out: List[List[float]] = []
        for level in levels:
            try:
                price = float(level[0])
                qty = float(level[1])
            except (TypeError, ValueError, IndexError):
                continue
            out.append([price, qty])
        return out

    def _normalize_orderbook(self, bids: List[List], asks: List[List]) -> Tuple[List[List], List[List]]:
        """
        Normalize orderbook to standard format:
        - Bids: descending by price (highest first) - best bid at index 0
        - Asks: ascending by price (lowest first) - best ask at index 0

        Args:
            bids: List of [price, amount] pairs
            asks: List of [price, amount] pairs

        Returns:
            Tuple of (normalized_bids, normalized_asks)
        """
        try:
            # Normalize bids - sort by price descending (highest price first)
            normalized_bids = []
            if bids:
                # Convert to float for sorting, then back to original format
                sorted_bids = sorted(bids, key=lambda x: float(x[0]), reverse=True)
                normalized_bids = sorted_bids

            # Normalize asks - sort by price ascending (lowest price first)
            normalized_asks = []
            if asks:
                # Convert to float for sorting, then back to original format
                sorted_asks = sorted(asks, key=lambda x: float(x[0]))
                normalized_asks = sorted_asks

            return normalized_bids, normalized_asks

        except (ValueError, TypeError, IndexError) as e:
            self.logger.warning(f"Error normalizing orderbook data: {e}, returning original data")
            return bids, asks

    async def _store_redis_data(self, stream_key: str, redis_data: Dict[str, Any]):
        """xadd with retry; on persistent failure buffer the NEWEST update per
        stream instead of silently dropping it. The health/drain loop flushes the
        buffer when Redis recovers. Memory bounded (one entry per stream)."""
        maxlen = STREAM_CONFIG.get('orderbook_maxlen', 10)

        async def _do_xadd():
            await self.redis_client.xadd(stream_key, redis_data, maxlen=maxlen)

        try:
            await self._retry_redis_operation(_do_xadd)
            self._pending_xadds.pop(stream_key, None)
        except Exception as e:
            self._pending_xadds[stream_key] = redis_data
            if (len(self._pending_xadds) >= self._backpressure_max_streams
                    and not self._redis_backpressured):
                self._redis_backpressured = True
                self.logger.critical(
                    f"Redis backpressure: {len(self._pending_xadds)} streams buffered "
                    f"(cap {self._backpressure_max_streams}); newest-per-stream retained. {e}")
                await self.report_error([], "RedisBackpressure", str(e))

    async def _flush_pending_xadds(self):
        """Drain the no-silent-loss buffer once Redis is healthy again."""
        if not self._pending_xadds:
            self._redis_backpressured = False
            return
        try:
            healthy = await RedisManager.health_check()
        except Exception:
            healthy = False
        if not healthy:
            return
        maxlen = STREAM_CONFIG.get('orderbook_maxlen', 10)
        drained = 0
        for stream_key, redis_data in list(self._pending_xadds.items()):
            try:
                await self.redis_client.xadd(stream_key, redis_data, maxlen=maxlen)
                self._pending_xadds.pop(stream_key, None)
                drained += 1
            except Exception:
                break
        if drained:
            self.logger.info(f"Drained {drained} buffered orderbook updates after Redis recovery")
        if not self._pending_xadds:
            self._redis_backpressured = False

    async def _write_gap_markers(self, symbols: List[str]):
        """Write a one-shot reconnect marker per symbol (additive, backward-safe:
        empty bids/asks + gap='reconnect'; existing readers already skip empties)."""
        ts = int(time.time() * 1000)
        wid = str(self.worker_id) if self.worker_id is not None else 'none'
        for symbol in symbols:
            try:
                norm = (self._normalize_symbol_for_redis(symbol)
                        if hasattr(self, '_normalize_symbol_for_redis') else symbol)
                stream_key = get_stream_key(self.exchange_name, self.market_type, norm)
                await self._store_redis_data(stream_key, {
                    'timestamp_ms': ts, 'recv_ts_ms': ts, 'symbol': norm, 'bids': '[]', 'asks': '[]',
                    'worker_id': wid, 'schema_version': self._schema_version, 'gap': 'reconnect',
                })
            except Exception as e:
                self.logger.debug(f"gap marker write failed for {symbol}: {e}")

    async def _write_heartbeat(self):
        """Publish this worker's health heartbeat (supervisor + healthcheck read it)."""
        try:
            key = get_heartbeat_key(self.exchange_name, self.market_type, self.worker_id)
            proxy_label = self._proxy_manager.current_proxy_label() if self._proxy_manager else 'direct'
            rotations = getattr(self._proxy_manager, 'rotations', 0) if self._proxy_manager else 0
            # Observability: active symbols whose own orderbook hasn't been written
            # within stale_symbol_age. For batched exchanges this exposes the gap
            # between "connection alive" (active) and "this symbol has fresh data".
            now = time.time()
            stale_symbols = sum(
                1 for s in self.active_symbols
                if now - self.last_symbol_update_wall.get(s, 0) > self.stale_symbol_age
            )
            payload = {
                'ts': int(time.time() * 1000),
                'msgs': self._messages_processed,
                'active_symbols': len(self.active_symbols),
                'monitored_symbols': len(self.currently_monitored_symbols),
                'stale_symbols': stale_symbols,
                'buffered_streams': len(self._pending_xadds),
                'redis_backpressured': self._redis_backpressured,
                'monitoring_healthy': self._monitoring_healthy,
                'current_proxy': proxy_label,
                'proxy_rotations': rotations,
                'worker_id': 'none' if self.worker_id is None else self.worker_id,
                'schema_version': self._schema_version,
            }
            ttl = MONITORING_CONFIG.get('heartbeat_ttl', 60)
            await self.redis_client.set(key, json.dumps(payload), ex=ttl)
        except Exception as e:
            self.logger.debug(f"heartbeat write failed: {e}")

    async def _health_and_drain_loop(self):
        """Background: drain backpressure buffer on Redis recovery + write heartbeat."""
        drain_interval = 5
        hb_interval = MONITORING_CONFIG.get('heartbeat_interval', 15)
        last_hb = 0.0
        while not self.shutdown_event.is_set():
            try:
                await self._flush_pending_xadds()
                now = time.time()
                if now - last_hb >= hb_interval:
                    await self._write_heartbeat()
                    last_hb = now
            except Exception as e:
                self.logger.debug(f"health/drain loop error: {e}")
            try:
                await asyncio.wait_for(self.shutdown_event.wait(), timeout=drain_interval)
                break
            except asyncio.TimeoutError:
                continue

    def _normalize_symbol_for_redis(self, symbol: str) -> str:
        """Canonical Redis-facing symbol form — MUST match get_stream_key()'s casing
        (uppercase) so the active/inactive sets and the stream key ALWAYS agree. The
        engine reads a book iff the symbol is in active, NOT in inactive, AND its stream
        exists — all keyed by this form; a casing mismatch leaves active-without-stream
        (or a symbol the engine can't see). Plugins may override but must stay consistent."""
        return symbol.upper()

    async def _mark_symbol_active(self, symbol: str):
        """Mark symbol as active in Redis with retry logic"""
        symbol = self._normalize_symbol_for_redis(symbol)
        async def _do_mark_active():
            active_key = f"symbols_status:{self.exchange_name}:{self.market_type}:active_symbols"
            inactive_key = f"symbols_status:{self.exchange_name}:{self.market_type}:inactive_symbols"

            # Add to active set and remove from inactive set
            await self.redis_client.sadd(active_key, symbol)
            await self.redis_client.srem(inactive_key, symbol)

        try:
            # Retry on connection pool exhaustion
            await self._retry_redis_operation(_do_mark_active)

            # Update local state only after successful Redis operations
            self.active_symbols.add(symbol)

        except Exception as e:
            self.logger.error(f"Error marking symbol {symbol} as active: {e}")

    async def _mark_symbol_inactive(self, symbol: str):
        """Mark symbol as inactive in Redis with retry logic"""
        symbol = self._normalize_symbol_for_redis(symbol)
        async def _do_mark_inactive():
            active_key = f"symbols_status:{self.exchange_name}:{self.market_type}:active_symbols"
            inactive_key = f"symbols_status:{self.exchange_name}:{self.market_type}:inactive_symbols"

            # Add to inactive set and remove from active set
            await self.redis_client.sadd(inactive_key, symbol)
            await self.redis_client.srem(active_key, symbol)

        try:
            # Retry on connection pool exhaustion
            await self._retry_redis_operation(_do_mark_inactive)

            # Update local state only after successful Redis operations
            self.active_symbols.discard(symbol)

        except Exception as e:
            self.logger.error(f"Error marking symbol {symbol} as inactive: {e}")

    async def _delete_symbol_stream(self, symbol: str):
        """Delete Redis stream for a symbol"""
        try:
            stream_key = get_stream_key(self.exchange_name, self.market_type, symbol)
            deleted = await self.redis_client.delete(stream_key)
            if deleted:
                self.logger.info(f"Deleted stream for symbol: {symbol}")
            else:
                self.logger.debug(f"No stream found to delete for symbol: {symbol}")

        except Exception as e:
            self.logger.error(f"Error deleting stream for symbol {symbol}: {e}")

    async def _cleanup_symbols_on_failure(self, symbols: List[str]):
        """Mark symbols as inactive and delete their streams after persistent failures"""
        try:
            # Mark all symbols as inactive
            for symbol in symbols:
                await self._mark_symbol_inactive(symbol)

            # Delete streams for all symbols
            for symbol in symbols:
                await self._delete_symbol_stream(symbol)

            self.logger.warning(f"Cleaned up {len(symbols)} symbols due to persistent connection failures")

        except Exception as e:
            self.logger.error(f"Error during symbol cleanup: {e}")

    async def _ping_task(self, websocket, identifier: str):
        """Send periodic ping messages to keep connection alive"""
        try:
            while not self.shutdown_event.is_set():
                await asyncio.sleep(self.ping_interval)

                ping_message = await self.get_ping_message()
                if ping_message:
                    await websocket.send(ping_message)
                    self.logger.debug(f"[{identifier}] Sent ping")

        except asyncio.CancelledError:
            self.logger.debug(f"[{identifier}] Ping task cancelled")
        except Exception as e:
            self.logger.error(f"[{identifier}] Ping task error: {e}")

    async def _handle_connection_error(self, identifier: str, error: Exception, consecutive_failures: int):
        """Handle connection errors and determine retry strategy"""
        error_type = type(error).__name__
        error_msg = str(error)

        self.logger.error(f"[{identifier}] Connection error ({consecutive_failures}): {error_msg}")

        # Determine affected symbols
        if isinstance(identifier, str) and not identifier.startswith('batch_'):
            symbols = [identifier]  # Individual symbol
        else:
            # For batch connections, we'd need to track which symbols are in this batch
            # For now, we'll handle this in the batch-specific error handling
            symbols = []

        # Report to error queue
        await self.report_error(symbols, error_type, error_msg, traceback.format_exc())

        # Keep the symbol active + its stream through transient reconnects; only cleanup
        # (mark inactive + delete stream) after sustained failure (the engine trades on
        # active∧¬inactive membership, so avoid flapping it on brief blips).
        if symbols and consecutive_failures >= self.cleanup_after_failures:
            await self._cleanup_symbols_on_failure(symbols)
            self.logger.warning(f"Cleaned up symbols {symbols} after {consecutive_failures} consecutive failures")

        # Handle proxy failover if configured
        if self._proxy_manager and consecutive_failures >= 3:
            await self._proxy_manager.handle_connection_failure(error_type, None)

    async def get_symbols_to_monitor(self) -> List[str]:
        """Get list of symbols to monitor from Redis"""
        try:
            market_data_key = f"{self.market_type}-market-data:{self.exchange_name}"
            symbol_data = await self.redis_client.hgetall(market_data_key)

            if not symbol_data:
                self.logger.warning(f"No symbol data found in Redis key: {market_data_key}")
                return []

            # Filter symbols based on acceptable quote assets
            filtered_symbols = []
            for symbol, data_str in symbol_data.items():
                # Ensure symbol is string
                symbol = symbol.decode('utf-8') if isinstance(symbol, bytes) else symbol

                # Skip metadata fields (like _version) and non-string values
                if symbol.startswith('_') or not isinstance(data_str, (str, bytes)):
                    continue

                # Convert bytes to string if needed
                data_str = data_str.decode('utf-8') if isinstance(data_str, bytes) else data_str

                try:
                    data = json.loads(data_str)

                    # Try different field names for quote asset
                    quote_asset = (
                        data.get('quote_asset') or
                        data.get('quoteCoin') or
                        data.get('quoteAsset') or
                        data.get('quote') or
                        ''
                    )

                    # If no quote asset field found, try to extract from symbol name
                    if not quote_asset:
                        symbol_upper = symbol.upper()
                        for quote in ACCEPTABLE_QUOTE_ASSETS:
                            if symbol_upper.endswith(quote):
                                quote_asset = quote
                                break

                    if quote_asset in ACCEPTABLE_QUOTE_ASSETS:
                        filtered_symbols.append(symbol)

                except (json.JSONDecodeError, KeyError):
                    self.logger.warning(f"Invalid symbol data for {symbol}")
                    continue

            # CRITICAL: Sort symbols to ensure consistent ordering across all workers
            # Without sorting, workers starting at different times might see symbols
            # in different orders, causing modulo distribution to assign the same
            # symbol to multiple workers (race condition)
            return sorted(filtered_symbols)

        except Exception as e:
            self.logger.error(f"Error getting symbols to monitor: {e}")
            return []

    def _filter_symbols_for_worker(self, all_symbols: List[str]) -> List[str]:
        """
        Filter symbols for this worker using modulo distribution.

        This is called automatically in start() after get_symbols_to_monitor() returns.
        Plugins that override get_symbols_to_monitor() don't need to call this manually.

        Symbols should ideally be sorted by importance (e.g., volume) before this filter
        is applied, so modulo distribution spreads high-importance symbols evenly.

        Worker 0 gets symbols[0], symbols[4], symbols[8], ...
        Worker 1 gets symbols[1], symbols[5], symbols[9], ...
        etc.
        """
        if not self.is_distributed:
            return all_symbols

        worker_symbols = [s for i, s in enumerate(all_symbols)
                         if i % self.num_workers == self.worker_id]

        self.logger.info(
            f"Worker {self.worker_id + 1}/{self.num_workers}: "
            f"handling {len(worker_symbols)}/{len(all_symbols)} symbols"
        )


        # Log sample of symbols this worker handles
        if worker_symbols:
            sample = worker_symbols[:5]
            self.logger.debug(f"Worker {self.worker_id} sample symbols: {sample}")

        return worker_symbols

    async def report_error(self, symbols: List[str], error_type: str, error_message: str, traceback_str: str = ""):
        """Report error to Redis error queue"""
        try:
            error_entry = {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "source_script": f"{self.exchange_name}_{self.market_type}_plugin",
                "exchange": self.exchange_name,
                "market_type": self.market_type,
                "affected_symbols": symbols,
                "error_type": error_type,
                "error_message": error_message,
                "traceback": traceback_str
            }

            error_queue_key = get_error_queue_key(self.exchange_name)
            # Bounded push: keep only the most recent N entries so a retry storm
            # (e.g. EMFILE loop) can't grow the queue without limit and bloat Redis.
            max_entries = STREAM_CONFIG.get('error_queue_max_entries', 5000)
            pipe = self.redis_client.pipeline()
            pipe.lpush(error_queue_key, json.dumps(error_entry))
            pipe.ltrim(error_queue_key, 0, max_entries - 1)
            await pipe.execute()

            self.logger.debug(f"Reported error to Redis: {error_type}")

        except Exception as e:
            self.logger.error(f"Failed to report error to Redis: {e}")

    # Dynamic Symbol Monitoring Methods

    async def get_current_market_symbols(self) -> Set[str]:
        """Get current symbols from market data Redis"""
        try:
            market_data_key = f"{self.market_type}-market-data:{self.exchange_name}"
            symbols = await self.redis_client.hkeys(market_data_key)

            # Filter symbols based on acceptable quote assets
            filtered_symbols = []
            for symbol in symbols:
                # Ensure symbol is string (handle both bytes and str from Redis)
                symbol = symbol.decode('utf-8') if isinstance(symbol, bytes) else symbol

                # Skip metadata fields (like _version)
                if symbol.startswith('_'):
                    continue

                # Extract quote asset from symbol name (e.g., BTCUSDT -> USDT)
                quote_asset = None
                symbol_upper = symbol.upper()
                for quote in ACCEPTABLE_QUOTE_ASSETS:
                    if symbol_upper.endswith(quote):
                        quote_asset = quote
                        break

                if quote_asset:
                    filtered_symbols.append(symbol)

            self.logger.debug(f"Found {len(filtered_symbols)} valid symbols in market data")
            return set(filtered_symbols)

        except Exception as e:
            self.logger.error(f"Error getting current market symbols: {e}")
            return set()

    async def detect_symbol_changes(self) -> tuple[Set[str], Set[str]]:
        """
        Detect new and removed symbols by comparing market data with currently monitored symbols

        Returns:
            tuple: (new_symbols, removed_symbols)
        """
        current_market_symbols = await self.get_current_market_symbols()

        # CRITICAL: Filter to only this worker's symbols before comparing
        # Without this, each worker sees other workers' symbols as "new" and starts
        # monitoring them, causing ALL workers to monitor ALL symbols!
        #
        # For new_symbols: Use alphabetical filtering so new listings go to one worker
        # For removed_symbols: Check against FULL market to detect true delistings only
        #
        # This handles exchanges with custom sorting (like Gate.io sorting by volume):
        # - Startup symbols are distributed by custom sort order
        # - New listings are distributed by alphabetical order (acceptable)
        # - Delistings are detected by checking if symbol exists in market at all
        if self.is_distributed:
            sorted_symbols = sorted(current_market_symbols)
            worker_symbols_from_market = set(
                s for i, s in enumerate(sorted_symbols)
                if i % self.num_workers == self.worker_id
            )

            # New symbols: in this worker's alphabetical slice AND not already monitored
            new_symbols = worker_symbols_from_market - self.currently_monitored_symbols

            # Removed symbols: currently monitored AND gone from market entirely (true delistings)
            removed_symbols = self.currently_monitored_symbols - current_market_symbols
        else:
            # Non-distributed mode: simple comparison
            new_symbols = current_market_symbols - self.currently_monitored_symbols
            removed_symbols = self.currently_monitored_symbols - current_market_symbols

        return new_symbols, removed_symbols

    async def start_monitoring_new_symbols(self, new_symbols: Set[str]):
        """Start monitoring new symbols dynamically"""
        if not new_symbols:
            return

        self.logger.info(f"🆕 Starting monitoring for {len(new_symbols)} new symbols: {list(new_symbols)[:5]}{'...' if len(new_symbols) > 5 else ''}")

        try:
            if self.connection_type == 'individual':
                await self._start_individual_symbols(new_symbols)
            elif self.connection_type == 'batched':
                await self._start_batched_symbols(new_symbols)

            # Update our tracked symbols
            self.currently_monitored_symbols.update(new_symbols)

        except Exception as e:
            self.logger.error(f"Error starting monitoring for new symbols: {e}")
            await self.report_error(list(new_symbols), "NewSymbolStartError", str(e))

    async def stop_monitoring_removed_symbols(self, removed_symbols: Set[str]):
        """Stop monitoring removed/delisted symbols and clean up"""
        if not removed_symbols:
            return

        self.logger.info(f"🗑️ Stopping monitoring for {len(removed_symbols)} removed symbols: {list(removed_symbols)[:5]}{'...' if len(removed_symbols) > 5 else ''}")

        try:
            # Cancel tasks for removed symbols
            for symbol in removed_symbols:
                if symbol in self.active_tasks:
                    task = self.active_tasks[symbol]
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                    del self.active_tasks[symbol]

                # Remove from active symbols
                self.active_symbols.discard(symbol)

                # Prune per-symbol state to avoid unbounded growth (REL-19/03)
                self.last_symbol_timestamps.pop(symbol, None)
                self._pending_xadds.pop(
                    get_stream_key(self.exchange_name, self.market_type, symbol), None)
                pt = self.ping_tasks.pop(symbol, None)
                if pt and not pt.done():
                    pt.cancel()

                # Clean up symbol streams and mark inactive
                await self._mark_symbol_inactive(symbol)
                await self._delete_symbol_stream(symbol)

            # Update our tracked symbols
            self.currently_monitored_symbols -= removed_symbols

            # For batched connections, we may need to reorganize batches
            if self.connection_type == 'batched':
                await self._reorganize_batches_after_removal(removed_symbols)

            self.logger.info(f"✅ Successfully stopped monitoring {len(removed_symbols)} removed symbols")

        except Exception as e:
            self.logger.error(f"Error stopping monitoring for removed symbols: {e}")

    async def _start_individual_symbols(self, symbols: Set[str]):
        """Start individual connections for new symbols"""
        # Use same delay logic as initial connections
        base_delay = self.initial_connection_delay
        if base_delay > 0 and self.is_distributed:
            effective_delay = base_delay * self.num_workers
        elif base_delay > 0:
            effective_delay = base_delay
        else:
            effective_delay = 0.01  # Default 10ms

        for i, symbol in enumerate(symbols):
            if self.shutdown_event.is_set():
                break

            task = asyncio.create_task(self._handle_symbol_connection(symbol))
            self.active_tasks[symbol] = task

            if i > 0:
                await asyncio.sleep(effective_delay)

    async def _start_batched_symbols(self, symbols: Set[str]):
        """Start batched connections for new symbols (add to existing batches or create new ones)"""
        # For now, create new batches for new symbols
        # TODO: Optimize to add to existing batches with capacity
        new_batches = self._create_symbol_batches(list(symbols))

        # Use same delay logic as initial connections
        base_delay = self.initial_connection_delay
        if base_delay > 0 and self.is_distributed:
            effective_delay = base_delay * self.num_workers
        elif base_delay > 0:
            effective_delay = base_delay
        else:
            effective_delay = 0.5  # Default 500ms

        for batch_id, batch_symbols in enumerate(new_batches):
            if self.shutdown_event.is_set():
                break

            batch_name = f"new_batch_{int(time.time())}_{batch_id}"
            task = asyncio.create_task(self._handle_batch_connection(batch_name, batch_symbols))
            self.active_tasks[batch_name] = task

            if batch_id < len(new_batches) - 1:
                await asyncio.sleep(effective_delay)

    async def _reorganize_batches_after_removal(self, removed_symbols: Set[str]):
        """Reorganize batched connections after symbols are removed"""
        # For batched connections, we may have partially empty batches
        # For now, just log - in the future we could optimize batch utilization
        self.logger.debug(f"Batched connections reorganization after removing {len(removed_symbols)} symbols")

    async def _monitor_symbol_changes(self):
        """Background task to monitor symbol changes and adapt connections"""
        self.logger.info(f"🔍 Starting symbol change monitoring (checking every {self.symbol_check_interval}s)")

        while not self.shutdown_event.is_set():
            try:
                # Detect symbol changes
                new_symbols, removed_symbols = await self.detect_symbol_changes()

                # Handle new symbols (listings)
                if new_symbols:
                    await self.start_monitoring_new_symbols(new_symbols)

                # Handle removed symbols (delistings)
                if removed_symbols:
                    await self.stop_monitoring_removed_symbols(removed_symbols)

                # Log heartbeat every cycle (for watchdog monitoring)
                active_count = len(self.active_symbols)
                total_count = len(self.currently_monitored_symbols)
                self.logger.info(f"💓 Heartbeat: monitoring {active_count}/{total_count} active symbols")

                # Log changes separately if any
                if new_symbols or removed_symbols:
                    self.logger.info(f"📊 Symbol changes: +{len(new_symbols)} new, -{len(removed_symbols)} removed")

                if self._monitor_consecutive_failures:
                    self._monitor_consecutive_failures = 0
                    self._monitoring_healthy = True

            except Exception as e:
                self._monitor_consecutive_failures += 1
                self.logger.error(f"Error in symbol change monitoring ({self._monitor_consecutive_failures}): {e}")
                if self._monitor_consecutive_failures >= 5:
                    self._monitoring_healthy = False
                if self._monitor_consecutive_failures >= 15:
                    self.logger.critical("Symbol monitoring failed 15x; signaling shutdown for respawn")
                    await self.report_error([], "MonitoringFailure", str(e))
                    self.shutdown_event.set()

            # Wait before next check
            try:
                await asyncio.wait_for(self.shutdown_event.wait(), timeout=self.symbol_check_interval)
                break  # Shutdown requested
            except asyncio.TimeoutError:
                continue  # Continue monitoring

    async def cleanup(self):
        """Cleanup resources and connections"""
        import traceback as tb
        self.logger.info("="*60)
        self.logger.info("Starting cleanup...")
        self.logger.info(f"Stack trace: {tb.format_stack()[-3].strip()}")
        self.logger.info("="*60)

        # Cancel symbol monitoring task
        if self.symbol_monitoring_task and not self.symbol_monitoring_task.done():
            self.symbol_monitoring_task.cancel()

        # Cancel health/drain task
        if self.health_task and not self.health_task.done():
            self.health_task.cancel()

        # Cancel tracked ping tasks (REL-03: previously leaked on shutdown)
        for _pt in list(self.ping_tasks.values()):
            if not _pt.done():
                _pt.cancel()
        self.ping_tasks.clear()

        # Cancel all active tasks IMMEDIATELY (aggressive cancellation for fast cleanup)
        cancelled_count = 0
        for task_name, task in self.active_tasks.items():
            if not task.done():
                task.cancel()
                cancelled_count += 1

        if cancelled_count > 0:
            self.logger.info(f"Cancelled {cancelled_count} active tasks")
            # Brief wait for tasks to acknowledge cancellation
            await asyncio.sleep(0.1)

        # Mark all symbols as inactive and delete their streams
        if self.redis_client and self.currently_monitored_symbols:
            try:
                symbols_to_cleanup = list(self.currently_monitored_symbols)  # Make a copy of ALL monitored symbols

                # Log sample symbols for debugging format issues
                if symbols_to_cleanup:
                    sample_symbols = symbols_to_cleanup[:3]
                    self.logger.debug(f"Sample symbols before normalization: {sample_symbols}")

                # Use Redis pipeline for fast batch operations (critical for exchanges with 1000+ symbols)
                # Use transaction=False to avoid silent rollbacks
                pipe = self.redis_client.pipeline(transaction=False)

                inactive_key = f"symbols_status:{self.exchange_name}:{self.market_type}:inactive_symbols"
                active_key = f"symbols_status:{self.exchange_name}:{self.market_type}:active_symbols"

                # Batch all operations: mark inactive + delete streams
                for symbol in symbols_to_cleanup:
                    # Normalize symbol if exchange has custom format (e.g., Gate.io uses BTC_USDT)
                    if hasattr(self, '_normalize_symbol_for_redis'):
                        normalized_symbol = self._normalize_symbol_for_redis(symbol)
                    else:
                        normalized_symbol = symbol

                    # Mark symbol inactive
                    pipe.sadd(inactive_key, normalized_symbol)
                    pipe.srem(active_key, normalized_symbol)
                    # Delete stream
                    stream_key = get_stream_key(self.exchange_name, self.market_type, normalized_symbol)
                    pipe.delete(stream_key)

                # Execute all operations at once (1 round trip vs thousands)
                results = await pipe.execute()

                # Verify execution succeeded
                if results and len(results) > 0:
                    successful_ops = len([r for r in results if r is not None])
                    # Check if normalization happened (for debugging Gate.io issues)
                    has_normalization = hasattr(self, '_normalize_symbol_for_redis')
                    self.logger.info(f"✓ Cleanup successful: {len(symbols_to_cleanup)} symbols processed, {successful_ops} operations completed (normalization: {has_normalization})")
                else:
                    self.logger.error(f"✗ Pipeline execution returned no results - cleanup may have failed!")

            except Exception as e:
                self.logger.error(f"Error during symbol cleanup: {e}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")

        # Redis connection is managed by shared pool - no need to close individually
        if self.redis_client:
            self.logger.info("Redis connection managed by shared pool")

        self.logger.info("Cleanup completed")

    # Abstract methods that exchange plugins must implement

    @abstractmethod
    async def get_websocket_url(self, symbol: str = None) -> str:
        """Get WebSocket URL for connection. Symbol may be needed for some exchanges."""
        pass

    @abstractmethod
    async def parse_message(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Parse incoming WebSocket message.

        Returns:
            Dict with keys: symbol, timestamp_ms, bids, asks, sequence (optional)
            None if message should be ignored
        """
        pass

    @abstractmethod
    async def subscribe_to_symbols(self, websocket, symbols: List[str]):
        """Subscribe to orderbook updates for given symbols"""
        pass

    # Optional methods that exchanges can override

    async def get_connection_kwargs(self, symbol: str = None) -> Dict[str, Any]:
        """Get additional connection parameters for websockets.connect()"""
        kwargs = {
            'open_timeout': MONITORING_CONFIG.get('connection_timeout', 30),
            'close_timeout': 10,
            'ping_interval': None,  # We handle ping manually
            'compression': None
        }

        # Note: Proxy configuration is now handled separately in connect_with_proxy_config
        # to support both HTTP and SOCKS5 proxies properly

        return kwargs

    async def get_ping_message(self) -> Optional[str]:
        """Get ping message to send. Return None if no ping needed."""
        return None