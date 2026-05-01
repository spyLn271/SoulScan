#!/usr/bin/env python3
"""
BitMart Market Data Handler Plugin

Fetches market data from BitMart REST API and stores in Redis
Demonstrates the market data plugin architecture
"""

# Fix Python path for imports
import sys
import os

import asyncio
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class BitMartMarketDataHandler(BaseMarketDataHandler):
    """
    BitMart market data handler - fetches spot market data from BitMart API
    """

    def __init__(self, market_type: str = 'spot'):
        super().__init__('bitmart', market_type)

        # Get BitMart-specific configuration
        config = get_market_config('bitmart', market_type)
        if not config:
            raise ValueError(f"BitMart {market_type} configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info(f"Initialized BitMart {market_type} handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse BitMart API response format

        BitMart Response format:
        {
            "code": 1000,
            "message": "OK",
            "data": {
                "tickers": [
                    {
                        "symbol": "BTC_USDT",
                        "last_price": "50000.15",
                        "quote_volume_24h": "123456.78",
                        "best_bid": "50000.1",
                        "best_ask": "50000.2",
                        ...
                    }
                ]
            }
        }
        """
        # BitMart API has a 'code' field. Check if it's 1000 (success).
        if response_data.get('code') != 1000:
            self.logger.error(f"Invalid API response from BitMart. Code: {response_data.get('code')}, Message: {response_data.get('message')}")
            return []

        tickers_list = response_data.get('data', {}).get('tickers', [])
        if not isinstance(tickers_list, list):
            self.logger.error("Invalid data format in BitMart API response")
            return []

        self.logger.debug(f"Found {len(tickers_list)} tickers from BitMart")

        parsed_data = []
        for ticker in tickers_list:
            try:
                # Extract symbol and transform format
                native_symbol_raw = ticker.get("symbol")
                if not native_symbol_raw:
                    continue

                # Transform symbol: remove "_" and "$" characters (e.g., "$NUT_USDT" -> "NUTUSDT")
                symbol = native_symbol_raw.replace("_", "").replace("$", "")

                # Extract volume data
                volume_24h_usdt_str = ticker.get("quote_volume_24h", "0.0")
                try:
                    volume_24h_usdt = float(volume_24h_usdt_str)
                except (ValueError, TypeError):
                    volume_24h_usdt = 0.0

                # Extract price data
                best_bid = ticker.get("best_bid")
                best_ask = ticker.get("best_ask")
                last_price = ticker.get("last_price")

                # Calculate accuracy (similar to OKX implementation)
                max_decimals = max(
                    self.get_decimal_places(best_bid) if best_bid else 0,
                    self.get_decimal_places(best_ask) if best_ask else 0,
                    self.get_decimal_places(last_price) if last_price else 0
                )

                # Calculate accuracy value (e.g., 0.0001 for 4 decimals)
                accuracy_val = pow(10, -max_decimals)

                # Format as string to avoid scientific notation
                if max_decimals > 0:
                    accuracy_str = f"{accuracy_val:.{max_decimals}f}"
                else:
                    accuracy_str = "1"  # For integers with 0 decimal places

                # Assemble data in consistent format
                symbol_data = {
                    'symbol': symbol,
                    'data': {
                        "24h_volume_usdt": volume_24h_usdt,
                        "best_bid": best_bid,
                        "best_ask": best_ask,
                        "lastPrice": last_price,
                        "accuracy": accuracy_str  # BitMart uses 'accuracy' field like OKX
                    }
                }

                parsed_data.append(symbol_data)

            except Exception as e:
                self.logger.warning(f"Error processing ticker {ticker.get('symbol', 'unknown')}: {e}")
                continue

        return parsed_data


class BitMartSpotHandler(BitMartMarketDataHandler):
    """BitMart Spot market data handler"""

    def __init__(self):
        super().__init__('spot')


# Alias for market data manager compatibility
BitmartSpotHandler = BitMartSpotHandler


# Main execution function for standalone running
async def main():
    """Main function for running BitMart handler standalone"""
    import logging

    # Setup logging (only if not already configured)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create BitMart handler
    config = get_market_config('bitmart', 'spot')
    if not config or not config.get('enabled', False):
        print("BitMart spot market data not enabled in configuration!")
        return

    handler = BitMartSpotHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize BitMart handler!")
        return

    print("Starting BitMart Spot market data handler...")

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


