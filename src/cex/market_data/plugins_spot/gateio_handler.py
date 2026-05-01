#!/usr/bin/env python3
"""
Gate.io Market Data Handler Plugin

Fetches market data from Gate.io REST API and stores in Redis
Demonstrates the market data plugin architecture
"""

# Fix Python path for imports
import sys
import os

import asyncio
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class GateioMarketDataHandler(BaseMarketDataHandler):
    """
    Gate.io market data handler - fetches spot market data from Gate.io API
    """

    def __init__(self, market_type: str = 'spot'):
        super().__init__('gateio', market_type)

        # Get Gate.io-specific configuration
        config = get_market_config('gateio', market_type)
        if not config:
            raise ValueError(f"Gate.io {market_type} configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info(f"Initialized Gate.io {market_type} handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Gate.io API response format

        Gate.io Response format:
        [
            {
                "currency_pair": "UMB_USDT",
                "highest_bid": "50000.1",
                "lowest_ask": "50000.2",
                "last": "50000.15",
                "quote_volume": "123456.78",
                ...
            }
        ]
        """
        # Gate.io API returns a direct list
        if not isinstance(response_data, list):
            self.logger.error("Invalid API response from Gate.io. Expected a list.")
            return []

        tickers_list = response_data
        self.logger.debug(f"Found {len(tickers_list)} tickers from Gate.io")

        parsed_data = []
        for ticker in tickers_list:
            try:
                # Extract symbol and convert format (UMB_USDT -> UMBUSDT)
                native_symbol_raw = ticker.get("currency_pair")
                if not native_symbol_raw:
                    continue

                # Convert from UMB_USDT to UMBUSDT format
                symbol = native_symbol_raw.replace("_", "")

                # Extract price and volume data
                try:
                    volume_24h_usdt = float(ticker.get("quote_volume", "0.0"))
                except (ValueError, TypeError):
                    volume_24h_usdt = 0.0

                bid_str = str(ticker.get("highest_bid"))
                ask_str = str(ticker.get("lowest_ask"))
                last_price_str = str(ticker.get("last"))

                # Calculate aggregation_level (Gate.io-specific field)
                # Determine aggregation level from precision
                precision_bid = self.get_decimal_places(bid_str)
                precision_ask = self.get_decimal_places(ask_str)
                precision_last = self.get_decimal_places(last_price_str)

                max_precision = max(precision_bid, precision_ask, precision_last)

                if max_precision > 0:
                    aggregation_level = f"0.{'0' * (max_precision - 1)}1"
                else:
                    aggregation_level = "1"

                # Assemble data in consistent format
                symbol_data = {
                    'symbol': symbol,
                    'data': {
                        "24h_volume_usdt": volume_24h_usdt,
                        "best_bid": bid_str,
                        "best_ask": ask_str,
                        "lastPrice": last_price_str,
                        "aggregation_level": aggregation_level  # Gate.io uses 'aggregation_level' field
                    }
                }

                parsed_data.append(symbol_data)

            except Exception as e:
                self.logger.warning(f"Error processing ticker {ticker.get('currency_pair', 'unknown')}: {e}")
                continue

        return parsed_data


class GateioSpotHandler(GateioMarketDataHandler):
    """Gate.io Spot market data handler"""

    def __init__(self):
        super().__init__('spot')


# Main execution function for standalone running
async def main():
    """Main function for running Gate.io handler standalone"""
    import logging

    # Setup logging (only if not already configured)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create Gate.io handler
    config = get_market_config('gateio', 'spot')
    if not config or not config.get('enabled', False):
        print("Gate.io spot market data not enabled in configuration!")
        return

    handler = GateioSpotHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize Gate.io handler!")
        return

    print("Starting Gate.io Spot market data handler...")

    try:
        handler.run()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        handler.cleanup()


