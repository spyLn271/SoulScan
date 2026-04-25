#!/usr/bin/env python3
"""
Binance Futures Market Data Handler Plugin

Fetches futures market data from Binance REST API and stores in Redis
Requires THREE API endpoints for complete data (24hr ticker, premium index, book ticker)
Uses async/aiohttp for concurrent requests
"""

# Fix Python path for imports
import sys
import os

import asyncio
import aiohttp
import json
from typing import Dict, Any, List

from src.CEX.market_data.core.base_handler import BaseMarketDataHandler
from src.CEX.market_data.config import get_market_config


class BinanceFuturesHandler(BaseMarketDataHandler):
    """
    Binance futures market data handler
    Fetches from THREE endpoints concurrently using async/aiohttp:
    1. 24hr ticker - volume, lastPrice
    2. premiumIndex - markPrice, indexPrice, funding rate, next funding time
    3. bookTicker - bid/ask prices
    """

    def __init__(self):
        super().__init__('binance', 'futures')

        # Get Binance futures configuration
        config = get_market_config('binance', 'futures')
        if not config:
            raise ValueError("Binance futures configuration not found")

        # Three API endpoints
        self.api_endpoint_24hr = config['api_endpoint_24hr']
        self.api_endpoint_premium = config['api_endpoint_premium']
        self.api_endpoint_book = config['api_endpoint_book']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info("Initialized Binance futures handler")

    async def fetch_all_data_async(self) -> List[Dict[str, Any]]:
        """
        Async method to fetch all data from THREE endpoints concurrently
        """
        async with aiohttp.ClientSession() as session:
            try:
                # Fetch all three endpoints concurrently
                self.logger.debug("Fetching data from all Binance endpoints...")
                ticker_24hr_task = session.get(self.api_endpoint_24hr, timeout=aiohttp.ClientTimeout(total=10))
                premium_task = session.get(self.api_endpoint_premium, timeout=aiohttp.ClientTimeout(total=10))
                book_ticker_task = session.get(self.api_endpoint_book, timeout=aiohttp.ClientTimeout(total=10))

                ticker_24hr_response, premium_response, book_ticker_response = await asyncio.gather(
                    ticker_24hr_task, premium_task, book_ticker_task
                )

                # Parse JSON responses
                ticker_24hr_json = await ticker_24hr_response.json()
                premium_json = await premium_response.json()
                book_ticker_json = await book_ticker_response.json()

                # Validate responses are lists
                if not isinstance(ticker_24hr_json, list) or not isinstance(premium_json, list) or not isinstance(book_ticker_json, list):
                    self.logger.error("Invalid API response format from Binance")
                    return []

                self.logger.debug(f"Found {len(ticker_24hr_json)} 24hr tickers, {len(premium_json)} premium data, {len(book_ticker_json)} book tickers")

                # Create lookup dictionaries by symbol
                premium_map = {item['symbol']: item for item in premium_json if 'symbol' in item}
                book_ticker_map = {item['symbol']: item for item in book_ticker_json if 'symbol' in item}

                # Process and combine all data
                parsed_data = []
                for ticker in ticker_24hr_json:
                    try:
                        symbol = ticker.get("symbol")
                        if not symbol:
                            continue

                        # Filter for USDT perpetual contracts only
                        if not symbol.endswith("USDT"):
                            continue

                        # Get corresponding data from other endpoints
                        premium_data = premium_map.get(symbol)
                        book_data = book_ticker_map.get(symbol)

                        if not premium_data or not book_data:
                            # Skip if we don't have complete data
                            continue

                        # Extract data from 24hr ticker endpoint
                        volume_24h_usdt = ticker.get("quoteVolume", "0.0")  # 24h turnover in USDT
                        last_price = ticker.get("lastPrice", "0.0")

                        # Extract data from premium index endpoint
                        mark_price = premium_data.get("markPrice")
                        index_price = premium_data.get("indexPrice")
                        funding_rate_raw = premium_data.get("lastFundingRate", "0.0")
                        next_funding_time_ms = premium_data.get("nextFundingTime", 0)

                        # Extract data from book ticker endpoint
                        best_bid = book_data.get("bidPrice")
                        best_ask = book_data.get("askPrice")

                        # Calculate funding rate percentage (multiply by 100)
                        try:
                            funding_rate_percent = float(funding_rate_raw) * 100
                        except (ValueError, TypeError):
                            funding_rate_percent = 0.0

                        # Convert next funding time from milliseconds to seconds
                        next_funding_time = None
                        if next_funding_time_ms and next_funding_time_ms > 0:
                            next_funding_time = int(next_funding_time_ms) // 1000

                        # Assemble data in standardized format
                        symbol_data = {
                            'symbol': symbol,
                            'data': {
                                "24h_volume_usdt": volume_24h_usdt,
                                "best_bid": best_bid,
                                "best_ask": best_ask,
                                "lastPrice": last_price,
                                "indexPrice": index_price,
                                "markPrice": mark_price,
                                "funding_rate_percent": funding_rate_percent,
                                "next_funding_time": next_funding_time
                            }
                        }

                        parsed_data.append(symbol_data)

                    except Exception as e:
                        self.logger.warning(f"Error processing ticker {ticker.get('symbol', 'unknown')}: {e}")
                        continue

                return parsed_data

            except Exception as e:
                self.logger.error(f"Error fetching Binance futures data: {e}")
                return []

    def update_redis_data(self):
        """
        Override base method to use async data fetching
        """
        try:
            # Run async fetch in sync context
            parsed_data = asyncio.run(self.fetch_all_data_async())

            if not parsed_data:
                self.logger.warning("No data returned from Binance API")
                return False

            # Store in Redis
            count = self._store_data_in_redis(parsed_data)
            self.logger.info(f"Successfully updated {count} futures symbols in Redis")
            return True

        except Exception as e:
            self.logger.error(f"Unexpected error during Binance update: {e}")
            return False

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Not used for Binance futures (override update_redis_data instead)
        """
        return []


# Main execution function for standalone running
async def main():
    """Main function for running Binance futures handler standalone"""
    import logging

    # Setup logging
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create Binance futures handler
    config = get_market_config('binance', 'futures')
    if not config or not config.get('enabled', False):
        print("Binance futures market data not enabled in configuration!")
        return

    handler = BinanceFuturesHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize Binance futures handler!")
        return

    print("Starting Binance Futures market data handler...")

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


