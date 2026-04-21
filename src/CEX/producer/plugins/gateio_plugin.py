#!/usr/bin/env python3
"""
Gate.io Exchange Plugin - Preserves all Gate.io-specific behavior

This plugin demonstrates the power of the new architecture:
- Preserves Gate.io's unique subscription format with aggregation parameter
- Maintains Gate.io-specific ping/pong handling with server.ping method
- Supports Gate.io depth.update message format
- Keeps Gate.io symbol format (BTC_USDT with underscore)
- Handles subscription acknowledgment messages
- Uses original Gate.io WebSocket endpoint: wss://webws.gateio.live/v3/
- Preserves individual connection mode (1 symbol per connection)
- Reduces ~800 lines of code to ~250 lines while maintaining full functionality
"""

import sys
import os

import asyncio
import json
import time
import itertools
from typing import Dict, List, Optional, Any

from src.CEX.producer.core.base_connector import BaseExchangeConnector
from src.CEX.producer.config import get_exchange_config


class GateioConnector(BaseExchangeConnector):
    """
    Gate.io exchange plugin - preserves all Gate.io-specific subscription and parsing logic
    Supports worker distribution for scaling across multiple processes.
    """

    def __init__(self, market_type: str = 'spot', worker_id: int = None, num_workers: int = None):
        # Pass worker params to base class - it handles worker distribution automatically
        super().__init__('gateio', market_type, worker_id=worker_id, num_workers=num_workers)

        # Gate.io-specific configuration - use new WebSocket endpoint
        self.original_ws_url = "wss://spot-webws.wsbridge.com/v3?device_type=0"
        self.depth_level = 30  # WEBWS_DEPTH_LEVEL_INT from original
        self.ping_interval = 25  # Override config - original uses 25 seconds

        # Request ID counter for Gate.io messages
        self.request_id_counter = itertools.count(1)

        # Override connection type - Gate.io uses individual connections
        self.connection_type = 'individual'
        self.symbols_per_connection = 1

        # Data receipt tracking
        self.symbols_with_data = set()  # Symbols that have received data in current period
        self.last_data_log_time = time.time()
        self.data_log_interval = 60  # Log every 60 seconds

        self.logger.info(f"Initialized Gate.io connector with endpoint: {self.original_ws_url}")

    def get_next_request_id(self) -> int:
        """Get next request ID for Gate.io messages"""
        return next(self.request_id_counter)

    async def get_websocket_url(self, symbol: str = None) -> str:
        """Get Gate.io WebSocket URL - use original endpoint"""
        return self.original_ws_url

    async def get_ping_message(self) -> Optional[str]:
        """Get Gate.io ping message format"""
        ping_payload = {
            "id": self.get_next_request_id(),
            "method": "server.ping",
            "params": []
        }
        return json.dumps(ping_payload)

    async def subscribe_to_symbols(self, websocket, symbols: List[str]):
        """
        Subscribe to Gate.io symbols using Gate.io-specific subscription format
        Preserves original Gate.io subscription behavior with aggregation parameter
        """
        for symbol in symbols:
            if self.shutdown_event.is_set():
                break

            # Get aggregation level from Redis market data or use fallback
            aggregation_str = await self._get_aggregation_level(symbol)
            if not aggregation_str:
                # Try common aggregation levels for Gate.io
                # Most symbols use "0.01" or "0.1", some use "1" or "0.001"
                aggregation_str = "0.01"  # Most common default
                self.logger.debug(f"No aggregation level found for {symbol}, using default '{aggregation_str}'")

            # Gate.io subscription format - exactly as in original
            sub_id = self.get_next_request_id()
            subscribe_payload = {
                "id": sub_id,
                "method": "depth.subscribe",
                "params": [symbol, self.depth_level, aggregation_str]
            }

            await websocket.send(json.dumps(subscribe_payload))
            self.logger.debug(f"Sent subscription for {symbol} with aggregation {aggregation_str} (ID: {sub_id})")

            # Small delay between subscriptions as in original
            await asyncio.sleep(0.1)

        self.logger.info(f"Sent subscriptions for {len(symbols)} symbols")

    async def _get_aggregation_level(self, symbol: str) -> Optional[str]:
        """Get aggregation level for symbol from Redis market data"""
        try:
            # Convert symbol format for Redis lookup (BTC_USDT -> BTCUSDT)
            redis_symbol = symbol.replace('_', '')
            market_data_key = f"{self.market_type}-market-data:{self.exchange_name}"

            symbol_data_str = await self.redis_client.hget(market_data_key, redis_symbol)
            if symbol_data_str:
                # Handle both bytes and string from Redis
                if isinstance(symbol_data_str, bytes):
                    symbol_data_str = symbol_data_str.decode('utf-8')

                symbol_data = json.loads(symbol_data_str)
                aggregation_level = symbol_data.get('aggregation_level')

                # Validate aggregation level format
                if aggregation_level:
                    # Ensure it's a string and in valid format
                    aggregation_level = str(aggregation_level)
                    return aggregation_level
        except json.JSONDecodeError as e:
            self.logger.debug(f"JSON decode error for {symbol}: {e}")
        except Exception as e:
            self.logger.debug(f"Error getting aggregation level for {symbol}: {e}")

        return None

    async def parse_message(self, raw_message, symbols=None) -> Optional[Dict[str, Any]]:
        """
        Parse Gate.io WebSocket message format
        Preserves original Gate.io message structure parsing for ping/pong and orderbook data
        """
        try:
            # Parse JSON message
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing Gate.io JSON message: {e}")
                return None

            # Handle pong responses to our ping
            msg_id = message.get("id")
            if msg_id and message.get("result") == "pong":
                self.logger.debug(f"Received pong response for ping ID {msg_id}")
                return None

            # Handle subscription acknowledgments
            if msg_id and "result" in message:
                if message.get("error") is None and message.get("result", {}).get("status") == "success":
                    self.logger.debug(f"Subscription acknowledged for ID {msg_id}")
                else:
                    error_msg = f"Subscription failed for ID {msg_id}: {message}"
                    self.logger.error(error_msg)
                    # Raise exception to trigger reconnection when subscription fails
                    raise Exception(f"Gate.io subscription failed: {message}")
                return None

            # Handle server error messages
            if message.get("method") == "server.error" or message.get("event") == "error":
                error_details = message.get("params", [{}])
                if isinstance(error_details, list) and error_details:
                    error_msg = error_details[0].get("message", str(message))
                else:
                    error_msg = str(message)
                self.logger.error(f"Gate.io server error: {error_msg}")
                return None

            # Handle depth updates
            if message.get("method") == "depth.update" and message.get("id") is None:
                params = message.get("params")
                if isinstance(params, list) and len(params) == 3:
                    is_snapshot, data_obj, symbol_from_data = params

                    if not isinstance(data_obj, dict):
                        return None

                    # Only process if this symbol is in our subscription list
                    if symbols and symbol_from_data not in symbols:
                        self.logger.debug(f"Received data for unsubscribed symbol: {symbol_from_data}")
                        return None

                    # Convert Gate.io orderbook format to standard format
                    bids = data_obj.get('bids', [])
                    asks = data_obj.get('asks', [])

                    # Gate.io provides timestamp in 'current' field
                    timestamp_ms = int(data_obj.get('current', time.time()) * 1000)

                    # Convert symbol for Redis storage (BTC_USDT -> BTCUSDT)
                    clean_symbol = symbol_from_data.replace('_', '')

                    # Track that this symbol received data
                    self.symbols_with_data.add(clean_symbol)

                    # Check if it's time to log data receipt status
                    current_time = time.time()
                    if current_time - self.last_data_log_time >= self.data_log_interval:
                        active_count = len(self.symbols_with_data)
                        total_count = len(self.currently_monitored_symbols)
                        sample_symbols = list(self.symbols_with_data)[:5]
                        self.logger.info(
                            f"📊 Data received in last minute for {active_count}/{total_count} symbols. "
                            f"Samples: {sample_symbols}{'...' if active_count > 5 else ''}"
                        )
                        # Reset tracking for next period
                        self.symbols_with_data.clear()
                        self.last_data_log_time = current_time

                    return {
                        'symbol': clean_symbol,  # Remove underscore for Redis storage
                        'timestamp_ms': timestamp_ms,
                        'bids': bids,
                        'asks': asks,
                        'sequence': data_obj.get('id', timestamp_ms),  # Use Gate.io's id field
                        'is_snapshot': is_snapshot
                    }

            return None

        except Exception as e:
            self.logger.warning(f"Failed to parse Gate.io message: {e}")
            return None

    async def _handle_messages(self, websocket, symbols: List[str]):
        """Handle incoming WebSocket messages with Gate.io-specific handling"""
        try:
            async for message in websocket:
                if self.shutdown_event.is_set():
                    break

                try:
                    # Parse message using Gate.io-specific implementation
                    parsed_data = await self.parse_message(message, symbols)

                    if parsed_data:
                        # Regular orderbook data, process normally
                        await self._process_orderbook_data(parsed_data)

                except Exception as e:
                    self.logger.error(f"Error processing Gate.io message: {e}")
                    await self.report_error(symbols, "MessageProcessingError", str(e))

        except Exception as e:
            self.logger.error(f"Error in Gate.io message handling: {e}")
            raise

    async def get_connection_kwargs(self, symbol: str = None) -> Dict[str, Any]:
        """Get Gate.io-specific connection parameters with browser-like headers"""
        kwargs = await super().get_connection_kwargs(symbol)

        # Add Gate.io-specific connection settings
        kwargs.update({
            'open_timeout': 20,
            'close_timeout': 10,
            'ping_interval': None,  # We handle ping manually
            'compression': None,
        })

        # Browser-like headers to avoid bot detection (websockets 15.0+ uses additional_headers)
        kwargs['additional_headers'] = {
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Origin': 'https://www.gate.com',
            'Pragma': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36'
        }

        return kwargs

    async def _handle_symbol_connection(self, symbol: str):
        """
        Override to add IP logging for debugging Gate.io connection issues
        Helps identify which IPs are getting rate limited (429 errors)
        """
        consecutive_failures = 0
        reconnect_delay = self.reconnect_delay_base

        while not self.shutdown_event.is_set():
            # Determine which IP will be used for this connection attempt BEFORE connecting
            attempted_ip = "unknown"
            try:
                # Extract proxy configuration to determine IP
                proxy_config = None
                if self._proxy_manager:
                    proxy_config = await self._proxy_manager.get_connection_params(symbol)

                # Determine the IP that will be used for this attempt
                if proxy_config and isinstance(proxy_config, dict):
                    # Using proxy - extract proxy host/IP
                    attempted_ip = proxy_config.get('host', 'unknown')
                    # If there's an exit_ip field, use that (more accurate)
                    if 'exit_ip' in proxy_config:
                        attempted_ip = proxy_config.get('exit_ip', attempted_ip)
                else:
                    attempted_ip = "direct"

                self.logger.info(f"[{symbol}] Connecting from IP: {attempted_ip} (failures: {consecutive_failures})...")

                # Get connection parameters
                ws_url = await self.get_websocket_url(symbol)
                connect_kwargs = await self.get_connection_kwargs(symbol)

                from src.CEX.producer.core.socks5_websocket import connect_with_proxy_config
                websocket = await connect_with_proxy_config(ws_url, proxy_config, **connect_kwargs)

                try:
                    # Connection successful - log with the IP used
                    self.logger.info(f"[{symbol}] ✅ Connected successfully from IP: {attempted_ip}")
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

                    # Start ping task if needed
                    ping_task = None
                    if self.ping_interval:
                        ping_task = asyncio.create_task(self._ping_task(websocket, symbol))

                    # Handle messages
                    try:
                        await self._handle_messages(websocket, [symbol])
                    finally:
                        if ping_task:
                            ping_task.cancel()
                finally:
                    # Always close the websocket
                    await websocket.close()

            except Exception as e:
                consecutive_failures += 1
                error_msg = str(e)

                # Enhanced error logging for rate limiting - now includes the IP that got rejected
                if '429' in error_msg or 'rate limit' in error_msg.lower():
                    self.logger.warning(f"[{symbol}] ⚠️  Rate limited (429) - connection rejected from {attempted_ip}")
                else:
                    self.logger.error(f"[{symbol}] ❌ Connection failed from {attempted_ip}: {error_msg}")

                await self._handle_connection_error(symbol, e, consecutive_failures)

                if not self.shutdown_event.is_set():
                    await asyncio.sleep(min(reconnect_delay, self.reconnect_delay_max))
                    reconnect_delay *= 2

    async def get_symbols_to_monitor(self) -> List[str]:
        """
        Override to get Gate.io symbols, sort by volume, and convert to underscore format

        Gate.io has connection limit (~2350 from same IP), so we prioritize high-volume symbols.
        This ensures we connect to the most important/liquid symbols first.
        """
        # Get symbols from base method (returns BTCUSDT format)
        redis_symbols = await super().get_symbols_to_monitor()

        # Enrich symbols with volume data
        symbol_volumes = []
        for symbol in redis_symbols:
            volume = await self._get_symbol_volume(symbol)
            symbol_volumes.append((symbol, volume))

        # Sort by volume descending (highest volume first)
        symbol_volumes.sort(key=lambda x: x[1], reverse=True)

        self.logger.info(
            f"Sorted {len(symbol_volumes)} symbols by 24h volume. "
            f"Top 3: {[(s, f'{v:,.0f}') for s, v in symbol_volumes[:3]]}"
        )

        # Convert to Gate.io WebSocket format (BTC_USDT)
        gateio_symbols = []
        for symbol, volume in symbol_volumes:
            gateio_symbol = self._convert_to_gateio_format(symbol)
            gateio_symbols.append(gateio_symbol)

        # Note: Worker filtering is done automatically by base class in start()
        # after this method returns, so we don't need to call _filter_symbols_for_worker() here

        return gateio_symbols

    async def _get_symbol_volume(self, symbol: str) -> float:
        """
        Get 24h trading volume in USDT for a symbol from Redis

        Returns:
            24h_volume_usdt as float, or 0.0 if not found
        """
        try:
            market_data_key = f"{self.market_type}-market-data:{self.exchange_name}"
            symbol_data_str = await self.redis_client.hget(market_data_key, symbol)

            if symbol_data_str:
                # Handle bytes if Redis returns bytes instead of string
                if isinstance(symbol_data_str, bytes):
                    symbol_data_str = symbol_data_str.decode('utf-8')

                symbol_data = json.loads(symbol_data_str)

                # Try different field names for 24h volume
                volume = (
                    symbol_data.get('24h_volume_usdt') or
                    symbol_data.get('volume_24h_usdt') or
                    symbol_data.get('volume_usdt') or
                    symbol_data.get('volume') or
                    0.0
                )

                return float(volume)

            return 0.0

        except Exception as e:
            self.logger.debug(f"Error getting volume for {symbol}: {e}")
            return 0.0

    def _convert_to_gateio_format(self, redis_symbol: str) -> str:
        """
        Convert Redis symbol format to Gate.io WebSocket format
        BTCUSDT -> BTC_USDT
        """
        # Most symbols end with USDT, USDC, etc.
        from src.CEX.producer.config import ACCEPTABLE_QUOTE_ASSETS

        symbol_upper = redis_symbol.upper()
        for quote in ACCEPTABLE_QUOTE_ASSETS:
            if symbol_upper.endswith(quote):
                base = symbol_upper[:-len(quote)]
                return f"{base}_{quote}"

        # Fallback: if no quote found, assume last 4 chars are quote
        if len(redis_symbol) > 4:
            base = redis_symbol[:-4]
            quote = redis_symbol[-4:]
            return f"{base}_{quote}"

        # If symbol is too short, return as-is
        return redis_symbol

    def _normalize_symbol_for_redis(self, symbol: str) -> str:
        """
        Normalize symbol to Redis format (remove underscore)
        BTC_USDT -> BTCUSDT
        BTCUSDT -> BTCUSDT
        """
        return symbol.replace('_', '')

    # Note: _filter_symbols_for_worker() is inherited from BaseExchangeConnector
    # and is called automatically in start() after get_symbols_to_monitor()

    async def _mark_symbol_active(self, symbol: str):
        """Override to normalize symbol before marking active"""
        normalized_symbol = self._normalize_symbol_for_redis(symbol)
        await super()._mark_symbol_active(normalized_symbol)

    async def _mark_symbol_inactive(self, symbol: str):
        """Override to normalize symbol before marking inactive"""
        normalized_symbol = self._normalize_symbol_for_redis(symbol)
        await super()._mark_symbol_inactive(normalized_symbol)

    async def _delete_symbol_stream(self, symbol: str):
        """Override to normalize symbol before deleting stream"""
        normalized_symbol = self._normalize_symbol_for_redis(symbol)
        await super()._delete_symbol_stream(normalized_symbol)

    async def get_current_market_symbols(self) -> set:
        """
        Override to get symbols from Redis and convert to Gate.io format
        Ensures consistency with get_symbols_to_monitor() format
        """
        # Get symbols from Redis (BTCUSDT format)
        redis_symbols = await super().get_current_market_symbols()

        # Convert to Gate.io WebSocket format (BTC_USDT)
        gateio_symbols = set()
        for symbol in redis_symbols:
            gateio_symbol = self._convert_to_gateio_format(symbol)
            gateio_symbols.add(gateio_symbol)

        return gateio_symbols


class GateioSpotConnector(GateioConnector):
    """Gate.io Spot market connector with optional worker distribution"""

    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__('spot', worker_id=worker_id, num_workers=num_workers)


class GateioFuturesConnector(GateioConnector):
    """Gate.io Futures market connector"""

    def __init__(self):
        super().__init__('futures')

    async def subscribe_to_symbols(self, websocket, symbols: List[str]):
        """Futures subscription logic (if different from spot)"""
        # For now, use same logic as spot
        # This can be customized if futures have different subscription requirements
        await super().subscribe_to_symbols(websocket, symbols)


# Main execution function for standalone running
async def main():
    """Main function for running Gate.io connector standalone with optional worker distribution"""
    from src.CEX.producer.core.base_connector import parse_worker_args
    from src.CEX.producer.core.logging_setup import setup_standalone_logging

    # Parse worker args using standard utility from base class
    worker_id, num_workers = parse_worker_args('Gate.io Orderbook Connector')

    # Choose connector based on config
    config = get_exchange_config('gateio')
    if not config:
        print("Gate.io configuration not found!")
        return

    # Determine market type
    market_type = None
    if config.get('spot', {}).get('enabled', False):
        market_type = 'spot'
    elif config.get('futures', {}).get('enabled', False):
        market_type = 'futures'
    else:
        print("No Gate.io markets enabled in configuration!")
        return

    # Setup logging with worker suffix if in distributed mode
    log_suffix = f"_w{worker_id}" if worker_id is not None else ""
    logger, streamer = await setup_standalone_logging('gateio', f"{market_type}{log_suffix}")

    if worker_id is not None:
        logger.info(f"Starting Gate.io {market_type} - Worker {worker_id + 1}/{num_workers}")
    else:
        logger.info(f"Starting Gate.io {market_type} connector (single process mode)...")

    # Create connector with worker config
    if market_type == 'spot':
        connector = GateioSpotConnector(
            worker_id=worker_id,
            num_workers=num_workers
        )
    else:
        # Futures doesn't support workers yet
        connector = GateioFuturesConnector()

    try:
        await connector.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Stop Redis log streaming
        if streamer:
            try:
                await streamer.stop()
            except Exception as e:
                logger.error(f"Error stopping log streamer: {e}")

        await connector.cleanup()


if __name__ == "__main__":
    asyncio.run(main())