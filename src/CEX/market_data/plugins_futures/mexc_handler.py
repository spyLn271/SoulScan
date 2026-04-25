#!/usr/bin/env python3
"""
MEXC Futures Market Data Handler Plugin

Fetches futures market data from MEXC REST API and stores in Redis
Requires TWO API endpoints: funding_rate (funding data) and ticker (price/volume data)
"""

# Fix Python path for imports
import sys
import os

import requests
import json
from typing import Dict, Any, List

from src.CEX.market_data.core.base_handler import BaseMarketDataHandler
from src.CEX.market_data.config import get_market_config


class MEXCFuturesHandler(BaseMarketDataHandler):
    """
    MEXC futures market data handler
    Fetches from TWO endpoints: funding_rate and ticker for complete data
    """

    def __init__(self):
        super().__init__('mexc', 'futures')

        # Get MEXC futures configuration
        config = get_market_config('mexc', 'futures')
        if not config:
            raise ValueError("MEXC futures configuration not found")

        self.api_endpoint_funding = config['api_endpoint_funding']
        self.api_endpoint_ticker = config['api_endpoint_ticker']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info("Initialized MEXC futures handler")

    def update_redis_data(self):
        """
        Override base method to fetch from TWO endpoints
        Combines funding rate data with ticker data for complete information
        """
        try:
            # Fetch funding rate data
            self.logger.debug(f"Fetching funding rate data from {self.api_endpoint_funding}")
            funding_response = requests.get(self.api_endpoint_funding, timeout=30)
            funding_response.raise_for_status()
            funding_data = funding_response.json()

            if not funding_data.get('success') or funding_data.get('code') != 0:
                self.logger.error(f"Invalid API response from MEXC funding rate endpoint")
                return False

            funding_list = funding_data.get('data', [])
            if not isinstance(funding_list, list):
                self.logger.error("Invalid data structure in MEXC funding response")
                return False

            # Fetch ticker data (price, volume, bid/ask)
            self.logger.debug(f"Fetching ticker data from {self.api_endpoint_ticker}")
            ticker_response = requests.get(self.api_endpoint_ticker, timeout=30)
            ticker_response.raise_for_status()
            ticker_data = ticker_response.json()

            if not ticker_data.get('success') or ticker_data.get('code') != 0:
                self.logger.error(f"Invalid API response from MEXC ticker endpoint")
                return False

            ticker_list = ticker_data.get('data', [])
            if not isinstance(ticker_list, list):
                self.logger.error("Invalid data structure in MEXC ticker response")
                return False

            self.logger.debug(f"Found {len(funding_list)} funding entries and {len(ticker_list)} tickers")

            # Create lookup dictionary for funding data
            funding_map = {item['symbol']: item for item in funding_list if 'symbol' in item}

            # Process and combine data
            parsed_data = self._parse_combined_data(ticker_list, funding_map)

            if not parsed_data:
                self.logger.warning("No data returned from combined parsing")
                return False

            # Store in Redis
            count = self._store_data_in_redis(parsed_data)
            self.logger.info(f"Successfully updated {count} futures symbols in Redis")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch data from MEXC API: {e}")
            return False
        except json.JSONDecodeError:
            self.logger.error("Failed to decode JSON from MEXC API response")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during update: {e}")
            return False

    def _parse_combined_data(self, ticker_list: List, funding_map: Dict) -> List[Dict[str, Any]]:
        """
        Parse combined ticker and funding rate data

        MEXC Funding Rate format:
        {
            "symbol": "BTC_USDT",
            "fundingRate": -0.000107,
            "nextSettleTime": 1760284800000,
            "timestamp": 1760284580319
        }

        MEXC Ticker format:
        {
            "symbol": "BTC_USDT",
            "lastPrice": 113145.8,
            "bid1": 113145.8,
            "ask1": 113145.9,
            "amount24": 3340815851.84382,
            "indexPrice": 113222.8,
            "fairPrice": 113145.9,
            "timestamp": 1760284637646
        }
        """
        parsed_data = []

        for ticker in ticker_list:
            try:
                # Extract symbol (in format "BTC_USDT")
                symbol_raw = ticker.get("symbol")
                if not symbol_raw:
                    continue

                # Get corresponding funding data
                funding_data = funding_map.get(symbol_raw)
                if not funding_data:
                    # Skip symbols without funding data
                    continue

                # Convert symbol format: "BTC_USDT" -> "BTCUSDT"
                symbol = symbol_raw.replace("_", "")

                # Get next funding time timestamp from nextSettleTime (milliseconds)
                next_funding_time = None
                next_settle_ms = funding_data.get("nextSettleTime")
                if next_settle_ms is not None:
                    next_funding_time = next_settle_ms // 1000  # Convert milliseconds to seconds

                # Calculate funding rate percentage
                try:
                    funding_rate = float(funding_data.get("fundingRate", 0.0))
                    funding_rate_percent = funding_rate * 100
                except (ValueError, TypeError):
                    funding_rate_percent = 0.0

                # Extract volume (amount24 is already in USDT)
                try:
                    volume_24h_usdt = float(ticker.get("amount24", 0.0))
                except (ValueError, TypeError):
                    volume_24h_usdt = 0.0

                # Extract price data
                last_price = ticker.get("lastPrice")
                best_bid = ticker.get("bid1")
                best_ask = ticker.get("ask1")
                index_price = ticker.get("indexPrice")
                # MEXC uses "fairPrice" for mark price
                mark_price = ticker.get("fairPrice")

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
        Not used for MEXC futures (override update_redis_data instead)
        """
        return []


# Main execution function for standalone running
async def main():
    """Main function for running MEXC futures handler standalone"""
    import logging
    import asyncio

    # Setup logging
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create MEXC futures handler
    config = get_market_config('mexc', 'futures')
    if not config or not config.get('enabled', False):
        print("MEXC futures market data not enabled in configuration!")
        return

    handler = MEXCFuturesHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize MEXC futures handler!")
        return

    print("Starting MEXC Futures market data handler...")

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


