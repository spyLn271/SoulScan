#!/usr/bin/env python3
"""
Hyperliquid Futures Market Data Handler Plugin

Fetches futures market data from Hyperliquid API and stores in Redis
Uses POST request and has hourly funding (countdown to next hour)
"""

# Fix Python path for imports
import sys
import os

import requests
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class HyperliquidFuturesHandler(BaseMarketDataHandler):
    """
    Hyperliquid futures market data handler
    Uses POST request and USDC (not USDT) as quote currency
    Funding is hourly (top of each hour)
    """

    def __init__(self):
        super().__init__('hyperliquid', 'futures')

        # Get Hyperliquid futures configuration
        config = get_market_config('hyperliquid', 'futures')
        if not config:
            raise ValueError("Hyperliquid futures configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info("Initialized Hyperliquid futures handler")

    def get_hyperliquid_next_funding_timestamp(self) -> int:
        """
        Calculate timestamp of next hour (Hyperliquid has hourly funding)
        Returns: Unix timestamp in seconds
        """
        now_utc = datetime.now(timezone.utc)
        # Calculate the timestamp for the next hour
        next_hour = (now_utc + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

        return int(next_hour.timestamp())

    def update_redis_data(self):
        """
        Override base method to use POST request
        Hyperliquid API requires POST with specific payload
        """
        try:
            # Fetch data using POST request
            self.logger.debug(f"Fetching data from {self.api_endpoint} (POST)")
            payload = {"type": "metaAndAssetCtxs"}
            response = requests.post(self.api_endpoint, json=payload, timeout=30)
            response.raise_for_status()

            # Parse response
            parsed_data = self.parse_api_response(response.json())

            if not parsed_data:
                self.logger.warning("No data returned from API")
                return False

            # Store in Redis
            count = self._store_data_in_redis(parsed_data)
            self.logger.info(f"Successfully updated {count} futures symbols in Redis")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch data from Hyperliquid API: {e}")
            return False
        except json.JSONDecodeError:
            self.logger.error("Failed to decode idl from Hyperliquid API response")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during update: {e}")
            return False

    def parse_api_response(self, response_data: Any) -> List[Dict[str, Any]]:
        """
        Parse Hyperliquid API response

        Hyperliquid Response format:
        [
            {
                "universe": [
                    {"name": "BTC", "isDelisted": false, ...},
                    ...
                ]
            },
            [
                {"funding": "0.0001", "markPx": "50000.15", "dayNtlVlm": "123456.78", ...},
                ...
            ]
        ]

        First element is dict with 'universe' key, second is asset contexts array
        """
        try:
            if not isinstance(response_data, list) or len(response_data) < 2:
                self.logger.error("Invalid response format from Hyperliquid")
                return []

            # Hyperliquid response: first element is dict with 'universe' key
            universe = response_data[0]['universe']
            asset_contexts = response_data[1]

            if not isinstance(universe, list) or not isinstance(asset_contexts, list):
                self.logger.error("Invalid data structure in Hyperliquid response")
                return []

            self.logger.debug(f"Found {len(universe)} futures tickers from Hyperliquid")

            # Calculate next funding time once (same for all symbols)
            next_funding_time = self.get_hyperliquid_next_funding_timestamp()

            parsed_data = []
            for i in range(len(universe)):
                try:
                    if i >= len(asset_contexts):
                        break

                    symbol_meta = universe[i]
                    market_data = asset_contexts[i]

                    # Skip delisted symbols
                    if symbol_meta.get('isDelisted', False):
                        continue

                    symbol_name = symbol_meta.get('name')
                    if not symbol_name:
                        continue

                    # Hyperliquid uses USDC (not USDT)
                    symbol = symbol_name + "USDC"

                    # Extract market data
                    funding_rate = market_data.get("funding")
                    mark_price = market_data.get("markPx")
                    turnover_24h = market_data.get("dayNtlVlm")

                    # Calculate funding rate percentage (multiply by 100 for consistency)
                    funding_rate_percent = None
                    if funding_rate is not None:
                        try:
                            funding_rate_percent = float(funding_rate) * 100
                        except (ValueError, TypeError):
                            funding_rate_percent = None

                    # Hyperliquid doesn't provide separate bid/ask in this endpoint
                    best_bid = None
                    best_ask = None

                    # Assemble data in consistent format
                    symbol_data = {
                        'symbol': symbol,
                        'data': {
                            "24h_volume_usdt": turnover_24h,
                            "best_bid": best_bid,
                            "best_ask": best_ask,
                            "lastPrice": mark_price,
                            "funding_rate_percent": funding_rate_percent,
                            "next_funding_time": next_funding_time
                        }
                    }

                    parsed_data.append(symbol_data)

                except Exception as e:
                    self.logger.warning(f"Error processing ticker at index {i}: {e}")
                    continue

            return parsed_data

        except Exception as e:
            self.logger.error(f"Error parsing Hyperliquid response: {e}")
            return []


# Main execution function for standalone running
async def main():
    """Main function for running Hyperliquid futures handler standalone"""
    import logging
    import asyncio

    # Setup logging
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create Hyperliquid futures handler
    config = get_market_config('hyperliquid', 'futures')
    if not config or not config.get('enabled', False):
        print("Hyperliquid futures market data not enabled in configuration!")
        return

    handler = HyperliquidFuturesHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize Hyperliquid futures handler!")
        return

    print("Starting Hyperliquid Futures market data handler...")

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


