#!/usr/bin/env python3
"""
dYdX Futures Market Data Handler Plugin

Fetches futures market data from dYdX REST API and stores in Redis
Requires TWO API endpoints:
1. Perpetual markets (for market data and funding rates)
2. Orderbook (individual calls for each market to get bid/ask)

Uses async/aiohttp for concurrent orderbook requests
"""

# Fix Python path for imports
import sys
import os

import asyncio
import aiohttp
import json
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class DydxFuturesHandler(BaseMarketDataHandler):
    """
    dYdX futures market data handler
    Fetches from TWO endpoints concurrently using async/aiohttp
    """

    def __init__(self):
        super().__init__('dydx', 'futures')

        # Get dYdX futures configuration
        config = get_market_config('dydx', 'futures')
        if not config:
            raise ValueError("dYdX futures configuration not found")

        self.api_endpoint_markets = config['api_endpoint_markets']
        self.api_endpoint_orderbook = config['api_endpoint_orderbook']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info("Initialized dYdX futures handler")

    async def fetch_orderbook(self, session: aiohttp.ClientSession, ticker: str) -> Dict[str, Any]:
        """
        Fetch orderbook for a specific market to get best bid/ask
        """
        url = f"{self.api_endpoint_orderbook}{ticker}"

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()

                    # Extract best bid and ask
                    bids = data.get('bids', [])
                    asks = data.get('asks', [])

                    best_bid = bids[0].get('price') if bids and len(bids) > 0 else None
                    best_ask = asks[0].get('price') if asks and len(asks) > 0 else None

                    return {"best_bid": best_bid, "best_ask": best_ask}
        except Exception as e:
            self.logger.warning(f"Could not fetch orderbook for {ticker}: {e}")

        return {"best_bid": None, "best_ask": None}

    async def fetch_all_data_async(self) -> List[Dict[str, Any]]:
        """
        Async method to fetch all data from multiple endpoints concurrently
        """
        async with aiohttp.ClientSession() as session:
            try:
                # Step 1: Fetch perpetual markets data
                self.logger.debug("Fetching perpetual markets data...")
                async with session.get(self.api_endpoint_markets, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    markets_json = await response.json()

                    # Debug: log response structure
                    self.logger.debug(f"dYdX API response type: {type(markets_json)}")
                    if isinstance(markets_json, dict):
                        self.logger.debug(f"dYdX API response keys: {list(markets_json.keys())}")

                    if 'markets' not in markets_json:
                        self.logger.error(f"Invalid response structure from dYdX markets endpoint. Keys found: {list(markets_json.keys()) if isinstance(markets_json, dict) else 'not a dict'}")
                        return []

                    markets_dict = markets_json.get('markets', {})
                    if not isinstance(markets_dict, dict):
                        self.logger.error("Invalid markets data structure")
                        return []

                    self.logger.debug(f"Found {len(markets_dict)} markets from dYdX")

                    # Extract all tickers
                    tickers = list(markets_dict.keys())

                # Step 2: Fetch orderbooks concurrently for all markets
                self.logger.debug(f"Fetching orderbooks for {len(tickers)} markets concurrently...")
                tasks = [
                    self.fetch_orderbook(session, ticker)
                    for ticker in tickers
                ]
                orderbook_results = await asyncio.gather(*tasks)

                # Create orderbook map
                orderbook_map = {
                    tickers[i]: orderbook_results[i]
                    for i in range(len(tickers))
                }
                self.logger.debug(f"Fetched {len(orderbook_map)} orderbooks")

                # Step 3: Combine all data
                parsed_data = []
                for ticker, market_data in markets_dict.items():
                    try:
                        # Skip inactive markets
                        if market_data.get('status') != 'ACTIVE':
                            continue

                        # Convert ticker format: "BTC-USD" -> "BTCUSD"
                        symbol = ticker.replace("-", "")

                        # Get orderbook data
                        orderbook = orderbook_map.get(ticker, {})

                        # Calculate funding rate percentage
                        funding_rate_val = None
                        next_funding_rate = market_data.get('nextFundingRate')
                        if next_funding_rate is not None:
                            try:
                                funding_rate_val = float(next_funding_rate) * 100
                            except (ValueError, TypeError):
                                pass

                        # Extract volume (already in USD)
                        try:
                            volume_24h_usdt = float(market_data.get('volume24H', '0'))
                        except (ValueError, TypeError):
                            volume_24h_usdt = 0.0

                        # Extract price data
                        # dYdX doesn't provide lastPrice in these endpoints, use oraclePrice
                        oracle_price = market_data.get('oraclePrice')
                        last_price = oracle_price  # Use oracle price as last price
                        index_price = oracle_price
                        mark_price = None  # Not explicitly provided

                        best_bid = orderbook.get('best_bid')
                        best_ask = orderbook.get('best_ask')

                        # dYdX doesn't provide nextFundingTime
                        next_funding_time = None

                        symbol_data = {
                            'symbol': symbol,
                            'data': {
                                "24h_volume_usdt": volume_24h_usdt,
                                "best_bid": best_bid,
                                "best_ask": best_ask,
                                "lastPrice": last_price,
                                "indexPrice": index_price,
                                "markPrice": mark_price,
                                "funding_rate_percent": funding_rate_val,
                                "next_funding_time": next_funding_time
                            }
                        }

                        parsed_data.append(symbol_data)

                    except Exception as e:
                        self.logger.warning(f"Error processing market {ticker}: {e}")
                        continue

                return parsed_data

            except Exception as e:
                self.logger.error(f"Error fetching dYdX futures data: {e}")
                return []

    def update_redis_data(self):
        """
        Override base method to use async data fetching
        """
        try:
            # Run async fetch in sync context
            parsed_data = asyncio.run(self.fetch_all_data_async())

            if not parsed_data:
                self.logger.warning("No data returned from dYdX API")
                return False

            # Store in Redis
            count = self._store_data_in_redis(parsed_data)
            self.logger.info(f"Successfully updated {count} futures symbols in Redis")
            return True

        except Exception as e:
            self.logger.error(f"Unexpected error during dYdX update: {e}")
            return False

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Not used for dYdX futures (override update_redis_data instead)
        """
        return []


# Main execution function for standalone running
async def main():
    """Main function for running dYdX futures handler standalone"""
    import logging

    # Setup logging
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create dYdX futures handler
    config = get_market_config('dydx', 'futures')
    if not config or not config.get('enabled', False):
        print("dYdX futures market data not enabled in configuration!")
        return

    handler = DydxFuturesHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize dYdX futures handler!")
        return

    print("Starting dYdX Futures market data handler...")

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


