#!/usr/bin/env python3
"""
OKX Market Data Handler Plugin

Fetches market data from OKX REST API and stores in Redis
Demonstrates the market data plugin architecture
"""

# Fix Python path for imports
import sys
import os

import asyncio
from typing import Dict, Any, List

from src.CEX.market_data.core.base_handler import BaseMarketDataHandler
from src.CEX.market_data.config import get_market_config


class OKXMarketDataHandler(BaseMarketDataHandler):
    """
    OKX market data handler - fetches spot/futures market data from OKX API
    """

    def __init__(self, market_type: str = 'spot'):
        super().__init__('okx', market_type)

        # Get OKX-specific configuration
        config = get_market_config('okx', market_type)
        if not config:
            raise ValueError(f"OKX {market_type} configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info(f"Initialized OKX {market_type} handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse OKX API response format

        OKX Response format:
        {
            "code": "0",
            "msg": "",
            "data": [
                {
                    "instId": "BTC-USDT",
                    "bidPx": "50000.1",
                    "askPx": "50000.2",
                    "last": "50000.15",
                    "volCcy24h": "123456.78",
                    ...
                }
            ]
        }
        """
        if response_data.get('code') != '0':
            self.logger.error(f"Invalid API response from OKX. Code: {response_data.get('code')}, Message: {response_data.get('msg')}")
            return []

        tickers_list = response_data.get('data', [])
        if not isinstance(tickers_list, list):
            self.logger.error("Invalid data format in OKX API response")
            return []

        self.logger.debug(f"Found {len(tickers_list)} tickers from OKX")

        parsed_data = []
        for ticker in tickers_list:
            try:
                # Extract symbol (convert OKX format BTC-USDT to BTCUSDT)
                symbol_raw = ticker.get("instId")
                if not symbol_raw:
                    continue

                symbol = symbol_raw.replace("-", "")

                # Extract price and volume data
                best_bid = ticker.get("bidPx", "0.0")
                best_ask = ticker.get("askPx", "0.0")
                last_price = ticker.get("last", "0.0")
                volume_24h_usdt = ticker.get("volCcy24h", "0.0")

                # Convert volume to float for storage
                try:
                    volume_24h_usdt_float = float(volume_24h_usdt)
                except (ValueError, TypeError):
                    volume_24h_usdt_float = 0.0

                # Calculate accuracy (precision) - OKX specific logic
                max_decimals = max(
                    self.get_decimal_places(best_bid),
                    self.get_decimal_places(best_ask),
                    self.get_decimal_places(last_price)
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
                        "24h_volume_usdt": volume_24h_usdt_float,
                        "best_bid": best_bid,
                        "best_ask": best_ask,
                        "lastPrice": last_price,
                        "accuracy": accuracy_str  # OKX uses 'accuracy' field
                    }
                }

                parsed_data.append(symbol_data)

            except Exception as e:
                self.logger.warning(f"Error processing ticker {ticker.get('instId', 'unknown')}: {e}")
                continue

        return parsed_data


class OkxSpotHandler(OKXMarketDataHandler):
    """OKX Spot market data handler"""

    def __init__(self):
        super().__init__('spot')


class OkxFuturesHandler(OKXMarketDataHandler):
    """OKX Futures market data handler"""

    def __init__(self):
        super().__init__('futures')


# Aliases for backward compatibility
OKXSpotHandler = OkxSpotHandler
OKXFuturesHandler = OkxFuturesHandler


# Main execution function for standalone running
async def main():
    """Main function for running OKX handler standalone"""
    import logging

    # Setup logging (only if not already configured)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create OKX handler
    config = get_market_config('okx', 'spot')
    if not config or not config.get('enabled', False):
        print("OKX spot market data not enabled in configuration!")
        return

    handler = OkxSpotHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize OKX handler!")
        return

    print("Starting OKX Spot market data handler...")

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


