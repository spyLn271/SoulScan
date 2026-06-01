#!/usr/bin/env python3
"""
Bybit Market Data Handler Plugin

Fetches market data from Bybit REST API and stores in Redis
Demonstrates the market data plugin architecture
"""

# Fix Python path for imports
import sys
import os

import asyncio
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class BybitMarketDataHandler(BaseMarketDataHandler):
    """
    Bybit market data handler - fetches spot/futures market data from Bybit API
    """

    def __init__(self, market_type: str = 'spot'):
        super().__init__('bybit', market_type)

        # Get Bybit-specific configuration
        config = get_market_config('bybit', market_type)
        if not config:
            raise ValueError(f"Bybit {market_type} configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info(f"Initialized Bybit {market_type} handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Bybit API response format

        Bybit Response format:
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
                        "turnover24h": "123456.78",
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
        self.logger.debug(f"Found {len(tickers_list)} tickers from Bybit")

        parsed_data = []
        for ticker in tickers_list:
            try:
                # Extract symbol (already in correct format: BTCUSDT)
                symbol = ticker.get("symbol")
                if not symbol:
                    continue

                # Extract price and volume data (keep as strings to preserve precision)
                volume_24h_usdt_str = ticker.get("turnover24h", "0.0")
                bid_str = ticker.get("bid1Price", "0.0")
                ask_str = ticker.get("ask1Price", "0.0")
                last_price_str = ticker.get("lastPrice", "0.0")

                # Calculate dumpScale (Bybit-specific field - maximum decimal places)
                bid_scale = self.get_decimal_places(bid_str)
                ask_scale = self.get_decimal_places(ask_str)
                last_price_scale = self.get_decimal_places(last_price_str)
                dump_scale = max(bid_scale, ask_scale, last_price_scale)

                # Assemble data in consistent format
                symbol_data = {
                    'symbol': symbol,
                    'data': {
                        "24h_volume_usdt": volume_24h_usdt_str,  # Keep as string to preserve precision
                        "best_bid": bid_str,
                        "best_ask": ask_str,
                        "lastPrice": last_price_str,
                        "dumpScale": dump_scale  # Bybit uses 'dumpScale' field
                    }
                }

                parsed_data.append(symbol_data)

            except Exception as e:
                self.logger.warning(f"Error processing ticker {ticker.get('symbol', 'unknown')}: {e}")
                continue

        return parsed_data


class BybitSpotHandler(BybitMarketDataHandler):
    """Bybit Spot market data handler"""

    def __init__(self):
        super().__init__('spot')


class BybitFuturesHandler(BybitMarketDataHandler):
    """Bybit Futures market data handler"""

    def __init__(self):
        super().__init__('futures')


# Main execution function for standalone running
async def main():
    """Main function for running Bybit handler standalone"""
    import logging

    # Setup logging (only if not already configured)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create Bybit handler
    config = get_market_config('bybit', 'spot')
    if not config or not config.get('enabled', False):
        print("Bybit spot market data not enabled in configuration!")
        return

    handler = BybitSpotHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize Bybit handler!")
        return

    print("Starting Bybit Spot market data handler...")

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


