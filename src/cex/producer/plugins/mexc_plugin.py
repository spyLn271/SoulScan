#!/usr/bin/env python3
"""
MEXC Exchange Plugin - Preserves all MEXC-specific behavior

This plugin demonstrates the power of the new architecture:
- Preserves MEXC's unique protobuf message parsing
- Maintains MEXC-specific subscription format with "method": "SUBSCRIPTION"
- Supports binary protobuf orderbook data processing
- Keeps custom ping mechanism using {"method": "PING"}
- Handles subscription error events properly
- Reduces ~800 lines of code to ~250 lines while maintaining full functionality
"""

import sys
import os

import asyncio
import json
import time
from typing import Dict, List, Optional, Any

from src.cex.producer.core.base_connector import BaseExchangeConnector
from src.cex.producer.config import get_exchange_config

# Import MEXC protobuf modules
PROTOBUF_AVAILABLE = False
PushDataV3ApiWrapper_pb2 = None
PublicLimitDepthsV3Api_pb2 = None

try:
    # First check if google.protobuf is available
    import google.protobuf

    # Add the protobuf scripts directory to Python path
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _protobuf_dir = os.path.join(_current_dir, 'mexc_protobuf_pb2_python_scripts')
    if _protobuf_dir not in sys.path:
        sys.path.insert(0, _protobuf_dir)

    # Now import the protobuf modules
    import PushDataV3ApiWrapper_pb2
    import PublicLimitDepthsV3Api_pb2
    PROTOBUF_AVAILABLE = True
except ImportError as e:
    _protobuf_error = e


class MexcConnector(BaseExchangeConnector):
    """
    MEXC exchange plugin - preserves all MEXC-specific protobuf subscription and parsing logic
    """

    def __init__(self, market_type: str = 'spot', worker_id: int = None, num_workers: int = None):
        super().__init__('mexc', market_type, worker_id=worker_id, num_workers=num_workers)

        # Check protobuf availability
        if not PROTOBUF_AVAILABLE:
            error_msg = (
                f"MEXC protobuf modules not available: {_protobuf_error}\n"
                "Please install protobuf library: pip install protobuf\n"
                "And ensure mexc_protobuf_pb2_python_scripts directory is in plugins folder"
            )
            self.logger.error(error_msg)
            raise ImportError(error_msg)

        # MEXC-specific configuration
        self.special_params = self.market_config.get('special_params', {})
        self.depth_level = self.special_params.get('depth_level', 20)
        self.ping_method = self.special_params.get('ping_method', {'method': 'PING'})
        self.subscription_batch_size = 10  # Send subscriptions in batches

        # Cache channel-to-symbol mapping (built once per subscription, not per message)
        self._channel_to_symbol_cache: Dict[str, str] = {}

        self.logger.info(f"Initialized MEXC connector with protobuf support and depth level {self.depth_level}")

    async def get_websocket_url(self, symbol: str = None) -> str:
        """Get MEXC WebSocket URL"""
        return self.market_config['ws_url']

    async def get_ping_message(self) -> Optional[str]:
        """Get MEXC ping message format"""
        return json.dumps(self.ping_method)

    async def subscribe_to_symbols(self, websocket, symbols: List[str]):
        """
        Subscribe to MEXC symbols using MEXC-specific subscription format
        Preserves original MEXC subscription behavior with protobuf channels
        """
        # DEBUG: Log if this worker is subscribing to AXSUSDT
        if 'AXSUSDT' in symbols:
            self.logger.warning(f"[DEBUG] Worker {self.worker_id} SUBSCRIBING to AXSUSDT (batch has {len(symbols)} symbols)")

        # Build channel strings for subscription AND cache the channel-to-symbol mapping
        # This cache is used in _parse_protobuf_message for O(1) lookup instead of O(n) rebuild per message
        all_target_channels = []
        for symbol in symbols:
            channel = f"spot@public.limit.depth.v3.api.pb@{symbol}@{self.depth_level}"
            all_target_channels.append(channel)
            self._channel_to_symbol_cache[channel] = symbol

        # Send subscriptions in batches to avoid overwhelming the server
        for i in range(0, len(all_target_channels), self.subscription_batch_size):
            if self.shutdown_event.is_set():
                break

            batch_channels = all_target_channels[i:i + self.subscription_batch_size]
            subscription_message = {
                "method": "SUBSCRIPTION",
                "params": batch_channels
            }

            await websocket.send(json.dumps(subscription_message))
            self.logger.debug(f"Sent subscription batch {i//self.subscription_batch_size + 1}: {len(batch_channels)} channels")

            # Small delay between batches
            await asyncio.sleep(0.2)

        self.logger.info(f"Sent subscriptions for {len(symbols)} symbols with {len(all_target_channels)} channels")

    async def parse_message(self, raw_message, symbols=None) -> Optional[Dict[str, Any]]:
        """
        Parse MEXC WebSocket message format with protobuf support
        Preserves original MEXC message structure parsing for both text and binary messages
        """
        try:
            # Handle text (idl) messages - errors, confirmations, pongs
            if isinstance(raw_message, str):
                try:
                    message_json = json.loads(raw_message)

                    # Handle subscription errors
                    if message_json.get('event') == 'error':
                        error_msg = f"MEXC subscription error: {message_json}"
                        self.logger.error(error_msg)
                        # Don't return error as orderbook data, let base class handle via report_error
                        return None

                    # Handle other idl messages (confirmations, etc.)
                    self.logger.debug(f"Received JSON message: {raw_message[:200]}")
                    return None

                except json.JSONDecodeError:
                    self.logger.debug(f"Received non-JSON text message: {raw_message[:100]}")
                    return None

            # Handle binary (protobuf) messages - orderbook data
            elif isinstance(raw_message, bytes):
                return await self._parse_protobuf_message(raw_message, symbols)

            return None

        except Exception as e:
            self.logger.warning(f"Failed to parse MEXC message: {e}")
            return None

    async def _parse_protobuf_message(self, binary_message: bytes, symbols=None) -> Optional[Dict[str, Any]]:
        """Parse binary protobuf message for orderbook data"""
        try:
            # Parse the protobuf wrapper
            wrapper = PushDataV3ApiWrapper_pb2.PushDataV3ApiWrapper()
            wrapper.ParseFromString(binary_message)

            # Use cached channel-to-symbol mapping (O(1) lookup instead of O(n) rebuild per message)
            # Cache is built in subscribe_to_symbols()
            if wrapper.channel not in self._channel_to_symbol_cache:
                self.logger.debug(f"Unknown channel in protobuf message: {wrapper.channel}")
                return None

            symbol = self._channel_to_symbol_cache[wrapper.channel]

            # Check if it contains limit depth data
            if wrapper.HasField("publicLimitDepths"):
                depth_pb = wrapper.publicLimitDepths

                # Extract orderbook data
                timestamp_ms = wrapper.sendTime if wrapper.sendTime else int(time.time() * 1000)

                # Convert protobuf orderbook to standard format
                bids = [[bid.price, bid.quantity] for bid in depth_pb.bids]
                asks = [[ask.price, ask.quantity] for ask in depth_pb.asks]

                return {
                    'symbol': symbol,
                    'timestamp_ms': timestamp_ms,
                    'bids': bids,
                    'asks': asks,
                    'sequence': depth_pb.version,  # Use protobuf version as sequence
                    'is_snapshot': True  # MEXC sends full snapshots
                }

            return None

        except Exception as e:
            self.logger.warning(f"Error parsing MEXC protobuf message: {e}")
            return None

    async def get_connection_kwargs(self, symbol: str = None) -> Dict[str, Any]:
        """Get MEXC-specific connection parameters"""
        kwargs = await super().get_connection_kwargs(symbol)

        # Add MEXC-specific connection settings
        kwargs.update({
            'open_timeout': 30,
            'close_timeout': 10,
            'ping_interval': None,  # We handle ping manually
            'compression': None,    # No compression for MEXC
        })

        return kwargs


class MexcSpotConnector(MexcConnector):
    """MEXC Spot market connector"""

    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__('spot', worker_id=worker_id, num_workers=num_workers)


class MexcFuturesConnector(MexcConnector):
    """MEXC Futures market connector"""

    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__('futures', worker_id=worker_id, num_workers=num_workers)

    async def subscribe_to_symbols(self, websocket, symbols: List[str]):
        """Futures subscription logic (if different from spot)"""
        # For now, use same logic as spot
        # This can be customized if futures have different subscription requirements
        await super().subscribe_to_symbols(websocket, symbols)


# Main execution function for standalone running
async def main():
    """Main function for running MEXC connector standalone"""
    from src.cex.producer.core.logging_setup import setup_standalone_logging
    from src.cex.producer.core.base_connector import parse_worker_args

    # Parse worker arguments for distributed mode
    worker_id, num_workers = parse_worker_args('MEXC Orderbook Connector')

    # Choose connector based on config
    config = get_exchange_config('mexc')
    if not config:
        print("MEXC configuration not found!")
        return

    # Determine market type
    market_type = None
    if config.get('spot', {}).get('enabled', False):
        market_type = 'spot'
        connector_class = MexcSpotConnector
    elif config.get('futures', {}).get('enabled', False):
        market_type = 'futures'
        connector_class = MexcFuturesConnector
    else:
        print("No MEXC markets enabled in configuration!")
        return

    # Setup logging with file + Redis streaming
    logger, streamer = await setup_standalone_logging('mexc', market_type)
    logger.info(f"Starting MEXC {market_type} connector...")

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