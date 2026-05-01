#!/usr/bin/env python3
"""
KuCoin Futures Market Data Handler Plugin

Fetches futures market data from KuCoin REST API and stores in Redis
Includes symbol mapping (XBT -> BTC) and funding rate information
Requires TWO API endpoints: contracts and tickers (for bid/ask data)
"""

# Fix Python path for imports
import sys
import os

import time
import requests
import json
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


# Symbol mapping for known exceptions
TICKER_EXCEPTION_MAP = {
    'XBT': 'BTC',
    # Add other exceptions here if discovered
}


class KucoinFuturesHandler(BaseMarketDataHandler):
    """
    KuCoin futures market data handler
    Includes symbol mapping and funding rate information
    """

    def __init__(self):
        super().__init__('kucoin', 'futures')

        # Get KuCoin futures configuration
        config = get_market_config('kucoin', 'futures')
        if not config:
            raise ValueError("KuCoin futures configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.api_endpoint_tickers = config['api_endpoint_tickers']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info("Initialized KuCoin futures handler")

    def update_redis_data(self):
        """
        Override base method to fetch from TWO endpoints
        Combines contract data with ticker data for bid/ask prices
        """
        try:
            # Fetch contracts data (for funding, volume, prices, countdown)
            self.logger.debug(f"Fetching contracts data from {self.api_endpoint}")
            contracts_response = requests.get(self.api_endpoint, timeout=30)
            contracts_response.raise_for_status()
            contracts_data = contracts_response.json()

            if contracts_data.get("code") != "200000" or "data" not in contracts_data:
                self.logger.error(f"Invalid API response from KuCoin contracts: {contracts_data.get('msg', 'Unknown error')}")
                return False

            contracts_list = contracts_data.get("data", [])

            # Fetch tickers data (for bid/ask prices)
            self.logger.debug(f"Fetching tickers data from {self.api_endpoint_tickers}")
            tickers_response = requests.get(self.api_endpoint_tickers, timeout=30)
            tickers_response.raise_for_status()
            tickers_data = tickers_response.json()

            if tickers_data.get("code") != "200000" or "data" not in tickers_data:
                self.logger.error(f"Invalid API response from KuCoin tickers: {tickers_data.get('msg', 'Unknown error')}")
                return False

            tickers_list = tickers_data.get("data", [])

            self.logger.debug(f"Found {len(contracts_list)} contracts and {len(tickers_list)} tickers")

            # Create lookup dictionary for tickers by symbol
            tickers_map = {ticker['symbol']: ticker for ticker in tickers_list}

            # Process and combine data
            parsed_data = self._parse_combined_data(contracts_list, tickers_map)

            if not parsed_data:
                self.logger.warning("No data returned from combined parsing")
                return False

            # Store in Redis
            count = self._store_data_in_redis(parsed_data)
            self.logger.info(f"Successfully updated {count} futures symbols in Redis")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch data from KuCoin API: {e}")
            return False
        except json.JSONDecodeError:
            self.logger.error("Failed to decode idl from KuCoin API response")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during update: {e}")
            return False

    def _parse_combined_data(self, contracts_list: List, tickers_map: Dict) -> List[Dict[str, Any]]:
        """
        Parse combined contract and ticker data

        Contracts provide: funding, volume, prices, countdown
        Tickers provide: bestBidPrice, bestAskPrice
        """
        parsed_data = []

        for contract in contracts_list:
            try:
                # Filter for perpetuals only (FFWCSX) and USDT quote currency
                if contract.get("type") != "FFWCSX" or contract.get("quoteCurrency") != "USDT":
                    continue

                native_symbol = contract.get("symbol")
                base_currency = contract.get("baseCurrency")
                quote_currency = contract.get("quoteCurrency")

                if not all([native_symbol, base_currency, quote_currency]):
                    continue

                # Apply symbol mapping (XBT -> BTC)
                common_base = TICKER_EXCEPTION_MAP.get(base_currency, base_currency)
                symbol = f"{common_base}{quote_currency}"  # e.g., BTCUSDT

                # Calculate funding rate percentage
                try:
                    funding_rate = float(contract.get("fundingFeeRate", "0.0"))
                    funding_rate_percent = funding_rate * 100
                except (ValueError, TypeError):
                    funding_rate_percent = 0.0

                # Get next funding time from nextFundingRateDateTime (absolute timestamp in milliseconds)
                next_funding_time = None
                next_funding_datetime_ms = contract.get("nextFundingRateDateTime")
                if next_funding_datetime_ms is not None:
                    # Convert milliseconds to seconds
                    next_funding_time = next_funding_datetime_ms // 1000

                # Extract volume
                try:
                    volume_24h_usdt = float(contract.get("turnoverOf24h", "0.0"))
                except (ValueError, TypeError):
                    volume_24h_usdt = 0.0

                # Extract prices from contracts
                try:
                    last_price = float(contract.get("lastTradePrice", "0.0"))
                except (ValueError, TypeError):
                    last_price = 0.0

                try:
                    index_price = float(contract.get("indexPrice", "0.0"))
                except (ValueError, TypeError):
                    index_price = 0.0

                try:
                    mark_price = float(contract.get("markPrice", "0.0"))
                except (ValueError, TypeError):
                    mark_price = 0.0

                # Get bid/ask from tickers (matched by native symbol)
                best_bid = 0.0
                best_ask = 0.0
                ticker_details = tickers_map.get(native_symbol)
                if ticker_details:
                    try:
                        best_bid = float(ticker_details.get("bestBidPrice", "0.0"))
                    except (ValueError, TypeError):
                        best_bid = 0.0

                    try:
                        best_ask = float(ticker_details.get("bestAskPrice", "0.0"))
                    except (ValueError, TypeError):
                        best_ask = 0.0

                # Assemble data in consistent format
                symbol_data = {
                    'symbol': symbol,
                    'data': {
                        "subscription_name": native_symbol,  # Original KuCoin symbol
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
                self.logger.warning(f"Error processing contract {contract.get('symbol', 'unknown')}: {e}")
                continue

        return parsed_data

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Not used for KuCoin futures (override update_redis_data instead)
        """
        return []


# Main execution function for standalone running
async def main():
    """Main function for running KuCoin futures handler standalone"""
    import logging
    import asyncio

    # Setup logging
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create KuCoin futures handler
    config = get_market_config('kucoin', 'futures')
    if not config or not config.get('enabled', False):
        print("KuCoin futures market data not enabled in configuration!")
        return

    handler = KucoinFuturesHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize KuCoin futures handler!")
        return

    print("Starting KuCoin Futures market data handler...")

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


