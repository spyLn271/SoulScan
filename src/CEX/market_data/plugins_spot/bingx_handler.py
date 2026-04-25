#!/usr/bin/env python3
"""
BingX Market Data Handler Plugin

Fetches market data from BingX REST API and stores in Redis
Demonstrates the market data plugin architecture
"""

# Fix Python path for imports
import sys
import os

import asyncio
import time
from typing import Dict, Any, List

from src.CEX.market_data.core.base_handler import BaseMarketDataHandler
from src.CEX.market_data.config import get_market_config


class BingxMarketDataHandler(BaseMarketDataHandler):
    """
    BingX market data handler - fetches spot market data from BingX API
    """

    def __init__(self, market_type: str = 'spot'):
        super().__init__('bingx', market_type)

        # Get BingX-specific configuration
        config = get_market_config('bingx', market_type)
        if not config:
            raise ValueError(f"BingX {market_type} configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info(f"Initialized BingX {market_type} handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse BingX API response format

        BingX Response format:
        {
            "code": 0,
            "msg": "",
            "data": [
                {
                    "symbol": "UMB-USDT",
                    "bidPrice": "0.00123",
                    "askPrice": "0.00124",
                    "lastPrice": "0.001235",
                    "quoteVolume": "1234567.89",
                    ...
                }
            ]
        }
        """
        # Check for API errors in the response body
        if response_data.get("code") != 0:
            self.logger.error(f"API error from BingX: {response_data.get('msg')}")
            return []

        tickers_list = response_data.get("data")
        if not isinstance(tickers_list, list):
            self.logger.error("Invalid API response from BingX Tickers endpoint. 'data' is not a list.")
            return []

        self.logger.debug(f"Found {len(tickers_list)} tickers from BingX")

        parsed_data = []
        for ticker in tickers_list:
            try:
                # Extract symbol and convert format (UMB-USDT -> UMBUSDT)
                native_symbol_raw = ticker.get("symbol")
                if not native_symbol_raw:
                    continue

                # Convert from UMB-USDT to UMBUSDT format for Redis storage
                native_symbol = native_symbol_raw.replace("-", "")

                # Extract volume (quoteVolume is the 24h volume in quote currency)
                try:
                    volume_24h_usdt = float(ticker.get("quoteVolume", "0.0"))
                except (ValueError, TypeError):
                    volume_24h_usdt = 0.0

                # Extract price data
                best_bid = ticker.get("bidPrice")
                best_ask = ticker.get("askPrice")
                last_price = ticker.get("lastPrice")

                # Assemble data in consistent format
                symbol_data = {
                    'symbol': native_symbol,
                    'data': {
                        "24h_volume_usdt": volume_24h_usdt,
                        "best_bid": best_bid,
                        "best_ask": best_ask,
                        "lastPrice": last_price,
                    }
                }

                parsed_data.append(symbol_data)

            except Exception as e:
                self.logger.warning(f"Error processing ticker {ticker.get('symbol', 'unknown')}: {e}")
                continue

        return parsed_data

    def update_redis_data(self):
        """
        Override to add BingX-specific timestamp parameter to API request
        """
        try:
            # BingX requires a timestamp parameter for this endpoint
            current_timestamp = int(time.time() * 1000)
            params = {'timestamp': current_timestamp}

            self.logger.debug(f"Fetching data from {self.api_endpoint} with timestamp {current_timestamp}")

            import requests
            response = requests.get(self.api_endpoint, params=params, timeout=30)
            response.raise_for_status()

            # Parse response using exchange-specific method
            parsed_data = self.parse_api_response(response.json())
            if not parsed_data:
                self.logger.warning("No data returned from API")
                return False

            # Process and store in Redis
            count = self._store_data_in_redis(parsed_data)
            self.logger.info(f"Successfully updated {count} {self.market_type} symbols in Redis")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch data from API: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during update: {e}")
            return False


class BingxSpotHandler(BingxMarketDataHandler):
    """BingX Spot market data handler"""

    def __init__(self):
        super().__init__('spot')


# Main execution function for standalone running
async def main():
    """Main function for running BingX handler standalone"""
    import logging

    # Setup logging (only if not already configured)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create BingX handler
    config = get_market_config('bingx', 'spot')
    if not config or not config.get('enabled', False):
        print("BingX spot market data not enabled in configuration!")
        return

    handler = BingxSpotHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize BingX handler!")
        return

    print("Starting BingX Spot market data handler...")

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


