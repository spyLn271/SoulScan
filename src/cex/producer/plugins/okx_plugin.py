#!/usr/bin/env python3
"""
OKX Exchange Plugin - Demonstrates batched connection architecture

This plugin shows how batched connections work in the new architecture:
- Manages multiple symbols per WebSocket connection (up to 20)
- Preserves OKX-specific subscription and data handling logic
- Supports snapshot/update processing and symbol format conversion
- ~150 lines vs ~800 lines in original implementation
"""

import sys
import os

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any, Set
import websockets

from src.cex.producer.core.base_connector import BaseExchangeConnector
from src.cex.producer.config import get_exchange_config


class OKXConnector(BaseExchangeConnector):
    """
    OKX exchange plugin - demonstrates batched connection handling
    """

    def __init__(self, market_type: str = 'spot', worker_id: int = None, num_workers: int = None):
        super().__init__('okx', market_type, worker_id=worker_id, num_workers=num_workers)

        # OKX-specific state for orderbook management
        self.orderbooks: Dict[str, Dict[str, Dict[str, float]]] = {}
        self.initialized_symbols: Set[str] = set()

        self.logger.info("Initialized OKX connector with batched connections")

    async def get_websocket_url(self, symbol: str = None) -> str:
        """Get OKX WebSocket URL"""
        return self.market_config['ws_url']

    async def get_ping_message(self) -> Optional[str]:
        """OKX uses text ping/pong"""
        return "ping"

    async def subscribe_to_symbols(self, websocket, symbols: List[str]):
        """
        Subscribe to multiple OKX symbols in a single message
        Only subscribes to symbols with valid accuracy data from Redis
        """
        # Get grouping values from Redis for proper subscription
        grouping_map = await self._get_symbol_groupings(symbols)

        # Filter to only symbols with valid grouping
        valid_symbols = [s for s in symbols if s in grouping_map]

        if not valid_symbols:
            self.logger.error("No symbols have valid grouping data - cannot subscribe")
            return

        if len(valid_symbols) < len(symbols):
            self.logger.info(f"Subscribing to {len(valid_symbols)}/{len(symbols)} symbols (others lack accuracy data)")

        # Build subscription arguments only for valid symbols
        args = []
        for symbol in valid_symbols:
            okx_symbol = self._convert_to_okx_format(symbol)
            args.append({
                "channel": "books-grouped",
                "grouping": grouping_map[symbol],  # No fallback needed - all valid_symbols have grouping
                "instId": okx_symbol
            })

            # Initialize orderbook for this symbol
            self.orderbooks[symbol] = {"bids": {}, "asks": {}}

        # Send subscription message
        subscribe_msg = {
            "op": "subscribe",
            "args": args
        }

        self.logger.info(f"Subscribing to {len(valid_symbols)} symbols in batch")
        await websocket.send(json.dumps(subscribe_msg))

    async def _get_symbol_groupings(self, symbols: List[str]) -> Dict[str, str]:
        """Get grouping values from Redis - only returns symbols with valid accuracy"""
        grouping_map = {}
        skipped = []

        try:
            market_data_key = f"{self.market_type}-market-data:{self.exchange_name}"
            redis_data = await self.redis_client.hgetall(market_data_key)

            if not redis_data:
                self.logger.warning(f"No market data found in Redis key: {market_data_key}")
                return {}

            # Decode Redis data (handle both bytes and strings)
            decoded_redis_data = {}
            for key, value in redis_data.items():
                key = key.decode('utf-8') if isinstance(key, bytes) else key
                value = value.decode('utf-8') if isinstance(value, bytes) else value
                decoded_redis_data[key] = value

            for symbol in symbols:
                native_symbol = symbol.replace("-", "")
                if native_symbol in decoded_redis_data:
                    try:
                        data = json.loads(decoded_redis_data[native_symbol])
                        accuracy = data.get("accuracy")
                        if accuracy:
                            grouping_map[symbol] = accuracy
                        else:
                            skipped.append(symbol)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse Redis data for {native_symbol}: {e}")
                        skipped.append(symbol)
                else:
                    skipped.append(symbol)

            if skipped:
                self.logger.warning(f"Skipping {len(skipped)} symbols without accuracy data: {skipped[:10]}{'...' if len(skipped) > 10 else ''}")

        except Exception as e:
            self.logger.error(f"Error getting symbol groupings from Redis: {e}")
            return {}

        return grouping_map

    def _convert_to_okx_format(self, native_symbol: str) -> str:
        """Convert native symbol format (BTCUSDT) to OKX format (BTC-USDT)"""
        for quote in ["USDT", "USDC", "USD", "BTC", "ETH"]:
            if native_symbol.endswith(quote):
                base = native_symbol[:-len(quote)]
                return f"{base}-{quote}"
        return native_symbol

    def _convert_from_okx_format(self, okx_symbol: str) -> str:
        """Convert OKX symbol format (BTC-USDT) to native format (BTCUSDT)"""
        return okx_symbol.replace("-", "")

    async def parse_message(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Parse OKX WebSocket message format
        Handles subscription responses and orderbook updates
        """
        # Handle ping/pong
        if message == "ping":
            return {"type": "ping"}
        if message == "pong":
            return None

        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return None

        # Handle subscription responses
        if "event" in data:
            event = data.get("event")
            if event == "error":
                self.logger.error(f"Subscription error: {data}")
                await self.report_error([], "SubscriptionError",
                                       f"Code: {data.get('code')}, Message: {data.get('msg')}")
            elif event == "subscribe":
                self.logger.info(f"Subscription confirmed: {data.get('arg', {})}")
            return None

        # Handle orderbook data
        if "arg" in data and "data" in data:
            arg = data["arg"]
            if arg.get("channel") != "books-grouped":
                return None

            okx_symbol = arg.get("instId")
            if not okx_symbol:
                return None

            native_symbol = self._convert_from_okx_format(okx_symbol)
            if native_symbol not in self.orderbooks:
                return None

            action = data.get("action", "")
            data_list = data.get("data", [])
            if not data_list:
                return None

            payload = data_list[0]
            return await self._process_orderbook_update(native_symbol, payload, action)

        return None

    async def _process_orderbook_update(self, symbol: str, payload: Dict[str, Any], action: str) -> Optional[Dict[str, Any]]:
        """Process OKX orderbook update and maintain local orderbook state"""
        book = self.orderbooks[symbol]
        bids = book["bids"]
        asks = book["asks"]

        bids_list = payload.get("bids", [])
        asks_list = payload.get("asks", [])
        ts_str = payload.get("ts", str(int(time.time() * 1000)))

        # Handle snapshot vs update
        if action == "snapshot" or symbol not in self.initialized_symbols:
            # Clear and replace book
            bids.clear()
            asks.clear()
            self._apply_side_snapshot(bids, bids_list)
            self._apply_side_snapshot(asks, asks_list)
            self.initialized_symbols.add(symbol)

            self.logger.debug(f"[{symbol}] Processed snapshot: {len(bids)} bids, {len(asks)} asks")

        elif action == "update" and symbol in self.initialized_symbols:
            # Apply incremental updates
            self._apply_side_update(bids, bids_list)
            self._apply_side_update(asks, asks_list)

        else:
            return None

        # Convert book to list format for output
        bids_formatted = [
            [price, str(size)]
            for price, size in sorted(bids.items(), key=lambda x: float(x[0]), reverse=True)[:40]
        ]
        asks_formatted = [
            [price, str(size)]
            for price, size in sorted(asks.items(), key=lambda x: float(x[0]))[:40]
        ]

        return {
            'symbol': symbol,
            'timestamp_ms': int(ts_str),
            'bids': bids_formatted,
            'asks': asks_formatted,
            'sequence': payload.get("seqId", 0)
        }

    def _apply_side_snapshot(self, side_book: Dict[str, float], side_data: List[List[str]]):
        """Apply snapshot data to one side of the orderbook"""
        for price_str, size_str in side_data:
            price = float(price_str)
            size = float(size_str)
            if size > 0:
                side_book[price_str] = size

    def _apply_side_update(self, side_book: Dict[str, float], side_data: List[List[str]]):
        """Apply incremental update to one side of the orderbook"""
        for price_str, size_str in side_data:
            price = float(price_str)
            size = float(size_str)
            if size == 0:
                # Remove price level
                side_book.pop(price_str, None)
            else:
                # Update price level
                side_book[price_str] = size

    async def _handle_messages(self, websocket, symbols: List[str]):
        """Override message handling to respond to pings"""
        try:
            async for message in websocket:
                if self.shutdown_event.is_set():
                    break

                # Handle ping/pong at the message level
                if isinstance(message, str):
                    if message == "ping":
                        await websocket.send("pong")
                        continue

                    try:
                        # Parse message using exchange-specific implementation
                        parsed_data = await self.parse_message(message)

                        if parsed_data and parsed_data.get('type') != 'ping':
                            await self._process_orderbook_data(parsed_data)

                    except Exception as e:
                        self.logger.error(f"Error processing message: {e}")
                        await self.report_error(symbols, "MessageProcessingError", str(e))

        except websockets.exceptions.ConnectionClosed:
            self.logger.info("WebSocket connection closed")
            raise
        except Exception as e:
            self.logger.error(f"Error in message handling: {e}")
            raise

    async def get_connection_kwargs(self, symbol: str = None) -> Dict[str, Any]:
        """Get OKX-specific connection parameters"""
        kwargs = await super().get_connection_kwargs(symbol)

        kwargs.update({
            'ping_interval': None,  # OKX handles ping/pong manually
            'close_timeout': 5,
        })

        return kwargs


class OkxSpotConnector(OKXConnector):
    """OKX Spot market connector"""

    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__('spot', worker_id=worker_id, num_workers=num_workers)


# Alias for backward compatibility
OKXSpotConnector = OkxSpotConnector


# Main execution function for standalone running
async def main():
    """Main function for running OKX connector standalone"""
    from src.cex.producer.core.logging_setup import setup_standalone_logging
    from src.cex.producer.core.base_connector import parse_worker_args

    # Parse worker arguments for distributed mode
    worker_id, num_workers = parse_worker_args('OKX Orderbook Connector')

    # Choose connector based on config
    config = get_exchange_config('okx')
    if not config:
        print("OKX configuration not found!")
        return

    # Determine market type
    market_type = None
    if config.get('spot', {}).get('enabled', False):
        market_type = 'spot'
        connector_class = OkxSpotConnector
    elif config.get('futures', {}).get('enabled', False):
        market_type = 'futures'
        connector_class = OkxFuturesConnector
    else:
        print("No OKX markets enabled in configuration!")
        return

    # Setup logging with file + Redis streaming
    logger, streamer = await setup_standalone_logging('okx', market_type)
    logger.info(f"Starting OKX {market_type} connector...")

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