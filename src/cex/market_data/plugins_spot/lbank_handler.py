#!/usr/bin/env python3
"""
LBank Market Data Handler Plugin

Fetches market data from LBank REST API and stores in Redis
Demonstrates the market data plugin architecture
"""

# Fix Python path for imports
import sys
import os

import asyncio
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class LBankMarketDataHandler(BaseMarketDataHandler):
    """
    LBank market data handler - fetches spot market data from LBank API
    """

    def __init__(self, market_type: str = 'spot'):
        super().__init__('lbank', market_type)

        # Get LBank-specific configuration
        config = get_market_config('lbank', market_type)
        if not config:
            raise ValueError(f"LBank {market_type} configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info(f"Initialized LBank {market_type} handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse LBank API response format

        LBank Response format:
        {
            "data": [
                {
                    "symbol": "btc_usdt",
                    "ticker": {
                        "buy": "50000.1",
                        "sell": "50000.2",
                        "latest": "50000.15",
                        "turnover": "123456.78",
                        ...
                    }
                }
            ]
        }
        """
        # LBank API returns a list in the 'data' field
        tickers_list = response_data.get('data', [])
        if not isinstance(tickers_list, list):
            self.logger.error("Invalid data format in LBank API response. Expected a list in the 'data' key.")
            return []

        self.logger.debug(f"Found {len(tickers_list)} tickers from LBank")

        parsed_data = []
        for item in tickers_list:
            try:
                # Extract symbol and ticker data
                native_symbol_raw = item.get("symbol")
                ticker = item.get("ticker", {})  # The actual data is in a nested object
                if not native_symbol_raw or not ticker:
                    continue

                # Convert from btc_usdt to btcusdt format
                symbol = native_symbol_raw.replace("_", "")

                # Extract price and volume data
                try:
                    volume_24h_usdt = float(ticker.get("turnover", 0.0))
                except (ValueError, TypeError):
                    volume_24h_usdt = 0.0

                bid_str = str(ticker.get("buy"))
                ask_str = str(ticker.get("sell"))
                last_price_str = str(ticker.get("latest"))

                # Calculate accuracy (LBank-specific field)
                # LBank returns numbers, so convert to string for decimal calculation
                max_decimals = max(
                    self.get_decimal_places(bid_str),
                    self.get_decimal_places(ask_str),
                    self.get_decimal_places(last_price_str)
                )
                accuracy_val = pow(10, -max_decimals)
                accuracy_str = f"{accuracy_val:.{max_decimals}f}" if max_decimals > 0 else "1"

                # Assemble data in consistent format
                symbol_data = {
                    'symbol': symbol,
                    'data': {
                        "24h_volume_usdt": volume_24h_usdt,
                        "best_bid": bid_str,
                        "best_ask": ask_str,
                        "lastPrice": last_price_str,
                        "accuracy": accuracy_str  # LBank uses 'accuracy' field
                    }
                }

                parsed_data.append(symbol_data)

            except Exception as e:
                self.logger.warning(f"Error processing ticker {item.get('symbol', 'unknown')}: {e}")
                continue

        return parsed_data


class LBankSpotHandler(LBankMarketDataHandler):
    """LBank Spot market data handler"""

    def __init__(self):
        super().__init__('spot')


# Main execution function for standalone running
async def main():
    """Main function for running LBank handler standalone"""
    import logging

    # Setup logging (only if not already configured)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create LBank handler
    config = get_market_config('lbank', 'spot')
    if not config or not config.get('enabled', False):
        print("LBank spot market data not enabled in configuration!")
        return

    handler = LBankSpotHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize LBank handler!")
        return

    print("Starting LBank Spot market data handler...")

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


