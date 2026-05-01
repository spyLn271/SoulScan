#!/usr/bin/env python3
"""
HTX Exchange Plugin - Preserves all HTX-specific behavior

This plugin demonstrates the power of the new architecture:
- Preserves HTX's unique gzip compression for all WebSocket messages
- Maintains HTX-specific ping/pong handling with timestamp exchange
- Supports HTX subscription format with market.{symbol}.depth.step0
- Keeps HTX symbol format (lowercase) and channel parsing logic
- Handles HTX-specific error responses with status field
- Uses original HTX WebSocket endpoint: wss://www.htx.com/-/s/pro/ws
- Reduces ~500 lines of code to ~200 lines while maintaining full functionality
"""

import sys
import os

import asyncio
import json
import time
import gzip
from typing import Dict, List, Optional, Any

from src.cex.producer.core.base_connector import BaseExchangeConnector
from src.cex.producer.config import get_exchange_config


class HtxConnector(BaseExchangeConnector):
    """
    HTX exchange plugin - preserves all HTX-specific subscription and parsing logic
    """

    def __init__(self, market_type: str = 'spot', worker_id: int = None, num_workers: int = None):
        super().__init__('htx', market_type, worker_id=worker_id, num_workers=num_workers)

        # HTX-specific configuration - use original WebSocket URL
        self.original_ws_url = "wss://www.htx.com/-/s/pro/ws"

        self.logger.info(f"Initialized HTX connector with original endpoint: {self.original_ws_url}")

    async def get_websocket_url(self, symbol: str = None) -> str:
        """Get HTX WebSocket URL - use original endpoint"""
        return self.original_ws_url

    async def get_ping_message(self) -> Optional[str]:
        """HTX doesn't send pings - server sends pings to us"""
        return None

    async def subscribe_to_symbols(self, websocket, symbols: List[str]):
        """
        Subscribe to HTX symbols using HTX-specific subscription format
        Preserves original HTX subscription behavior with market.{symbol}.depth.step0

        Note: Converts symbols to lowercase for HTX API compatibility
        """
        for symbol in symbols:
            if self.shutdown_event.is_set():
                break

            # HTX requires lowercase symbols in subscription messages
            lowercase_symbol = symbol.lower()

            # HTX subscription format - exactly as in original
            sub_payload = {
                "sub": f"market.{lowercase_symbol}.depth.step0",
                "id": f"htx-{lowercase_symbol}-{int(time.time())}"
            }

            await websocket.send(json.dumps(sub_payload))
            self.logger.debug(f"Sent subscription for {symbol} (as {lowercase_symbol})")

        self.logger.info(f"Sent subscriptions for {len(symbols)} symbols")

    async def parse_message(self, raw_message, symbols=None) -> Optional[Dict[str, Any]]:
        """
        Parse HTX WebSocket message format with gzip decompression
        Preserves original HTX message structure parsing for both ping/pong and orderbook data
        """
        try:
            # All HTX messages are gzip compressed - decompress first
            try:
                decompressed_message = gzip.decompress(raw_message)
                data = json.loads(decompressed_message.decode('utf-8'))
            except Exception as e:
                self.logger.error(f"Error decompressing/decoding HTX message: {e}")
                return None

            # Handle ping messages - server sends ping, we respond with pong
            if 'ping' in data:
                return {
                    'type': 'ping_response',
                    'response': json.dumps({'pong': data['ping']})
                }

            # Handle subscription error responses
            if 'status' in data and data.get('status') == 'error':
                error_msg = data.get('err-msg', 'Unknown subscription error')
                self.logger.error(f"HTX subscription error: {error_msg}. Full message: {data}")
                return None

            # Handle orderbook data
            if 'ch' in data and 'tick' in data:
                # Extract symbol from channel - HTX format: market.{symbol}.depth.step0
                try:
                    symbol_from_channel = data['ch'].split('.')[1]
                except (IndexError, AttributeError):
                    self.logger.warning(f"Could not extract symbol from HTX channel: {data.get('ch')}")
                    return None

                # Only process if this symbol is in our subscription list
                # Convert to uppercase for comparison since our symbols list is now uppercase
                if symbols and symbol_from_channel.upper() not in symbols:
                    self.logger.debug(f"Received data for unsubscribed symbol: {symbol_from_channel}")
                    return None

                tick_data = data.get('tick', {})
                if not tick_data:
                    return None

                # Convert HTX orderbook format to standard format
                bids = tick_data.get('bids', [])
                asks = tick_data.get('asks', [])

                # HTX provides timestamp
                timestamp_ms = data.get('ts', int(time.time() * 1000))

                return {
                    'symbol': symbol_from_channel.upper(),  # Capitalize for Redis storage
                    'timestamp_ms': timestamp_ms,
                    'bids': bids,
                    'asks': asks,
                    'sequence': tick_data.get('version', timestamp_ms),  # Use version or timestamp
                    'is_snapshot': True  # HTX sends full snapshots
                }

            return None

        except Exception as e:
            self.logger.warning(f"Failed to parse HTX message: {e}")
            return None

    async def _handle_messages(self, websocket, symbols: List[str]):
        """Handle incoming WebSocket messages with HTX-specific ping/pong support"""
        try:
            async for message in websocket:
                if self.shutdown_event.is_set():
                    break

                try:
                    # Parse message using HTX-specific implementation
                    parsed_data = await self.parse_message(message, symbols)

                    if parsed_data:
                        # Handle ping responses separately
                        if parsed_data.get('type') == 'ping_response':
                            await websocket.send(parsed_data['response'])
                            self.logger.debug(f"Sent pong response to HTX ping")
                        else:
                            # Regular orderbook data, process normally
                            await self._process_orderbook_data(parsed_data)

                except Exception as e:
                    self.logger.error(f"Error processing HTX message: {e}")
                    await self.report_error(symbols, "MessageProcessingError", str(e))

        except Exception as e:
            self.logger.error(f"Error in HTX message handling: {e}")
            raise

    async def get_symbols_to_monitor(self) -> List[str]:
        """
        Get list of symbols to monitor from Redis, normalized to uppercase

        HTX stores symbols as lowercase in Redis but we need uppercase for consistent
        Redis state management (active/inactive symbol tracking)
        """
        # Get symbols from base implementation (lowercase from Redis)
        symbols = await super().get_symbols_to_monitor()

        # Convert all symbols to uppercase for consistent Redis state management
        uppercase_symbols = [symbol.upper() for symbol in symbols]

        self.logger.debug(f"Normalized {len(symbols)} symbols from lowercase to uppercase")
        return uppercase_symbols

    async def get_current_market_symbols(self) -> set:
        """
        Get current symbols from market data Redis, normalized to uppercase

        Used by dynamic symbol monitoring to detect new/removed symbols.
        Ensures consistency with get_symbols_to_monitor() for proper state management.
        """
        # Get symbols from base implementation (lowercase from Redis)
        symbols = await super().get_current_market_symbols()

        # Convert all symbols to uppercase for consistent Redis state management
        uppercase_symbols = {symbol.upper() for symbol in symbols}

        self.logger.debug(f"Normalized {len(symbols)} current market symbols from lowercase to uppercase")
        return uppercase_symbols

    async def get_connection_kwargs(self, symbol: str = None) -> Dict[str, Any]:
        """Get HTX-specific connection parameters"""
        kwargs = await super().get_connection_kwargs(symbol)

        # Add HTX-specific connection settings
        kwargs.update({
            'open_timeout': 30,
            'close_timeout': 10,
            'ping_interval': None,  # HTX server sends pings to us
            'compression': None,    # No websockets compression (HTX uses gzip internally)
        })

        return kwargs


class HtxSpotConnector(HtxConnector):
    """HTX Spot market connector"""

    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__('spot', worker_id=worker_id, num_workers=num_workers)


class HtxFuturesConnector(HtxConnector):
    """HTX Futures market connector"""

    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__('futures', worker_id=worker_id, num_workers=num_workers)

    async def subscribe_to_symbols(self, websocket, symbols: List[str]):
        """Futures subscription logic (if different from spot)"""
        # For now, use same logic as spot
        # This can be customized if futures have different subscription requirements
        await super().subscribe_to_symbols(websocket, symbols)


# Main execution function for standalone running
async def main():
    """Main function for running HTX (Huobi) connector standalone"""
    from src.cex.producer.core.logging_setup import setup_standalone_logging
    from src.cex.producer.core.base_connector import parse_worker_args

    # Parse worker arguments for distributed mode
    worker_id, num_workers = parse_worker_args('HTX Orderbook Connector')

    # Choose connector based on config
    config = get_exchange_config('htx')
    if not config:
        print("HTX (Huobi) configuration not found!")
        return

    # Determine market type
    market_type = None
    if config.get('spot', {}).get('enabled', False):
        market_type = 'spot'
        connector_class = HtxSpotConnector
    elif config.get('futures', {}).get('enabled', False):
        market_type = 'futures'
        connector_class = HtxFuturesConnector
    else:
        print("No HTX (Huobi) markets enabled in configuration!")
        return

    # Setup logging with file + Redis streaming
    logger, streamer = await setup_standalone_logging('htx', market_type)
    logger.info(f"Starting HTX (Huobi) {market_type} connector...")

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