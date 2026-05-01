#!/usr/bin/env python3
"""
KuCoin Market Data Handler Plugin

Fetches market data from KuCoin REST API and stores in Redis
"""

# Fix Python path for imports
import sys
import os

import asyncio
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class KucoinMarketDataHandler(BaseMarketDataHandler):
    """
    KuCoin market data handler - fetches spot market data from KuCoin API
    """

    def __init__(self, market_type: str = 'spot'):
        super().__init__('kucoin', market_type)

        # Get KuCoin-specific configuration
        config = get_market_config('kucoin', market_type)
        if not config:
            raise ValueError(f"KuCoin {market_type} configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info(f"Initialized KuCoin {market_type} handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse KuCoin API response format

        KuCoin Response format:
        {
            "code": "200000",
            "data": {
                "time": 1234567890,
                "ticker": [
                    {
                        "symbol": "BTC-USDT",
                        "buy": "50000.1",
                        "sell": "50000.2",
                        "last": "50000.15",
                        "volValue": "123456.78",
                        ...
                    }
                ]
            }
        }
        """
        # Check KuCoin API response code
        if response_data.get('code') != '200000':
            self.logger.error(f"Invalid API response from KuCoin. Code: {response_data.get('code')}, "
                            f"Message: {response_data.get('msg')}")
            return []

        # Extract ticker list from nested structure
        tickers_list = response_data.get('data', {}).get('ticker', [])
        if not isinstance(tickers_list, list):
            self.logger.error("Invalid data format in KuCoin API response")
            return []

        self.logger.debug(f"Found {len(tickers_list)} tickers from KuCoin")

        parsed_data = []
        for ticker in tickers_list:
            try:
                # Extract symbol and convert format (BTC-USDT -> BTCUSDT)
                native_symbol_raw = ticker.get("symbol")
                if not native_symbol_raw:
                    continue

                # Convert from BTC-USDT to BTCUSDT format
                symbol = native_symbol_raw.replace("-", "")

                # Extract volume data (volValue is the quote volume/turnover)
                try:
                    volume_24h_usdt = float(ticker.get("volValue", "0.0"))
                except (ValueError, TypeError):
                    volume_24h_usdt = 0.0

                # Extract price data
                # KuCoin uses 'buy' for best bid, 'sell' for best ask, 'last' for last price
                best_bid = ticker.get("buy")
                best_ask = ticker.get("sell")
                last_price = ticker.get("last")

                # Skip if critical data is missing
                if not best_bid or not best_ask or not last_price:
                    continue

                # Assemble data in consistent format
                symbol_data = {
                    'symbol': symbol,
                    'data': {
                        "24h_volume_usdt": volume_24h_usdt,
                        "best_bid": str(best_bid),
                        "best_ask": str(best_ask),
                        "lastPrice": str(last_price),
                    }
                }

                parsed_data.append(symbol_data)

            except Exception as e:
                self.logger.warning(f"Error processing ticker {ticker.get('symbol', 'unknown')}: {e}")
                continue

        return parsed_data


class KucoinSpotHandler(KucoinMarketDataHandler):
    """KuCoin Spot market data handler"""

    def __init__(self):
        super().__init__('spot')


# Main execution function for standalone running
async def main():
    """Main function for running KuCoin handler standalone"""
    import logging

    # Setup logging (only if not already configured)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create KuCoin handler
    config = get_market_config('kucoin', 'spot')
    if not config or not config.get('enabled', False):
        print("KuCoin spot market data not enabled in configuration!")
        return

    handler = KucoinSpotHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize KuCoin handler!")
        return

    print("Starting KuCoin Spot market data handler...")

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


