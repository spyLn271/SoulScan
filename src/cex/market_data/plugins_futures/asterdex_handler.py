#!/usr/bin/env python3
"""
Asterdex Futures Market Data Handler Plugin

Fetches futures market data from Asterdex REST API and stores in Redis
Requires THREE API endpoints: premiumIndex (funding data), ticker/pair (price/volume data), and bookTicker (bid/ask prices)
"""

# Fix Python path for imports
import sys
import os

import requests
import json
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class AsterdexFuturesHandler(BaseMarketDataHandler):
    """
    Asterdex futures market data handler
    Fetches from THREE endpoints: premiumIndex, ticker/pair, and bookTicker for complete data
    """

    def __init__(self):
        super().__init__('asterdex', 'futures')

        # Get Asterdex futures configuration
        config = get_market_config('asterdex', 'futures')
        if not config:
            raise ValueError("Asterdex futures configuration not found")

        self.api_endpoint_premium = config['api_endpoint_premium']
        self.api_endpoint_ticker = config['api_endpoint_ticker']
        self.api_endpoint_book = config['api_endpoint_book']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info("Initialized Asterdex futures handler")

    def update_redis_data(self):
        """
        Override base method to fetch from THREE endpoints
        Combines premium index, ticker, and book ticker data for complete information
        """
        try:
            # Fetch premium index data (funding, mark price, index price)
            self.logger.debug(f"Fetching premium index data from {self.api_endpoint_premium}")
            premium_response = requests.get(self.api_endpoint_premium, timeout=30)
            premium_response.raise_for_status()
            premium_list = premium_response.json()

            if not isinstance(premium_list, list):
                self.logger.error("Invalid API response from Asterdex premium index endpoint")
                return False

            # Fetch ticker/pair data (last price, volume)
            self.logger.debug(f"Fetching ticker data from {self.api_endpoint_ticker}")
            ticker_response = requests.get(self.api_endpoint_ticker, timeout=30)
            ticker_response.raise_for_status()
            ticker_data = ticker_response.json()

            # Extract data array from nested response
            if not isinstance(ticker_data, dict) or 'data' not in ticker_data:
                self.logger.error("Invalid API response from Asterdex ticker endpoint")
                return False

            ticker_list = ticker_data.get('data', [])
            if not isinstance(ticker_list, list):
                self.logger.error("Invalid data structure in Asterdex ticker response")
                return False

            # Fetch book ticker data (bid/ask prices)
            self.logger.debug(f"Fetching book ticker data from {self.api_endpoint_book}")
            book_response = requests.get(self.api_endpoint_book, timeout=30)
            book_response.raise_for_status()
            book_list = book_response.json()

            if not isinstance(book_list, list):
                self.logger.error("Invalid API response from Asterdex book ticker endpoint")
                return False

            self.logger.debug(f"Found {len(premium_list)} premium entries, {len(ticker_list)} tickers, and {len(book_list)} book tickers")

            # Create lookup dictionary for premium data
            premium_map = {item['symbol']: item for item in premium_list}

            # Create lookup dictionary for book ticker data
            book_map = {}
            for item in book_list:
                symbol = item.get('symbol')
                if symbol:
                    book_map[symbol] = {
                        'bidPrice': item.get('bidPrice'),
                        'askPrice': item.get('askPrice')
                    }

            # Process and combine data
            parsed_data = self._parse_combined_data(ticker_list, premium_map, book_map)

            if not parsed_data:
                self.logger.warning("No data returned from combined parsing")
                return False

            # Store in Redis
            count = self._store_data_in_redis(parsed_data)
            self.logger.info(f"Successfully updated {count} futures symbols in Redis")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch data from Asterdex API: {e}")
            return False
        except json.JSONDecodeError:
            self.logger.error("Failed to decode idl from Asterdex API response")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during update: {e}")
            return False

    def _parse_combined_data(self, ticker_list: List, premium_map: Dict, book_map: Dict) -> List[Dict[str, Any]]:
        """
        Parse combined ticker, premium index, and book ticker data

        Asterdex Premium Index format:
        {
            "symbol": "INJUSDT",
            "markPrice": "8.61709300",
            "indexPrice": "8.62324034",
            "lastFundingRate": "0.00006601",
            "nextFundingTime": 1760284800000,
            ...
        }

        Asterdex Ticker/Pair format:
        {
            "symbol": "INJUSDT",
            "lastPrice": 8.621,
            "quoteVolume": 76845.52,
            ...
        }

        Asterdex Book Ticker format:
        {
            "symbol": "BTCUSDT",
            "bidPrice": "102508.7",
            "askPrice": "102508.8",
            ...
        }
        """
        parsed_data = []

        for ticker in ticker_list:
            try:
                # Extract symbol
                symbol = ticker.get("symbol")
                if not symbol:
                    continue

                # Get corresponding premium data
                premium_data = premium_map.get(symbol)
                if not premium_data:
                    # Skip symbols without premium data
                    continue

                # Get corresponding book ticker data
                book_data = book_map.get(symbol, {})

                # Get next funding time timestamp from nextFundingTime (milliseconds)
                next_funding_time = None
                next_funding_ms = premium_data.get("nextFundingTime")
                if next_funding_ms is not None:
                    next_funding_time = next_funding_ms // 1000  # Convert milliseconds to seconds

                # Calculate funding rate percentage
                try:
                    funding_rate = float(premium_data.get("lastFundingRate", "0.0"))
                    funding_rate_percent = funding_rate * 100
                except (ValueError, TypeError):
                    funding_rate_percent = 0.0

                # Extract volume (quote volume = volume in USDT)
                try:
                    volume_24h_usdt = float(ticker.get("quoteVolume", "0.0"))
                except (ValueError, TypeError):
                    volume_24h_usdt = 0.0

                # Extract price data
                # Use lastPrice from ticker API (as specified)
                last_price = ticker.get("lastPrice")
                index_price = premium_data.get("indexPrice")
                mark_price = premium_data.get("markPrice")

                # Extract bid/ask prices from book ticker
                best_bid = book_data.get('bidPrice')
                best_ask = book_data.get('askPrice')

                # Assemble data in consistent format
                symbol_data = {
                    'symbol': symbol,
                    'data': {
                        "24h_volume_usdt": volume_24h_usdt,
                        "best_bid": best_bid,  # Now populated from book ticker
                        "best_ask": best_ask,  # Now populated from book ticker
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

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Not used for Asterdex futures (override update_redis_data instead)
        """
        return []


# Main execution function for standalone running
async def main():
    """Main function for running Asterdex futures handler standalone"""
    import logging
    import asyncio

    # Setup logging
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create Asterdex futures handler
    config = get_market_config('asterdex', 'futures')
    if not config or not config.get('enabled', False):
        print("Asterdex futures market data not enabled in configuration!")
        return

    handler = AsterdexFuturesHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize Asterdex futures handler!")
        return

    print("Starting Asterdex Futures market data handler...")

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


