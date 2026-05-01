#!/usr/bin/env python3
"""
Bitget Futures Market Data Handler Plugin

Fetches futures market data from Bitget REST API and stores in Redis
Single endpoint provides all necessary futures data
"""

# Fix Python path for imports
import sys
import os

import asyncio
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class BitgetFuturesHandler(BaseMarketDataHandler):
    """
    Bitget futures market data handler - fetches USDT perpetual futures data from Bitget API
    Includes funding rate, mark price, and index price
    Note: Bitget API does not provide next_funding_time, so it will be set to None
    """

    def __init__(self):
        super().__init__('bitget', 'futures')

        # Get Bitget futures configuration
        config = get_market_config('bitget', 'futures')
        if not config:
            raise ValueError("Bitget futures configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info("Initialized Bitget futures handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Bitget API response for futures market data

        Bitget Futures Response format:
        {
            "code": "00000",
            "msg": "success",
            "requestTime": 1760659403836,
            "data": [
                {
                    "symbol": "BTCUSDT",
                    "lastPr": "107991.2",
                    "bidPr": "107991.2",
                    "askPr": "107991.3",
                    "usdtVolume": "11173603689.740969318",
                    "indexPrice": "108039.7839733153943421",
                    "markPrice": "107991.2",
                    "fundingRate": "0.000075",
                    ...
                }
            ]
        }
        """
        # Check for successful response
        if response_data.get("code") != "00000" or "data" not in response_data:
            self.logger.error(f"Invalid API response from Bitget: {response_data.get('msg', 'Unknown error')}")
            return []

        tickers_list = response_data.get("data", [])
        if not isinstance(tickers_list, list):
            self.logger.error("Invalid data format in Bitget API response")
            return []

        self.logger.debug(f"Found {len(tickers_list)} tickers from Bitget futures")

        parsed_data = []
        for ticker in tickers_list:
            try:
                # Extract symbol
                symbol = ticker.get("symbol")
                if not symbol:
                    continue

                # Filter for USDT pairs only (already filtered by productType=USDT-FUTURES, but double-check)
                if not symbol.endswith("USDT"):
                    continue

                # Extract price and volume data
                last_price = ticker.get("lastPr", "0.0")
                bid_price = ticker.get("bidPr", "0.0")
                ask_price = ticker.get("askPr", "0.0")
                volume_24h_usdt = ticker.get("usdtVolume", "0.0")
                index_price = ticker.get("indexPrice", "0.0")
                mark_price = ticker.get("markPrice", "0.0")
                funding_rate_raw = ticker.get("fundingRate", "0.0")

                # Convert funding rate to percentage (multiply by 100)
                try:
                    funding_rate = float(funding_rate_raw)
                    funding_rate_percent = funding_rate * 100
                except (ValueError, TypeError):
                    funding_rate_percent = 0.0

                # Bitget API does not provide next_funding_time, set to None
                next_funding_time = None

                # Assemble data in standardized format
                symbol_data = {
                    'symbol': symbol,
                    'data': {
                        "24h_volume_usdt": volume_24h_usdt,
                        "best_bid": bid_price,
                        "best_ask": ask_price,
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


# Main execution function for standalone running
async def main():
    """Main function for running Bitget futures handler standalone"""
    import logging

    # Setup logging
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create Bitget futures handler
    config = get_market_config('bitget', 'futures')
    if not config or not config.get('enabled', False):
        print("Bitget futures market data not enabled in configuration!")
        return

    handler = BitgetFuturesHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize Bitget futures handler!")
        return

    print("Starting Bitget Futures market data handler...")

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


