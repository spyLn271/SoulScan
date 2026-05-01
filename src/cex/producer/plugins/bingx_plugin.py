#!/usr/bin/env python3
"""
BingX Exchange Plugin - Preserves all BingX-specific behavior

This plugin demonstrates the power of the new architecture:
- Preserves BingX's unique symbol format conversion (BTCUSDT <-> BTC-USDT)
- Maintains dual ping/pong handling (string and idl formats)
- Supports gzip decompression for compressed messages
- Keeps BingX-specific subscription format with UUID and reqType
- Reduces ~800 lines of code to ~200 lines while maintaining full functionality
"""

import sys
import os

import asyncio
import json
import time
import uuid
import gzip
import io
from typing import Dict, List, Optional, Any

from src.cex.producer.core.base_connector import BaseExchangeConnector
from src.cex.producer.config import get_exchange_config


class BingxConnector(BaseExchangeConnector):
    """
    BingX exchange plugin - preserves all BingX-specific subscription and parsing logic
    """

    def __init__(self, market_type: str = 'spot', worker_id: int = None, num_workers: int = None):
        super().__init__('bingx', market_type, worker_id=worker_id, num_workers=num_workers)

        # BingX-specific configuration
        self.depth_level = 50  # BingX uses depth50 for spot markets
        self.update_interval_ms = 200  # For futures, ignored for spot

        self.logger.info(f"Initialized BingX connector with depth level {self.depth_level}")

    async def get_websocket_url(self, symbol: str = None) -> str:
        """Get BingX WebSocket URL"""
        return self.market_config['ws_url']

    async def get_ping_message(self) -> Optional[str]:
        """BingX sends ping to us, we don't need to send ping"""
        return None

    async def subscribe_to_symbols(self, websocket, symbols: List[str]):
        """
        Subscribe to BingX symbols using BingX-specific subscription format
        Preserves original BingX subscription behavior with UUID and reqType
        """
        subscription_payloads = []
        for redis_symbol in symbols:
            # Convert Redis symbol format to BingX WebSocket format
            bingx_ws_symbol = self._convert_to_bingx_format(redis_symbol)

            # Create BingX-specific subscription payload
            data_type_str = f"{bingx_ws_symbol}@depth{self.depth_level}"
            if self.market_type == 'futures':
                data_type_str = f"{bingx_ws_symbol}@depth{self.depth_level}@{self.update_interval_ms}ms"

            subscription_payloads.append({
                "id": str(uuid.uuid4()),
                "reqType": "sub",
                "dataType": data_type_str
            })

        # Send all subscriptions
        for i, sub_payload in enumerate(subscription_payloads):
            await websocket.send(json.dumps(sub_payload))
            if i % 5 == 0:  # Log every 5th subscription
                self.logger.debug(f"Subscribed to {i+1}/{len(subscription_payloads)} symbols")
            await asyncio.sleep(0.01)  # Small delay between subscriptions

        self.logger.info(f"Sent subscriptions for {len(symbols)} symbols with depth level {self.depth_level}")

    async def parse_message(self, raw_message) -> Optional[Dict[str, Any]]:
        """
        Parse BingX WebSocket message format with gzip decompression
        Preserves original BingX message structure parsing and ping/pong handling
        """
        try:
            # Handle gzip compression
            if isinstance(raw_message, bytes):
                try:
                    utf8_data_str = gzip.GzipFile(fileobj=io.BytesIO(raw_message), mode='rb').read().decode('utf-8')
                except Exception:
                    utf8_data_str = raw_message.decode(errors='ignore')
            else:
                utf8_data_str = raw_message

            # Handle string ping messages
            if utf8_data_str.lower() == "ping":
                # BingX expects "Pong" response to string ping
                return {
                    'type': 'ping_response',
                    'response': "Pong"
                }

            # Try to parse as idl
            try:
                data = json.loads(utf8_data_str)
            except json.JSONDecodeError:
                return None

            # Handle idl ping messages
            if data.get("ping"):
                # BingX expects pong response with same timestamp
                return {
                    'type': 'ping_response',
                    'response': json.dumps({"pong": data["ping"]})
                }

            # Handle subscription confirmation messages
            if data.get("code") == 0 and data.get("msg") == "SUCCESS":
                self.logger.debug(f"Subscription confirmed: {data.get('id')}")
                return None

            # Handle orderbook data
            if data.get("dataType") and isinstance(data.get("data"), dict):
                # Extract symbol from message and convert back to Redis format
                bingx_symbol_from_msg = data["dataType"].split('@')[0]
                redis_symbol = self._convert_from_bingx_format(bingx_symbol_from_msg)

                orderbook_data = data["data"]
                timestamp_ms = int(time.time() * 1000)

                # Process orderbook data - BingX format is already correctly sorted
                bids = orderbook_data.get('bids', [])  # Already high -> low
                asks = orderbook_data.get('asks', [])  # Already low -> high

                return {
                    'symbol': redis_symbol,
                    'timestamp_ms': timestamp_ms,
                    'bids': bids,
                    'asks': asks,
                    'sequence': timestamp_ms,  # BingX doesn't provide sequence, use timestamp
                    'is_snapshot': True  # BingX sends full snapshots
                }

            return None

        except Exception as e:
            self.logger.warning(f"Failed to parse BingX message: {e}")
            return None

    async def _handle_messages(self, websocket, symbols: List[str]):
        """Handle incoming WebSocket messages with BingX-specific ping/pong and stale stream detection"""
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
                    # Parse message using BingX-specific implementation
                    parsed_data = await self.parse_message(message)

                    if parsed_data:
                        # Handle ping responses separately - DO NOT reset timer for pings
                        if parsed_data.get('type') == 'ping_response':
                            await websocket.send(parsed_data['response'])
                            self.logger.debug(f"Sent ping response: {parsed_data['response'][:50]}")
                        else:
                            # Regular orderbook data, process and reset timer
                            await self._process_orderbook_data(parsed_data)
                            last_data_time = time.time()

                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
                    await self.report_error(symbols, "MessageProcessingError", str(e))

        except StaleStreamError:
            self.logger.warning(f"Stale stream detected - no data for {self.stale_stream_timeout}s, reconnecting...")
            raise
        except Exception as e:
            self.logger.error(f"Error in message handling: {e}")
            raise

    def _convert_to_bingx_format(self, redis_symbol: str) -> str:
        """
        Convert Redis symbol format to BingX WebSocket format.
        Redis: BTCUSDT -> BingX WS: BTC-USDT
        """
        # Most symbols end with USDT, USDC, BTC, ETH, etc.
        common_quotes = ['USDT', 'USDC', 'BTC', 'ETH', 'BNB', 'BUSD']

        for quote in common_quotes:
            if redis_symbol.endswith(quote):
                base = redis_symbol[:-len(quote)]
                return f"{base}-{quote}"

        # Fallback: if no common quote found, assume last 4 chars are quote
        if len(redis_symbol) > 4:
            base = redis_symbol[:-4]
            quote = redis_symbol[-4:]
            return f"{base}-{quote}"

        # If symbol is too short, return as-is (shouldn't happen)
        return redis_symbol

    def _convert_from_bingx_format(self, bingx_symbol: str) -> str:
        """
        Convert BingX WebSocket symbol format back to Redis format.
        BingX WS: BTC-USDT -> Redis: BTCUSDT
        """
        return bingx_symbol.replace('-', '')

    async def get_connection_kwargs(self, symbol: str = None) -> Dict[str, Any]:
        """Get BingX-specific connection parameters"""
        kwargs = await super().get_connection_kwargs(symbol)

        # Add BingX-specific connection settings
        kwargs.update({
            'open_timeout': 20,
            'close_timeout': 10,
            'ping_interval': None,  # Handle ping manually
        })

        return kwargs


class BingxSpotConnector(BingxConnector):
    """BingX Spot market connector"""

    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__('spot', worker_id=worker_id, num_workers=num_workers)


class BingxFuturesConnector(BingxConnector):
    """BingX Futures market connector"""

    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__('futures', worker_id=worker_id, num_workers=num_workers)

    async def subscribe_to_symbols(self, websocket, symbols: List[str]):
        """Futures subscription logic with update interval"""
        # Use parent logic but futures includes update interval in dataType
        await super().subscribe_to_symbols(websocket, symbols)


# Main execution function for standalone running
async def main():
    """Main function for running BingX connector standalone"""
    from src.cex.producer.core.logging_setup import setup_standalone_logging
    from src.cex.producer.core.base_connector import parse_worker_args

    # Parse worker arguments for distributed mode
    worker_id, num_workers = parse_worker_args('BingX Orderbook Connector')

    # Choose connector based on config
    config = get_exchange_config('bingx')
    if not config:
        print("BingX configuration not found!")
        return

    # Determine market type
    market_type = None
    if config.get('spot', {}).get('enabled', False):
        market_type = 'spot'
        connector_class = BingxSpotConnector
    elif config.get('futures', {}).get('enabled', False):
        market_type = 'futures'
        connector_class = BingxFuturesConnector
    else:
        print("No BingX markets enabled in configuration!")
        return

    # Setup logging with file + Redis streaming
    logger, streamer = await setup_standalone_logging('bingx', market_type)
    logger.info(f"Starting BingX {market_type} connector...")

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