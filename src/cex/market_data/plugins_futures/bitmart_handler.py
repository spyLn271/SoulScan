#!/usr/bin/env python3
"""
BitMart Futures Market Data Handler Plugin

Fetches futures market data from BitMart REST API and stores in Redis
Single endpoint provides all necessary futures data
"""

# Fix Python path for imports
import sys
import os

import asyncio
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class BitMartFuturesHandler(BaseMarketDataHandler):
    """
    BitMart futures market data handler - fetches perpetual futures data from BitMart API
    Includes funding rate, next funding time, mark price, and index price
    """

    def __init__(self):
        super().__init__('bitmart', 'futures')

        # Get BitMart futures configuration
        config = get_market_config('bitmart', 'futures')
        if not config:
            raise ValueError("BitMart futures configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info("Initialized BitMart futures handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse BitMart API response for futures market data

        BitMart Futures Response format:
        {
            "code": 1000,
            "message": "Ok",
            "data": {
                "symbols": [
                    {
                        "symbol": "BTCUSDT",
                        "last_price": "108044.4",
                        "turnover_24h": "12647998675.9666",
                        "index_price": "108096.52130435",
                        "funding_rate": "0.000021",
                        "funding_time": 1760659200000,
                        "expire_timestamp": 0,
                        ...
                    }
                ]
            }
        }
        """
        # Check for successful response
        if response_data.get("code") != 1000 or "data" not in response_data:
            self.logger.error(f"Invalid API response from BitMart: {response_data.get('message', 'Unknown error')}")
            return []

        # Extract symbols array from nested data structure
        data_obj = response_data.get("data", {})
        if not isinstance(data_obj, dict) or "symbols" not in data_obj:
            self.logger.error("Invalid data structure in BitMart API response")
            return []

        symbols_list = data_obj.get("symbols", [])
        if not isinstance(symbols_list, list):
            self.logger.error("Invalid symbols list in BitMart API response")
            return []

        self.logger.debug(f"Found {len(symbols_list)} symbols from BitMart futures")

        parsed_data = []
        for contract in symbols_list:
            try:
                # Extract symbol
                symbol = contract.get("symbol")
                if not symbol:
                    continue

                # Filter for USDT perpetuals only (expire_timestamp == 0 means perpetual)
                expire_timestamp = contract.get("expire_timestamp", -1)
                if expire_timestamp != 0:
                    continue

                # Filter for USDT pairs only
                if not symbol.endswith("USDT"):
                    continue

                # Extract price and volume data
                last_price = contract.get("last_price", "0.0")
                turnover_24h = contract.get("turnover_24h", "0.0")
                index_price = contract.get("index_price", "0.0")
                funding_rate_raw = contract.get("funding_rate", "0.0")
                funding_time_ms = contract.get("funding_time")

                # Convert funding rate to percentage (multiply by 100)
                try:
                    funding_rate = float(funding_rate_raw)
                    funding_rate_percent = funding_rate * 100
                except (ValueError, TypeError):
                    funding_rate_percent = 0.0

                # Convert funding time from milliseconds to seconds
                next_funding_time = None
                if funding_time_ms is not None:
                    try:
                        next_funding_time = int(funding_time_ms) // 1000
                    except (ValueError, TypeError):
                        pass

                # BitMart doesn't provide separate bid/ask in this endpoint, use last_price
                # Also doesn't provide separate mark_price, use index_price
                symbol_data = {
                    'symbol': symbol,
                    'data': {
                        "24h_volume_usdt": turnover_24h,
                        "best_bid": last_price,
                        "best_ask": last_price,
                        "lastPrice": last_price,
                        "indexPrice": index_price,
                        "markPrice": index_price,  # Use index_price as mark_price
                        "funding_rate_percent": funding_rate_percent,
                        "next_funding_time": next_funding_time
                    }
                }

                parsed_data.append(symbol_data)

            except Exception as e:
                self.logger.warning(f"Error processing contract {contract.get('symbol', 'unknown')}: {e}")
                continue

        return parsed_data


# Main execution function for standalone running
async def main():
    """Main function for running BitMart futures handler standalone"""
    import logging

    # Setup logging
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create BitMart futures handler
    config = get_market_config('bitmart', 'futures')
    if not config or not config.get('enabled', False):
        print("BitMart futures market data not enabled in configuration!")
        return

    handler = BitMartFuturesHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize BitMart futures handler!")
        return

    print("Starting BitMart Futures market data handler...")

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


