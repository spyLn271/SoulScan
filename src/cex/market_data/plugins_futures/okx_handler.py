#!/usr/bin/env python3
"""
OKX Futures Market Data Handler Plugin

Fetches futures market data from OKX REST API and stores in Redis
Requires multiple API endpoints for complete data (tickers, funding rate, mark price, index price)
Uses async/aiohttp for concurrent requests
"""

# Fix Python path for imports
import sys
import os

import asyncio
import aiohttp
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class OkxFuturesHandler(BaseMarketDataHandler):
    """
    OKX futures market data handler
    Fetches from multiple endpoints concurrently using async/aiohttp
    Funding times: 00:00, 08:00, 16:00 UTC (8-hour cycles)
    """

    def __init__(self):
        super().__init__('okx', 'futures')

        # Get OKX futures configuration
        config = get_market_config('okx', 'futures')
        if not config:
            raise ValueError("OKX futures configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        # Additional OKX endpoints
        self.funding_rate_api = "https://www.okx.com/api/v5/public/funding-rate"
        self.mark_price_api = "https://www.okx.com/api/v5/public/mark-price?instType=SWAP"
        self.index_tickers_api = "https://www.okx.com/api/v5/public/index-tickers"

        self.logger.info("Initialized OKX futures handler")

    def get_okx_next_funding_timestamp(self) -> int:
        """
        Calculate timestamp of next OKX funding time (00, 08, 16 UTC)
        Returns: Unix timestamp in seconds
        """
        now_utc = datetime.now(timezone.utc)
        funding_hours = [0, 8, 16]

        # Find the next funding hour
        next_funding_hour = -1
        for hour in funding_hours:
            if now_utc.hour < hour:
                next_funding_hour = hour
                break

        # If past the last funding hour, next one is tomorrow at 00:00
        if next_funding_hour == -1:
            next_funding_time = (now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            next_funding_time = now_utc.replace(hour=next_funding_hour, minute=0, second=0, microsecond=0)

        return int(next_funding_time.timestamp())

    async def fetch_additional_data(self, session: aiohttp.ClientSession, inst_id: str) -> Dict[str, Any]:
        """
        Fetch funding rate and index price for a specific instrument
        """
        funding_url = f"{self.funding_rate_api}?instId={inst_id}"
        index_url = f"{self.index_tickers_api}?instId={inst_id}"

        funding_data, index_price = None, None

        try:
            async with session.get(funding_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('code') == '0' and data.get('data'):
                        funding_data = data['data'][0]

            async with session.get(index_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('code') == '0' and data.get('data'):
                        index_price = data['data'][0].get('idxPx')

        except Exception as e:
            self.logger.warning(f"Could not fetch additional data for {inst_id}: {e}")

        return {"funding_data": funding_data, "index_price": index_price}

    async def fetch_all_data_async(self) -> List[Dict[str, Any]]:
        """
        Async method to fetch all data from multiple endpoints concurrently
        """
        async with aiohttp.ClientSession() as session:
            try:
                # Fetch tickers and mark prices concurrently
                self.logger.debug("Fetching initial ticker and mark price data...")
                tickers_task = session.get(self.api_endpoint, timeout=aiohttp.ClientTimeout(total=10))
                mark_price_task = session.get(self.mark_price_api, timeout=aiohttp.ClientTimeout(total=10))

                tickers_response, mark_price_response = await asyncio.gather(tickers_task, mark_price_task)

                tickers_json = await tickers_response.json()
                mark_price_json = await mark_price_response.json()

                if tickers_json.get('code') != '0' or mark_price_json.get('code') != '0':
                    self.logger.error(f"API error. Ticker: {tickers_json.get('msg')}, MarkPrice: {mark_price_json.get('msg')}")
                    return []

                tickers_list = tickers_json.get('data', [])
                mark_price_map = {item['instId']: item['markPx'] for item in mark_price_json.get('data', [])}
                self.logger.debug(f"Found {len(tickers_list)} tickers and {len(mark_price_map)} mark prices")

                # Fetch funding rates and index prices concurrently for all symbols
                self.logger.debug("Fetching funding rates and index prices concurrently...")
                tasks = [
                    self.fetch_additional_data(session, ticker['instId'])
                    for ticker in tickers_list if 'instId' in ticker
                ]
                additional_results = await asyncio.gather(*tasks)
                additional_data_map = {
                    tickers_list[i]['instId']: data
                    for i, data in enumerate(additional_results) if i < len(tickers_list)
                }
                self.logger.debug("All additional data fetched")

                # Calculate fallback next funding time (used if API doesn't provide fundingTime)
                fallback_next_funding_time = self.get_okx_next_funding_timestamp()

                # Process and combine all data
                parsed_data = []
                for ticker in tickers_list:
                    inst_id = ticker.get("instId")
                    if not inst_id:
                        continue

                    # Convert symbol format: BTC-USDT-SWAP -> BTCUSDT
                    symbol = inst_id.replace("-SWAP", "").replace("-", "")

                    additional_data = additional_data_map.get(inst_id, {})
                    funding_data = additional_data.get("funding_data")

                    # Calculate funding rate percentage and get next funding time from API
                    funding_rate_val = None
                    next_funding_time = None
                    if funding_data:
                        if funding_data.get('fundingRate'):
                            try:
                                funding_rate_val = float(funding_data['fundingRate']) * 100
                            except (ValueError, TypeError):
                                pass
                        if funding_data.get('fundingTime'):
                            try:
                                # Convert from milliseconds to seconds
                                next_funding_time = int(funding_data['fundingTime']) // 1000
                            except (ValueError, TypeError):
                                pass

                    # Get markPrice and calculate volume in USDT
                    mark_price = mark_price_map.get(inst_id)
                    volume_base = ticker.get("volCcy24h")
                    if volume_base and mark_price:
                        try:
                            volume_usdt = float(volume_base) * float(mark_price)
                        except (ValueError, TypeError):
                            volume_usdt = volume_base
                    else:
                        volume_usdt = volume_base

                    symbol_data = {
                        'symbol': symbol,
                        'data': {
                            "24h_volume_usdt": volume_usdt,
                            "best_bid": ticker.get("bidPx"),
                            "best_ask": ticker.get("askPx"),
                            "lastPrice": ticker.get("last"),
                            "indexPrice": additional_data.get("index_price"),
                            "markPrice": mark_price,
                            "funding_rate_percent": funding_rate_val,
                            "next_funding_time": next_funding_time or fallback_next_funding_time
                        }
                    }

                    parsed_data.append(symbol_data)

                return parsed_data

            except Exception as e:
                self.logger.error(f"Error fetching OKX futures data: {e}")
                return []

    def update_redis_data(self):
        """
        Override base method to use async data fetching
        """
        try:
            # Run async fetch in sync context
            parsed_data = asyncio.run(self.fetch_all_data_async())

            if not parsed_data:
                self.logger.warning("No data returned from OKX API")
                return False

            # Store in Redis
            count = self._store_data_in_redis(parsed_data)
            self.logger.info(f"Successfully updated {count} futures symbols in Redis")
            return True

        except Exception as e:
            self.logger.error(f"Unexpected error during OKX update: {e}")
            return False

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Not used for OKX futures (override update_redis_data instead)
        """
        return []


# Main execution function for standalone running
async def main():
    """Main function for running OKX futures handler standalone"""
    import logging

    # Setup logging
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create OKX futures handler
    config = get_market_config('okx', 'futures')
    if not config or not config.get('enabled', False):
        print("OKX futures market data not enabled in configuration!")
        return

    handler = OkxFuturesHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize OKX futures handler!")
        return

    print("Starting OKX Futures market data handler...")

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


