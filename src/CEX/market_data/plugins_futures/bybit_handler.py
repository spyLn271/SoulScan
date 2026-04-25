#!/usr/bin/env python3
"""
Bybit Futures Market Data Handler Plugin

Fetches futures market data from Bybit REST API and stores in Redis
Includes funding rate, next funding timestamp, mark price, and index price
"""

# Fix Python path for imports
import sys
import os

from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List

from src.CEX.market_data.core.base_handler import BaseMarketDataHandler
from src.CEX.market_data.config import get_market_config


class BybitFuturesHandler(BaseMarketDataHandler):
    """
    Bybit futures market data handler - fetches perpetual futures data from Bybit API
    Includes funding rate, countdown timer, mark price, and index price
    """

    def __init__(self):
        super().__init__('bybit', 'futures')

        # Get Bybit futures configuration
        config = get_market_config('bybit', 'futures')
        if not config:
            raise ValueError("Bybit futures configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info("Initialized Bybit futures handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Bybit API response for futures market data

        Bybit Futures Response format:
        {
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": [
                    {
                        "symbol": "BTCUSDT",
                        "bid1Price": "50000.1",
                        "ask1Price": "50000.2",
                        "lastPrice": "50000.15",
                        "indexPrice": "50000.10",
                        "markPrice": "50000.12",
                        "turnover24h": "123456.78",
                        "fundingRate": "0.0001",
                        "nextFundingTime": "1234567890000",
                        "deliveryTime": "0",
                        ...
                    }
                ]
            }
        }
        """
        if response_data.get("retCode") != 0 or "result" not in response_data or "list" not in response_data["result"]:
            self.logger.error(f"Invalid API response from Bybit: {response_data.get('retMsg', 'Unknown error')}")
            return []

        tickers_list = response_data["result"]["list"]
        self.logger.debug(f"Found {len(tickers_list)} tickers from Bybit futures")

        parsed_data = []
        for ticker in tickers_list:
            try:
                # Extract symbol
                symbol = ticker.get("symbol")
                if not symbol:
                    continue

                # Filter for perpetuals only (deliveryTime is "0")
                if ticker.get("deliveryTime") != "0":
                    continue

                # Filter for USDT pairs only
                if not symbol.endswith("USDT"):
                    continue

                # Extract price and volume data (keep as strings to preserve precision)
                volume_24h_usdt_str = ticker.get("turnover24h", "0.0")
                bid_str = ticker.get("bid1Price", "0.0")
                ask_str = ticker.get("ask1Price", "0.0")
                last_price_str = ticker.get("lastPrice", "0.0")
                index_price_str = ticker.get("indexPrice", "0.0")
                mark_price_str = ticker.get("markPrice", "0.0")
                funding_rate_str = ticker.get("fundingRate", "0.0")
                next_funding_ms_str = ticker.get("nextFundingTime")

                # Calculate funding rate percentage using Decimal for precision
                try:
                    funding_rate_decimal = Decimal(funding_rate_str)
                    funding_rate_percent_str = str(funding_rate_decimal * 100)
                except InvalidOperation:
                    funding_rate_percent_str = "0.0"

                # Get next funding time as timestamp (in seconds)
                next_funding_time = None
                if next_funding_ms_str and next_funding_ms_str.isdigit():
                    next_funding_ms = int(next_funding_ms_str)
                    next_funding_time = next_funding_ms // 1000  # Convert milliseconds to seconds

                # Assemble data in consistent format
                symbol_data = {
                    'symbol': symbol,
                    'data': {
                        "24h_volume_usdt": volume_24h_usdt_str,
                        "best_bid": bid_str,
                        "best_ask": ask_str,
                        "lastPrice": last_price_str,
                        "indexPrice": index_price_str,
                        "markPrice": mark_price_str,
                        "funding_rate_percent": funding_rate_percent_str,
                        "next_funding_time": next_funding_time
                    }
                }

                parsed_data.append(symbol_data)

            except Exception as e:
                self.logger.warning(f"Error processing ticker {ticker.get('symbol', 'unknown')}: {e}")
                continue

        return parsed_data


# Main execution function for standalone running
async def main():
    """Main function for running Bybit futures handler standalone"""
    import logging
    import asyncio

    # Setup logging (only if not already configured)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create Bybit futures handler
    config = get_market_config('bybit', 'futures')
    if not config or not config.get('enabled', False):
        print("Bybit futures market data not enabled in configuration!")
        return

    handler = BybitFuturesHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize Bybit futures handler!")
        return

    print("Starting Bybit Futures market data handler...")

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


