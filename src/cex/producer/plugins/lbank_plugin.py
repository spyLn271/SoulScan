#!/usr/bin/env python3
"""
LBank Exchange Plugin - Preserves all LBank-specific behavior

This plugin demonstrates the power of the new architecture:
- Preserves LBank's unique symbol format with lowercase and underscores
- Maintains custom ping/pong protocol (server-initiated)
- Keeps individual subscription format per symbol
- Supports depth data without snapshot/delta complexity
- Reduces ~650 lines of code to ~200 lines while maintaining full functionality
"""

import sys
import os

import asyncio
import json
import time
import traceback
import websockets
from typing import Dict, List, Optional, Any

from src.cex.producer.core.base_connector import BaseExchangeConnector
from src.cex.producer.config import get_exchange_config


class LbankConnector(BaseExchangeConnector):
    """
    LBank exchange plugin - preserves all LBank-specific subscription and parsing logic
    """

    def __init__(self, market_type: str = 'spot', worker_id: int = None, num_workers: int = None):
        super().__init__('lbank', market_type, worker_id=worker_id, num_workers=num_workers)

        # LBank-specific state
        self.subscribed_symbols: Dict[str, str] = {}  # ws_symbol -> standard_symbol mapping
        self.pending_pong_data: Optional[str] = None  # For ping/pong tracking

        # LBank-specific settings from original implementation
        self.depth_level = "50"
        self.subscription_delay = 0.25  # 250ms delay between subscriptions

        self.logger.info("Initialized LBank connector with custom ping/pong and symbol format conversion")

    def convert_to_lbank_format(self, symbol: str) -> str:
        """
        Convert standard symbol format to LBank WebSocket format.
        LBank uses lowercase with underscore: "BTCUSDT" -> "btc_usdt"
        """
        # If it already contains an underscore, assume it's in the correct format
        if '_' in symbol:
            return symbol.lower()

        if '/' in symbol:
            # Handle "BTC/USDT" format
            base, quote = symbol.split('/')
            return f"{base.lower()}_{quote.lower()}"

        # Handle "BTCUSDT" format - extract quote asset
        symbol_upper = symbol.upper()
        from src.cex.producer.config import ACCEPTABLE_QUOTE_ASSETS

        for quote in ACCEPTABLE_QUOTE_ASSETS:
            if symbol_upper.endswith(quote):
                base = symbol_upper[:-len(quote)]
                return f"{base.lower()}_{quote.lower()}"

        # Fallback - just lowercase
        return symbol.lower()

    def convert_from_lbank_format(self, ws_symbol: str) -> str:
        """
        Convert LBank WebSocket format to standard format.
        E.g., "btc_usdt" -> "BTCUSDT"
        """
        if '_' in ws_symbol:
            base, quote = ws_symbol.split('_')
            return f"{base.upper()}{quote.upper()}"

        return ws_symbol.upper()

    async def get_websocket_url(self, symbol: str = None) -> str:
        """Get LBank WebSocket URL - preserves original endpoint"""
        return self.market_config['ws_url']

    async def get_ping_message(self) -> Optional[str]:
        """
        LBank uses server-initiated ping/pong, so we don't send pings
        Return None to indicate no manual ping needed
        """
        return None

    async def subscribe_to_symbols(self, websocket, symbols: List[str]):
        """
        Subscribe to LBank symbols using individual subscription format
        Preserves original LBank individual subscription behavior
        """
        self.subscribed_symbols.clear()

        for symbol in symbols:
            # Convert to LBank WebSocket format
            ws_symbol = self.convert_to_lbank_format(symbol)
            self.subscribed_symbols[ws_symbol] = symbol

            # LBank individual subscription format
            subscription_msg = {
                "action": "subscribe",
                "subscribe": "depth",
                "depth": self.depth_level,
                "pair": ws_symbol
            }

            await websocket.send(json.dumps(subscription_msg))
            self.logger.debug(f"Subscribed to {symbol} as {ws_symbol}")

            # Add delay between subscriptions to avoid overwhelming the server
            await asyncio.sleep(self.subscription_delay)

        self.logger.info(f"Sent individual subscriptions for {len(symbols)} symbols")

    async def parse_message(self, raw_message) -> Optional[Dict[str, Any]]:
        """
        Parse LBank WebSocket message format
        Handles custom ping/pong and depth updates
        """
        try:
            # LBank sends text messages (no compression)
            if isinstance(raw_message, bytes):
                msg_str = raw_message.decode('utf-8')
            else:
                msg_str = raw_message

            data = json.loads(msg_str)
            action = data.get("action")

            # Handle LBank's custom PING/PONG protocol
            if action == "ping":
                # Store pong data for response - this will be handled by base connector
                ping_value = data.get("ping")
                if ping_value is not None:
                    self.pending_pong_data = ping_value
                    # Return a special message type to trigger pong response
                    return {
                        '_internal_action': 'send_pong',
                        'pong_data': ping_value
                    }

            # Handle subscription errors
            if action == "error" or "error" in data:
                error_msg = data.get("message", str(data))
                self.logger.error(f"LBank subscription error: {error_msg}")
                # Let base connector handle error reporting
                return None

            # Process depth data
            if "depth" in data and "pair" in data:
                ws_pair = data.get("pair")

                if ws_pair in self.subscribed_symbols:
                    standard_symbol = self.subscribed_symbols[ws_pair]
                    depth_data = data["depth"]
                    timestamp_ms = int(time.time() * 1000)  # LBank doesn't provide timestamp

                    return {
                        'symbol': standard_symbol,
                        'timestamp_ms': timestamp_ms,
                        'bids': depth_data.get("bids", []),
                        'asks': depth_data.get("asks", []),
                        'sequence': timestamp_ms,  # Use timestamp as sequence
                        'is_snapshot': True  # LBank sends full depth, not incremental
                    }

            # Ignore other message types
            return None

        except json.JSONDecodeError:
            return None
        except Exception as e:
            self.logger.warning(f"Failed to parse LBank message: {e}")
            return None

    async def _handle_messages(self, websocket, symbols: List[str]):
        """Handle LBank messages with custom ping/pong and stale stream detection"""
        from src.cex.producer.core.base_connector import StaleStreamError
        last_data_time = time.time()

        try:
            while not self.shutdown_event.is_set():
                try:
                    message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=self.stale_stream_timeout
                    )
                except asyncio.TimeoutError:
                    elapsed = time.time() - last_data_time
                    if elapsed >= self.stale_stream_timeout:
                        raise StaleStreamError(self.stale_stream_timeout, last_data_time)
                    continue

                try:
                    # Parse message using exchange-specific implementation
                    parsed_data = await self.parse_message(message)

                    if parsed_data:
                        # Handle special internal actions - DO NOT reset timer for pongs
                        if parsed_data.get('_internal_action') == 'send_pong':
                            pong_msg = {
                                "action": "pong",
                                "pong": parsed_data['pong_data']
                            }
                            await websocket.send(json.dumps(pong_msg))
                            self.logger.debug(f"Responded to PING with PONG: {parsed_data['pong_data']}")
                            continue

                        # Process normal orderbook data and reset timer
                        await self._process_orderbook_data(parsed_data)
                        last_data_time = time.time()

                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
                    await self.report_error(symbols, "MessageProcessingError", str(e))

        except StaleStreamError:
            self.logger.warning(f"Stale stream detected - no data for {self.stale_stream_timeout}s, reconnecting...")
            raise
        except Exception as e:
            self.logger.error(f"Error in LBank message handling: {e}")
            raise

    async def _handle_symbol_connection(self, symbol: str):
        """Handle WebSocket connection for a single symbol (override to use custom message handler)"""
        consecutive_failures = 0
        reconnect_delay = self.reconnect_delay_base

        while not self.shutdown_event.is_set():
            try:
                self.logger.info(f"[{symbol}] Connecting (failures: {consecutive_failures})...")

                # Get connection parameters (with proxy if needed)
                ws_url = await self.get_websocket_url(symbol)
                connect_kwargs = await self.get_connection_kwargs(symbol)

                async with websockets.connect(ws_url, **connect_kwargs) as websocket:
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

                    # Handle messages with LBank-specific ping/pong
                    try:
                        await self._handle_messages(websocket, [symbol])
                    finally:
                        pass  # No ping task to cancel for LBank

            except Exception as e:
                consecutive_failures += 1
                await self._handle_connection_error(symbol, e, consecutive_failures)

                if not self.shutdown_event.is_set():
                    await asyncio.sleep(min(reconnect_delay, self.reconnect_delay_max))
                    reconnect_delay *= 2

    async def _handle_batch_connection(self, batch_id: int, symbols: List[str]):
        """Handle WebSocket connection for a batch of symbols (override to use custom message handler)"""
        consecutive_failures = 0
        reconnect_delay = self.reconnect_delay_base
        batch_name = f"batch_{batch_id}"

        while not self.shutdown_event.is_set():
            try:
                self.logger.info(f"[{batch_name}] Connecting with {len(symbols)} symbols...")

                # Get connection parameters
                ws_url = await self.get_websocket_url()
                connect_kwargs = await self.get_connection_kwargs()

                async with websockets.connect(ws_url, **connect_kwargs) as websocket:
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

                    # Handle messages with LBank-specific ping/pong
                    try:
                        await self._handle_messages(websocket, symbols)
                    finally:
                        pass  # No ping task to cancel for LBank

            except Exception as e:
                consecutive_failures += 1

                # Handle batch connection error with proper symbol cleanup
                error_type = type(e).__name__
                error_msg = str(e)

                self.logger.error(f"[{batch_name}] Connection error ({consecutive_failures}): {error_msg}")

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

    async def get_connection_kwargs(self, symbol: str = None) -> Dict[str, Any]:
        """Get LBank-specific connection parameters"""
        kwargs = await super().get_connection_kwargs(symbol)

        # Add LBank-specific connection settings
        kwargs.update({
            'open_timeout': 20,
            'close_timeout': 10,
            'ping_interval': None,  # LBank handles ping/pong manually
        })

        return kwargs


class LbankSpotConnector(LbankConnector):
    """LBank Spot market connector"""

    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__('spot', worker_id=worker_id, num_workers=num_workers)


# Main execution function for standalone running
async def main():
    """Main function for running LBank connector standalone"""
    from src.cex.producer.core.logging_setup import setup_standalone_logging
    from src.cex.producer.core.base_connector import parse_worker_args

    # Parse worker arguments for distributed mode
    worker_id, num_workers = parse_worker_args('LBank Orderbook Connector')

    # Choose connector based on config
    config = get_exchange_config('lbank')
    if not config:
        print("LBank configuration not found!")
        return

    # Determine market type
    market_type = None
    if config.get('spot', {}).get('enabled', False):
        market_type = 'spot'
        connector_class = LbankSpotConnector
    elif config.get('futures', {}).get('enabled', False):
        market_type = 'futures'
        connector_class = LbankFuturesConnector
    else:
        print("No LBank markets enabled in configuration!")
        return

    # Setup logging with file + Redis streaming
    logger, streamer = await setup_standalone_logging('lbank', market_type)
    logger.info(f"Starting LBank {market_type} connector...")

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