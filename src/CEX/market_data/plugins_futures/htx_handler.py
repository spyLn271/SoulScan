#!/usr/bin/env python3
"""
HTX (Huobi) Futures Market Data Handler Plugin

Fetches futures market data from HTX REST API and stores in Redis
Requires TWO API endpoints:
1. Batch ticker (for price/volume data and list of all contracts)
2. Funding rate (individual calls for each contract)

Uses async/aiohttp for concurrent funding rate requests
"""

# Fix Python path for imports
import sys
import os

import asyncio
import aiohttp
import json
from typing import Dict, Any, List

from src.CEX.market_data.core.base_handler import BaseMarketDataHandler
from src.CEX.market_data.config import get_market_config


class HTXFuturesHandler(BaseMarketDataHandler):
    """
    HTX futures market data handler
    Fetches from TWO endpoints concurrently using async/aiohttp
    Funding times: Every 8 hours (00:00, 08:00, 16:00 UTC)
    """

    def __init__(self):
        super().__init__('htx', 'futures')

        # Get HTX futures configuration
        config = get_market_config('htx', 'futures')
        if not config:
            raise ValueError("HTX futures configuration not found")

        self.api_endpoint_ticker = config['api_endpoint_ticker']
        self.api_endpoint_funding = config['api_endpoint_funding']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        # HTTP headers required by HTX API
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }

        self.logger.info("Initialized HTX futures handler")

    async def fetch_funding_rate(self, session: aiohttp.ClientSession, contract_code: str) -> Dict[str, Any]:
        """
        Fetch funding rate for a specific contract
        """
        url = f"{self.api_endpoint_funding}?contract_code={contract_code}"

        try:
            async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json(content_type=None)
                    if data.get('status') == 'ok':
                        return data.get('data', {})
        except Exception as e:
            self.logger.warning(f"Could not fetch funding rate for {contract_code}: {e}")

        return {}

    async def fetch_all_data_async(self) -> List[Dict[str, Any]]:
        """
        Async method to fetch all data from TWO endpoints concurrently
        """
        async with aiohttp.ClientSession() as session:
            try:
                # Step 1: Fetch batch ticker data (contains all contracts and their data)
                self.logger.debug("Fetching batch ticker data...")
                async with session.get(self.api_endpoint_ticker, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    ticker_json = await response.json(content_type=None)

                    if ticker_json.get('status') != 'ok':
                        self.logger.error(f"Failed to fetch tickers: {ticker_json.get('err-msg')}")
                        return []

                    tickers_list = ticker_json.get('ticks', [])
                    self.logger.debug(f"Found {len(tickers_list)} tickers")

                    # Extract all contract codes from tickers
                    contract_codes = [t['contract_code'] for t in tickers_list if 'contract_code' in t]

                # Step 2: Fetch funding rates concurrently for all contracts
                self.logger.debug(f"Fetching funding rates for {len(contract_codes)} contracts concurrently...")
                tasks = [
                    self.fetch_funding_rate(session, contract_code)
                    for contract_code in contract_codes
                ]
                funding_results = await asyncio.gather(*tasks)

                # Create funding rate map
                funding_map = {
                    contract_codes[i]: funding_results[i]
                    for i in range(len(contract_codes))
                    if funding_results[i]
                }
                self.logger.debug(f"Fetched {len(funding_map)} funding rates")

                # Step 3: Combine all data
                parsed_data = []
                for ticker in tickers_list:
                    try:
                        contract_code = ticker.get('contract_code')
                        if not contract_code:
                            continue

                        # Get funding data
                        funding = funding_map.get(contract_code, {})

                        # Convert contract_code: "BTC-USDT" -> "BTCUSDT"
                        symbol = contract_code.replace("-", "")

                        # Calculate funding rate percentage
                        funding_rate_val = None
                        if funding and funding.get('funding_rate'):
                            try:
                                funding_rate_val = float(funding['funding_rate']) * 100
                            except (ValueError, TypeError):
                                pass

                        # Get next funding time timestamp from funding_time (milliseconds)
                        next_funding_time = None
                        funding_time_ms = funding.get('funding_time')
                        if funding_time_ms:
                            try:
                                next_funding_time = int(funding_time_ms) // 1000  # Convert milliseconds to seconds
                            except (ValueError, TypeError):
                                pass

                        # Extract volume (trade_turnover is already in USDT)
                        try:
                            volume_24h_usdt = float(ticker.get('trade_turnover', '0'))
                        except (ValueError, TypeError):
                            volume_24h_usdt = 0.0

                        # Extract prices from ticker
                        # bid and ask are arrays: [price, amount]
                        bid_price = None
                        ask_price = None
                        bid_data = ticker.get('bid')
                        ask_data = ticker.get('ask')

                        if bid_data and isinstance(bid_data, list) and len(bid_data) > 0:
                            bid_price = bid_data[0]

                        if ask_data and isinstance(ask_data, list) and len(ask_data) > 0:
                            ask_price = ask_data[0]

                        last_price = ticker.get('close')  # 'close' is last price in HTX

                        # HTX batch ticker doesn't provide index/mark price
                        index_price = None
                        mark_price = None

                        symbol_data = {
                            'symbol': symbol,
                            'data': {
                                "24h_volume_usdt": volume_24h_usdt,
                                "best_bid": bid_price,
                                "best_ask": ask_price,
                                "lastPrice": last_price,
                                "indexPrice": index_price,
                                "markPrice": mark_price,
                                "funding_rate_percent": funding_rate_val,
                                "next_funding_time": next_funding_time
                            }
                        }

                        parsed_data.append(symbol_data)

                    except Exception as e:
                        self.logger.warning(f"Error processing ticker {ticker.get('contract_code', 'unknown')}: {e}")
                        continue

                return parsed_data

            except Exception as e:
                self.logger.error(f"Error fetching HTX futures data: {e}")
                return []

    def update_redis_data(self):
        """
        Override base method to use async data fetching
        """
        try:
            # Run async fetch in sync context
            parsed_data = asyncio.run(self.fetch_all_data_async())

            if not parsed_data:
                self.logger.warning("No data returned from HTX API")
                return False

            # Store in Redis
            count = self._store_data_in_redis(parsed_data)
            self.logger.info(f"Successfully updated {count} futures symbols in Redis")
            return True

        except Exception as e:
            self.logger.error(f"Unexpected error during HTX update: {e}")
            return False

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Not used for HTX futures (override update_redis_data instead)
        """
        return []


# Main execution function for standalone running
async def main():
    """Main function for running HTX futures handler standalone"""
    import logging

    # Setup logging
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create HTX futures handler
    config = get_market_config('htx', 'futures')
    if not config or not config.get('enabled', False):
        print("HTX futures market data not enabled in configuration!")
        return

    handler = HTXFuturesHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize HTX futures handler!")
        return

    print("Starting HTX Futures market data handler...")

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


