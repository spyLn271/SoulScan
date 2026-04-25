#!/usr/bin/env python3
"""
HTX Market Data Handler Plugin

Fetches market data from HTX (Huobi) REST API and stores in Redis
Demonstrates the market data plugin architecture
"""

# Fix Python path for imports
import sys
import os

import asyncio
from typing import Dict, Any, List

from src.CEX.market_data.core.base_handler import BaseMarketDataHandler
from src.CEX.market_data.config import get_market_config


class HTXMarketDataHandler(BaseMarketDataHandler):
    """
    HTX market data handler - fetches spot market data from HTX API
    """

    def __init__(self, market_type: str = 'spot'):
        super().__init__('htx', market_type)

        # Get HTX-specific configuration
        config = get_market_config('htx', market_type)
        if not config:
            raise ValueError(f"HTX {market_type} configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info(f"Initialized HTX {market_type} handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse HTX API response format

        HTX Response format:
        {
            "status": "ok",
            "data": [
                {
                    "symbol": "btcusdt",
                    "bid": "50000.1",
                    "ask": "50000.2",
                    "close": "50000.15",
                    "vol": "123456.78",
                    ...
                }
            ]
        }
        """
        # HTX API has a 'status' field. Check if it's 'ok'.
        if response_data.get('status') != 'ok':
            self.logger.error(f"Invalid API response from HTX. Status: {response_data.get('status')}, Error: {response_data.get('err-msg')}")
            return []

        tickers_list = response_data.get('data', [])
        if not isinstance(tickers_list, list):
            self.logger.error("Invalid data format in HTX API response")
            return []

        self.logger.debug(f"Found {len(tickers_list)} tickers from HTX")

        parsed_data = []
        for ticker in tickers_list:
            try:
                # Extract symbol (already in correct format: btcusdt)
                symbol = ticker.get("symbol")
                if not symbol:
                    continue

                # Extract price and volume data (keep as strings to preserve precision)
                # 'vol' is the turnover in the quote currency (e.g., USDT)
                try:
                    volume_24h_usdt = float(ticker.get("vol", "0.0"))
                except (ValueError, TypeError):
                    volume_24h_usdt = 0.0

                volume_24h_usdt_str = str(volume_24h_usdt)
                bid_str = str(ticker.get("bid"))
                ask_str = str(ticker.get("ask"))
                last_price_str = str(ticker.get("close"))  # 'close' is the last price in HTX's ticker

                # Assemble data in consistent format
                symbol_data = {
                    'symbol': symbol,
                    'data': {
                        "24h_volume_usdt": volume_24h_usdt_str,
                        "best_bid": bid_str,
                        "best_ask": ask_str,
                        "lastPrice": last_price_str,
                    }
                }

                parsed_data.append(symbol_data)

            except Exception as e:
                self.logger.warning(f"Error processing ticker {ticker.get('symbol', 'unknown')}: {e}")
                continue

        return parsed_data


class HTXSpotHandler(HTXMarketDataHandler):
    """HTX Spot market data handler"""

    def __init__(self):
        super().__init__('spot')


# Main execution function for standalone running
async def main():
    """Main function for running HTX handler standalone"""
    import logging

    # Setup logging (only if not already configured)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create HTX handler
    config = get_market_config('htx', 'spot')
    if not config or not config.get('enabled', False):
        print("HTX spot market data not enabled in configuration!")
        return

    handler = HTXSpotHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize HTX handler!")
        return

    print("Starting HTX Spot market data handler...")

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


