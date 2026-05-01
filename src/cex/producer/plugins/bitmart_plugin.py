#!/usr/bin/env python3
"""
BitMart Exchange Plugin - Preserves all BitMart-specific behavior

This plugin demonstrates the power of the new architecture:
- Preserves BitMart's unique zlib compression handling
- Maintains symbol format with underscores (BTC_USDT)
- Keeps batch subscription with depth20 format
- Supports simple ping/pong protocol
- Handles full orderbook snapshots
- Reduces ~630 lines of code to ~200 lines while maintaining full functionality
"""

import sys
import os

import asyncio
import json
import time
import traceback
import zlib
from typing import Dict, List, Optional, Any

from src.cex.producer.core.base_connector import BaseExchangeConnector
from src.cex.producer.core.socks5_websocket import connect_with_proxy_config
from src.cex.producer.config import get_exchange_config, ACCEPTABLE_QUOTE_ASSETS


class BitmartConnector(BaseExchangeConnector):
    """
    BitMart exchange plugin - preserves all BitMart-specific subscription and parsing logic
    """

    # Class-level shared state for global rate limiting across all workers
    # This ensures ALL workers pause when ANY worker gets a 429
    _global_rate_limit_until: float = 0  # Timestamp when rate limit expires
    RATE_LIMIT_DELAY = 20  # Seconds to wait when 429 is detected

    def __init__(self, market_type: str = 'spot', worker_id: int = None, num_workers: int = None):
        super().__init__('bitmart', market_type, worker_id=worker_id, num_workers=num_workers)

        # BitMart-specific state
        self.subscribed_symbols: Dict[str, str] = {}  # ws_symbol -> standard_symbol mapping
        self.message_buffer: List[Dict[str, Any]] = []  # Buffer for multiple depth updates per message

        # BitMart-specific settings from original implementation
        self.depth_level = "spot/depth20"
        self.subscription_delay = 0.05  # 50ms delay between subscriptions

        self.logger.info("Initialized BitMart connector with zlib compression and batch subscription support")

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is a 429 rate limit error"""
        error_str = str(error).lower()
        return '429' in error_str or 'too many' in error_str or 'rate limit' in error_str

    async def _wait_for_rate_limit(self):
        """Wait if global rate limit is active across all workers"""
        now = time.time()
        if BitmartConnector._global_rate_limit_until > now:
            wait_time = BitmartConnector._global_rate_limit_until - now
            self.logger.warning(f"Global rate limit active, waiting {wait_time:.1f}s before connecting...")
            await asyncio.sleep(wait_time)

    async def _set_global_rate_limit(self):
        """Set global rate limit for all workers when 429 is detected"""
        BitmartConnector._global_rate_limit_until = time.time() + self.RATE_LIMIT_DELAY
        self.logger.warning(f"429 detected! Setting global rate limit for {self.RATE_LIMIT_DELAY}s (all workers will wait)")

    def decompress_data(self, data: bytes) -> Optional[str]:
        """
        Decompress zlib-compressed data from BitMart
        Preserves original decompression method
        """
        try:
            decompress = zlib.decompressobj(-zlib.MAX_WBITS)
            inflated = decompress.decompress(data)
            inflated += decompress.flush()
            return inflated.decode('UTF-8')
        except Exception as e:
            self.logger.error(f"Error decompressing data: {e}")
            return None

    def convert_to_bitmart_format(self, symbol: str) -> str:
        """
        Convert standard symbol format to BitMart WebSocket format.
        E.g., "BTCUSDT" -> "BTC_USDT"
        """
        if '_' in symbol:
            return symbol  # Already in correct format

        # Extract quote asset and convert
        for quote in ACCEPTABLE_QUOTE_ASSETS:
            if symbol.upper().endswith(quote):
                base = symbol[:-len(quote)]
                return f"{base}_{quote}"

        return symbol  # Fallback

    def convert_from_bitmart_format(self, symbol: str) -> str:
        """
        Convert BitMart WebSocket format to standard format.
        E.g., "BTC_USDT" -> "BTCUSDT"
        """
        if '_' in symbol:
            return symbol.replace('_', '')

        return symbol  # Already in standard format

    async def get_websocket_url(self, symbol: str = None) -> str:
        """Get BitMart WebSocket URL with compression parameters - matches working example"""
        return self.market_config['ws_url']

    async def get_ping_message(self) -> Optional[str]:
        """Get BitMart ping message format - simple string"""
        return "ping"

    async def subscribe_to_symbols(self, websocket, symbols: List[str]):
        """
        Subscribe to BitMart symbols one-by-one to ensure reliability.
        This matches the behavior of the original working script.
        """
        self.subscribed_symbols.clear()
        self.logger.info(f"Subscribing to {len(symbols)} symbols one by one...")

        for symbol in symbols:
            # Convert to BitMart WebSocket format
            ws_symbol = self.convert_to_bitmart_format(symbol)
            self.subscribed_symbols[ws_symbol] = symbol

            # BitMart subscription format: "spot/depth20:BTC_USDT"
            subscription_msg = {
                "op": "subscribe",
                "args": [f"{self.depth_level}:{ws_symbol}"]
            }

            await websocket.send(json.dumps(subscription_msg))
            self.logger.debug(f"Sent subscription for {symbol}")

            # Delay between subscriptions to avoid rate-limiting
            await asyncio.sleep(self.subscription_delay)

        self.logger.info(f"Finished sending subscriptions for {len(symbols)} symbols.")

    async def parse_message(self, raw_message) -> Optional[Dict[str, Any]]:
        """
        Parse BitMart WebSocket message format with zlib decompression
        Handles multiple depth updates per message using buffering
        """
        try:
            # If we have buffered messages, return the next one
            if self.message_buffer:
                return self.message_buffer.pop(0)

            # Handle compression
            if isinstance(raw_message, bytes):
                message_str = self.decompress_data(raw_message)
            else:
                message_str = raw_message

            # Skip empty messages and pong responses
            if not message_str or message_str == "pong":
                return None

            data = json.loads(message_str)

            # Handle subscription errors
            if data.get("event") == "error":
                error_msg = data.get("message", "Unknown subscription error")
                self.logger.error(f"BitMart subscription error: {error_msg}")
                # Let base connector handle error reporting
                return None

            # Process orderbook data
            if data.get("table") and "depth" in data.get("table"):
                depth_updates = data.get("data", [])

                # Process all depth updates in this message
                for depth_update in depth_updates:
                    ws_symbol = depth_update.get("symbol")

                    if ws_symbol:
                        # Convert WebSocket symbol format to standard format using conversion function
                        standard_symbol = self.convert_from_bitmart_format(ws_symbol)

                        parsed_update = {
                            'symbol': standard_symbol,
                            'timestamp_ms': depth_update.get("ms_t", int(time.time() * 1000)),
                            'bids': depth_update.get("bids", []),
                            'asks': depth_update.get("asks", []),
                            'sequence': depth_update.get("update_id", int(time.time() * 1000)),
                            'is_snapshot': True  # BitMart sends full depth snapshots
                        }

                        # Add to buffer
                        self.message_buffer.append(parsed_update)

                # Return the first update from the buffer
                if self.message_buffer:
                    return self.message_buffer.pop(0)

            # Ignore other message types
            return None

        except json.JSONDecodeError:
            return None
        except Exception as e:
            self.logger.warning(f"Failed to parse BitMart message: {e}")
            return None

    async def get_connection_kwargs(self, symbol: str = None) -> Dict[str, Any]:
        """Get BitMart-specific connection parameters"""
        kwargs = await super().get_connection_kwargs(symbol)

        # Add BitMart-specific connection settings
        kwargs.update({
            'open_timeout': 20,
            'close_timeout': 10,
            'ping_interval': None,  # Handle ping manually
            'compression': None,  # BitMart handles compression internally
        })

        return kwargs

    async def _handle_batch_connection(self, batch_id: int, symbols: List[str]):
        """
        Handle WebSocket connection for a batch of symbols with BitMart-specific rate limit handling.

        This overrides the base class method to add global rate limiting:
        - Before connecting, check if we're in a global rate limit period
        - If 429 is detected, set global rate limit for ALL workers
        """
        consecutive_failures = 0
        reconnect_delay = self.reconnect_delay_base
        batch_name = f"batch_{batch_id}"

        while not self.shutdown_event.is_set():
            try:
                # BITMART-SPECIFIC: Wait if global rate limit is active
                await self._wait_for_rate_limit()

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

                    # Start ping task if needed
                    ping_task = None
                    if self.ping_interval:
                        ping_task = asyncio.create_task(self._ping_task(websocket, batch_name))

                    # Handle messages
                    try:
                        await self._handle_messages(websocket, symbols)
                    finally:
                        if ping_task:
                            ping_task.cancel()
                finally:
                    # Always close the websocket
                    await websocket.close()

            except Exception as e:
                consecutive_failures += 1

                # Handle batch connection error with proper symbol cleanup
                error_type = type(e).__name__
                error_msg = str(e)

                self.logger.error(f"[{batch_name}] Connection error ({consecutive_failures}): {error_msg}")

                # BITMART-SPECIFIC: Check if this is a 429 rate limit error
                if self._is_rate_limit_error(e):
                    await self._set_global_rate_limit()
                    # Use rate limit delay instead of normal backoff
                    reconnect_delay = self.RATE_LIMIT_DELAY

                # Report error for all symbols in this batch
                await self.report_error(symbols, error_type, error_msg, traceback.format_exc())

                # Clean up streams and mark symbols inactive immediately on connection failure
                # Stale data is dangerous for trading calculations - better no data than wrong data
                await self._cleanup_symbols_on_failure(symbols)
                self.logger.warning(f"Cleaned up batch {batch_name} with {len(symbols)} symbols immediately on connection failure")

                # Handle proxy failover if configured
                if self._proxy_manager and consecutive_failures >= 3:
                    await self._proxy_manager.handle_connection_failure(error_type, None)

                if not self.shutdown_event.is_set():
                    await asyncio.sleep(min(reconnect_delay, self.reconnect_delay_max))
                    reconnect_delay *= 2


class BitmartSpotConnector(BitmartConnector):
    """BitMart Spot market connector"""

    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__('spot', worker_id=worker_id, num_workers=num_workers)


# Main execution function for standalone running
async def main():
    """Main function for running BitMart connector standalone"""
    from src.cex.producer.core.logging_setup import setup_standalone_logging
    from src.cex.producer.core.base_connector import parse_worker_args

    # Parse worker arguments for distributed mode
    worker_id, num_workers = parse_worker_args('BitMart Orderbook Connector')

    # Choose connector based on config
    config = get_exchange_config('bitmart')
    if not config:
        print("BitMart configuration not found!")
        return

    # Determine market type
    market_type = None
    if config.get('spot', {}).get('enabled', False):
        market_type = 'spot'
        connector_class = BitmartSpotConnector
    elif config.get('futures', {}).get('enabled', False):
        market_type = 'futures'
        connector_class = BitmartFuturesConnector
    else:
        print("No BitMart markets enabled in configuration!")
        return

    # Setup logging with file + Redis streaming
    logger, streamer = await setup_standalone_logging('bitmart', market_type)
    logger.info(f"Starting BitMart {market_type} connector...")

    # Create connector with worker params
    connector = connector_class(worker_id=worker_id, num_workers=num_workers)

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