#!/usr/bin/env python3
"""
CoinEx Futures Market Data Handler Plugin

Fetches futures market data from CoinEx REST API and stores in Redis
Uses single endpoint that returns all ticker data including funding rates
"""

# Fix Python path for imports
import sys
import os

import time
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class CoinExFuturesHandler(BaseMarketDataHandler):
    """
    CoinEx futures market data handler
    Single endpoint returns all data including funding rates
    """

    def __init__(self):
        super().__init__('coinex', 'futures')

        # Get CoinEx futures configuration
        config = get_market_config('coinex', 'futures')
        if not config:
            raise ValueError("CoinEx futures configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info("Initialized CoinEx futures handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse CoinEx futures API response

        CoinEx Response format:
        {
            "code": 0,
            "data": {
                "date": 1760287933770,
                "ticker": {
                    "SYRUPUSDT": {
                        "vol": "493163.00000000000000000000",
                        "low": "0.31820000000000000000",
                        "high": "0.3754",
                        "last": "0.3714",
                        "buy": "0.3703",
                        "sell": "0.3726",
                        "funding_time": 427,  # minutes until next funding
                        "funding_rate_next": "-0.00163812",
                        "index_price": "0.3715",
                        "sign_price": "0.3707"
                    }
                }
            }
        }
        """
        # Check CoinEx API response code
        if response_data.get("code") != 0:
            self.logger.error(f"Invalid API response from CoinEx: code={response_data.get('code')}")
            return []

        data = response_data.get("data", {})
        ticker_dict = data.get("ticker", {})

        if not isinstance(ticker_dict, dict):
            self.logger.error("Invalid ticker data structure in CoinEx response")
            return []

        self.logger.debug(f"Found {len(ticker_dict)} futures tickers from CoinEx")

        parsed_data = []
        for symbol, ticker in ticker_dict.items():
            try:
                # Skip metadata entries with _SIGNPRICE or _INDEXPRICE suffix
                if symbol.endswith('_SIGNPRICE') or symbol.endswith('_INDEXPRICE'):
                    continue

                # Symbol is already in correct format (e.g., "SYRUPUSDT")
                if not symbol:
                    continue

                # Calculate 24h volume in USDT using formula: vol × ((low + high) / 2)
                try:
                    vol = float(ticker.get("vol", "0"))
                    low = float(ticker.get("low", "0"))
                    high = float(ticker.get("high", "0"))

                    if low > 0 and high > 0:
                        avg_price = (low + high) / 2
                        volume_24h_usdt = vol * avg_price
                    else:
                        volume_24h_usdt = 0.0
                except (ValueError, TypeError, ZeroDivisionError):
                    volume_24h_usdt = 0.0

                # Calculate funding rate percentage
                try:
                    funding_rate = float(ticker.get("funding_rate_next", "0"))
                    funding_rate_percent = funding_rate * 100
                except (ValueError, TypeError):
                    funding_rate_percent = 0.0

                # Calculate next funding time from funding_time (duration in MINUTES)
                # API returns countdown in minutes; result must be on exact HOUR boundary
                next_funding_time = None
                funding_time_minutes = ticker.get("funding_time")
                if funding_time_minutes is not None:
                    try:
                        funding_time_int = int(funding_time_minutes)
                        if funding_time_int > 0:
                            # Convert minutes to seconds and add to current time
                            current_time = int(time.time())
                            approximate_time = current_time + (funding_time_int * 60)
                            # Round to nearest hour boundary (funding always on exact hour)
                            next_funding_time = round(approximate_time / 3600) * 3600
                    except (ValueError, TypeError):
                        pass

                # Extract price data
                last_price = ticker.get("last")
                best_bid = ticker.get("buy")
                best_ask = ticker.get("sell")
                index_price = ticker.get("index_price")
                # CoinEx uses "sign_price" for mark price
                mark_price = ticker.get("sign_price")

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
                self.logger.warning(f"Error processing ticker {symbol}: {e}")
                continue

        return parsed_data


# Main execution function for standalone running
async def main():
    """Main function for running CoinEx futures handler standalone"""
    import logging
    import asyncio

    # Setup logging
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create CoinEx futures handler
    config = get_market_config('coinex', 'futures')
    if not config or not config.get('enabled', False):
        print("CoinEx futures market data not enabled in configuration!")
        return

    handler = CoinExFuturesHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize CoinEx futures handler!")
        return

    print("Starting CoinEx Futures market data handler...")

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


