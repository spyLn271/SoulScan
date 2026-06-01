#!/usr/bin/env python3
"""
MEXC Market Data Handler Plugin

Fetches market data from MEXC REST API and stores in Redis
Demonstrates the market data plugin architecture
"""

# Fix Python path for imports
import sys
import os

import asyncio
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class MEXCMarketDataHandler(BaseMarketDataHandler):
    """
    MEXC market data handler - fetches spot market data from MEXC API
    """

    def __init__(self, market_type: str = 'spot'):
        super().__init__('mexc', market_type)

        # Get MEXC-specific configuration
        config = get_market_config('mexc', market_type)
        if not config:
            raise ValueError(f"MEXC {market_type} configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info(f"Initialized MEXC {market_type} handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse MEXC API response format

        MEXC Response format:
        [
            {
                "symbol": "BTC_USDT",
                "bidPrice": "50000.1",
                "askPrice": "50000.2",
                "lastPrice": "50000.15",
                "quoteVolume": "123456.78",
                ...
            }
        ]
        """
        # MEXC API returns a direct list. Validate that it's a list.
        if not isinstance(response_data, list):
            self.logger.error("Invalid API response from MEXC. Expected a list.")
            return []

        tickers_list = response_data
        self.logger.debug(f"Found {len(tickers_list)} tickers from MEXC")

        parsed_data = []
        for ticker in tickers_list:
            try:
                # Extract symbol and convert format (BTC_USDT -> BTCUSDT)
                native_symbol_raw = ticker.get("symbol")
                if not native_symbol_raw:
                    continue

                # Convert from BTC_USDT to BTCUSDT format
                symbol = native_symbol_raw.replace("_", "")

                # Extract price and volume data (keep as strings to preserve precision)
                # 'quoteVolume' is the quote volume
                try:
                    volume_24h_usdt = float(ticker.get("quoteVolume", "0.0"))
                except (ValueError, TypeError):
                    volume_24h_usdt = 0.0

                bid_str = str(ticker.get("bidPrice"))
                ask_str = str(ticker.get("askPrice"))
                last_price_str = str(ticker.get("lastPrice"))

                # Assemble data in consistent format
                symbol_data = {
                    'symbol': symbol,
                    'data': {
                        "24h_volume_usdt": volume_24h_usdt,
                        "best_bid": bid_str,
                        "best_ask": ask_str,
                        "lastPrice": last_price_str,
                    }
                }

                parsed_data.append(symbol_data)

            except Exception as e:
                self.logger.warning(f"Error processing ticker {ticker.get('symbol', 'unknown')}: {e}")
                continue

        return parsed_data


class MEXCSpotHandler(MEXCMarketDataHandler):
    """MEXC Spot market data handler"""

    def __init__(self):
        super().__init__('spot')


# Main execution function for standalone running
async def main():
    """Main function for running MEXC handler standalone"""
    import logging

    # Setup logging (only if not already configured)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create MEXC handler
    config = get_market_config('mexc', 'spot')
    if not config or not config.get('enabled', False):
        print("MEXC spot market data not enabled in configuration!")
        return

    handler = MEXCSpotHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize MEXC handler!")
        return

    print("Starting MEXC Spot market data handler...")

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


