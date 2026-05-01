#!/usr/bin/env python3
"""
Binance Spot Market Data Handler Plugin

Fetches spot market data from Binance REST API and stores in Redis
Single endpoint provides all necessary data
"""

# Fix Python path for imports
import sys
import os

import asyncio
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class BinanceSpotHandler(BaseMarketDataHandler):
    """
    Binance spot market data handler - fetches spot market data from Binance API
    """

    def __init__(self):
        super().__init__('binance', 'spot')

        # Get Binance spot configuration
        config = get_market_config('binance', 'spot')
        if not config:
            raise ValueError("Binance spot configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info("Initialized Binance spot handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Binance API response for spot market data

        Binance Spot Response format (direct list):
        [
            {
                "symbol": "ETHBTC",
                "lastPrice": "0.03572000",
                "bidPrice": "0.03571000",
                "askPrice": "0.03572000",
                "quoteVolume": "773.39887980",
                ...
            },
            ...
        ]
        """
        if not isinstance(response_data, list):
            self.logger.error("Invalid API response from Binance - expected list")
            return []

        tickers_list = response_data
        self.logger.debug(f"Found {len(tickers_list)} tickers from Binance spot")

        parsed_data = []
        for ticker in tickers_list:
            try:
                # Extract symbol (already in correct format: BTCUSDT)
                symbol = ticker.get("symbol")
                if not symbol:
                    continue

                # Filter for USDT pairs only
                if not symbol.endswith("USDT"):
                    continue

                # Extract price and volume data
                last_price = ticker.get("lastPrice", "0.0")
                best_bid = ticker.get("bidPrice", "0.0")
                best_ask = ticker.get("askPrice", "0.0")
                volume_24h_usdt = ticker.get("quoteVolume", "0.0")  # quoteVolume is 24h volume in USDT

                # Convert volume to float for consistency
                try:
                    volume_24h_usdt_float = float(volume_24h_usdt)
                except (ValueError, TypeError):
                    volume_24h_usdt_float = 0.0

                # Assemble data in consistent format
                symbol_data = {
                    'symbol': symbol,
                    'data': {
                        "24h_volume_usdt": volume_24h_usdt_float,
                        "best_bid": best_bid,
                        "best_ask": best_ask,
                        "lastPrice": last_price
                    }
                }

                parsed_data.append(symbol_data)

            except Exception as e:
                self.logger.warning(f"Error processing ticker {ticker.get('symbol', 'unknown')}: {e}")
                continue

        return parsed_data


# Main execution function for standalone running
async def main():
    """Main function for running Binance spot handler standalone"""
    import logging

    # Setup logging (only if not already configured)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create Binance spot handler
    config = get_market_config('binance', 'spot')
    if not config or not config.get('enabled', False):
        print("Binance spot market data not enabled in configuration!")
        return

    handler = BinanceSpotHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize Binance spot handler!")
        return

    print("Starting Binance Spot market data handler...")

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


