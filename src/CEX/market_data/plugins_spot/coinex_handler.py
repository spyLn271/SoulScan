#!/usr/bin/env python3
"""
CoinEx Market Data Handler Plugin

Fetches market data from CoinEx REST API and stores in Redis
Demonstrates the market data plugin architecture
"""

# Fix Python path for imports
import sys
import os

import asyncio
from typing import Dict, Any, List

from src.CEX.market_data.core.base_handler import BaseMarketDataHandler
from src.CEX.market_data.config import get_market_config


class CoinExMarketDataHandler(BaseMarketDataHandler):
    """
    CoinEx market data handler - fetches spot market data from CoinEx API
    """

    def __init__(self, market_type: str = 'spot'):
        super().__init__('coinex', market_type)

        # Get CoinEx-specific configuration
        config = get_market_config('coinex', market_type)
        if not config:
            raise ValueError(f"CoinEx {market_type} configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info(f"Initialized CoinEx {market_type} handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse CoinEx API response format

        CoinEx Response format:
        {
            "code": 0,
            "data": [
                {
                    "market": "BTCUSDT",
                    "last": "50000.15",
                    "value": "123456.78",
                    ...
                }
            ],
            "message": "OK"
        }
        """
        # CoinEx API has a 'code' field. Check if it's 0 (success).
        if response_data.get('code') != 0:
            self.logger.error(f"Invalid API response from CoinEx. Message: {response_data.get('message')}")
            return []

        tickers_list = response_data.get('data', [])
        if not isinstance(tickers_list, list):
            self.logger.error("Invalid data format in CoinEx API response")
            return []

        self.logger.debug(f"Found {len(tickers_list)} tickers from CoinEx")

        parsed_data = []
        for ticker in tickers_list:
            try:
                # Extract symbol (CoinEx symbol is 'market' and already in 'BTCUSDT' format)
                symbol = ticker.get("market")
                if not symbol:
                    continue

                # Extract volume data (This is the quote volume/turnover)
                volume_24h_usdt_str = ticker.get("value", "0.0")
                try:
                    volume_24h_usdt = float(volume_24h_usdt_str)
                except (ValueError, TypeError):
                    volume_24h_usdt = 0.0

                # Extract price data
                last_price = ticker.get("last")

                # NOTE: CoinEx API does not provide best bid/ask. They are set to None.
                best_bid = None
                best_ask = None

                # Assemble data in consistent format
                symbol_data = {
                    'symbol': symbol,
                    'data': {
                        "24h_volume_usdt": volume_24h_usdt,
                        "best_bid": best_bid,
                        "best_ask": best_ask,
                        "lastPrice": last_price,
                    }
                }

                parsed_data.append(symbol_data)

            except Exception as e:
                self.logger.warning(f"Error processing ticker {ticker.get('market', 'unknown')}: {e}")
                continue

        return parsed_data


class CoinExSpotHandler(CoinExMarketDataHandler):
    """CoinEx Spot market data handler"""

    def __init__(self):
        super().__init__('spot')


# Alias for market data manager compatibility
CoinexSpotHandler = CoinExSpotHandler


# Main execution function for standalone running
async def main():
    """Main function for running CoinEx handler standalone"""
    import logging

    # Setup logging (only if not already configured)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create CoinEx handler
    config = get_market_config('coinex', 'spot')
    if not config or not config.get('enabled', False):
        print("CoinEx spot market data not enabled in configuration!")
        return

    handler = CoinExSpotHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize CoinEx handler!")
        return

    print("Starting CoinEx Spot market data handler...")

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


