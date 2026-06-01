#!/usr/bin/env python3
"""
BingX Futures Market Data Handler Plugin

Fetches futures market data from BingX REST API and stores in Redis
Requires TWO API endpoints: premiumIndex (funding data) and ticker (price/volume data)
"""

# Fix Python path for imports
import sys
import os

import requests
import json
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class BingxFuturesHandler(BaseMarketDataHandler):
    """
    BingX futures market data handler
    Fetches from TWO endpoints: premiumIndex and ticker for complete data
    """

    def __init__(self):
        super().__init__('bingx', 'futures')

        # Get BingX futures configuration
        config = get_market_config('bingx', 'futures')
        if not config:
            raise ValueError("BingX futures configuration not found")

        self.api_endpoint_premium = config['api_endpoint_premium']
        self.api_endpoint_ticker = config['api_endpoint_ticker']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info("Initialized BingX futures handler")

    def update_redis_data(self):
        """
        Override base method to fetch from TWO endpoints
        Combines premium index data with ticker data for complete information
        """
        try:
            # Fetch premium index data (funding, mark price, index price)
            self.logger.debug(f"Fetching premium index data from {self.api_endpoint_premium}")
            premium_response = requests.get(self.api_endpoint_premium, timeout=30)
            premium_response.raise_for_status()
            premium_data = premium_response.json()

            if premium_data.get('code') != 0:
                self.logger.error(f"Invalid API response from BingX premium index endpoint: {premium_data.get('msg')}")
                return False

            premium_list = premium_data.get('data', [])
            if not isinstance(premium_list, list):
                self.logger.error("Invalid data structure in BingX premium response")
                return False

            # Fetch ticker data (last price, volume)
            self.logger.debug(f"Fetching ticker data from {self.api_endpoint_ticker}")
            ticker_response = requests.get(self.api_endpoint_ticker, timeout=30)
            ticker_response.raise_for_status()
            ticker_data = ticker_response.json()

            if ticker_data.get('code') != 0:
                self.logger.error(f"Invalid API response from BingX ticker endpoint: {ticker_data.get('msg')}")
                return False

            ticker_list = ticker_data.get('data', [])
            if not isinstance(ticker_list, list):
                self.logger.error("Invalid data structure in BingX ticker response")
                return False

            self.logger.debug(f"Found {len(premium_list)} premium entries and {len(ticker_list)} tickers")

            # Create lookup dictionary for premium data
            premium_map = {item['symbol']: item for item in premium_list if 'symbol' in item}

            # Process and combine data
            parsed_data = self._parse_combined_data(ticker_list, premium_map)

            if not parsed_data:
                self.logger.warning("No data returned from combined parsing")
                return False

            # Store in Redis
            count = self._store_data_in_redis(parsed_data)
            self.logger.info(f"Successfully updated {count} futures symbols in Redis")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch data from BingX API: {e}")
            return False
        except json.JSONDecodeError:
            self.logger.error("Failed to decode idl from BingX API response")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during update: {e}")
            return False

    def _parse_combined_data(self, ticker_list: List, premium_map: Dict) -> List[Dict[str, Any]]:
        """
        Parse combined ticker and premium index data

        BingX Premium Index format:
        {
            "symbol": "BTC-USDT",
            "markPrice": "112530.3",
            "indexPrice": "112585.3",
            "lastFundingRate": "0.00004520",
            "nextFundingTime": 1760284800000
        }

        BingX Ticker format:
        {
            "symbol": "BTC-USDT",
            "lastPrice": "112530.5",
            "quoteVolume": "2563179259.74",
            "bidPrice": "112530.3",
            "askPrice": "112530.7",
            "time": 1760283477279
        }
        """
        parsed_data = []

        for ticker in ticker_list:
            try:
                # Extract symbol (in format "BTC-USDT")
                symbol_raw = ticker.get("symbol")
                if not symbol_raw:
                    continue

                # Get corresponding premium data
                premium_data = premium_map.get(symbol_raw)
                if not premium_data:
                    # Skip symbols without premium data
                    continue

                # Convert symbol format: "BTC-USDT" -> "BTCUSDT"
                symbol = symbol_raw.replace("-", "")

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

                # Extract volume (quoteVolume is already in USDT)
                try:
                    volume_24h_usdt = float(ticker.get("quoteVolume", "0.0"))
                except (ValueError, TypeError):
                    volume_24h_usdt = 0.0

                # Extract price data
                last_price = ticker.get("lastPrice")
                best_bid = ticker.get("bidPrice")
                best_ask = ticker.get("askPrice")
                index_price = premium_data.get("indexPrice")
                mark_price = premium_data.get("markPrice")

                # Assemble data in consistent format
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

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Not used for BingX futures (override update_redis_data instead)
        """
        return []


# Main execution function for standalone running
async def main():
    """Main function for running BingX futures handler standalone"""
    import logging
    import asyncio

    # Setup logging
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create BingX futures handler
    config = get_market_config('bingx', 'futures')
    if not config or not config.get('enabled', False):
        print("BingX futures market data not enabled in configuration!")
        return

    handler = BingxFuturesHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize BingX futures handler!")
        return

    print("Starting BingX Futures market data handler...")

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


