#!/usr/bin/env python3
"""
Gate.io Futures Market Data Handler Plugin

Fetches futures market data from Gate.io REST API and stores in Redis
Requires TWO API endpoints: tickers and contracts (for funding data)
"""

# Fix Python path for imports
import sys
import os

import requests
import json
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class GateioFuturesHandler(BaseMarketDataHandler):
    """
    Gate.io futures market data handler
    Fetches from TWO endpoints: tickers and contracts for complete data
    """

    def __init__(self):
        super().__init__('gateio', 'futures')

        # Get Gate.io futures configuration
        config = get_market_config('gateio', 'futures')
        if not config:
            raise ValueError("Gate.io futures configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.api_endpoint_contracts = config['api_endpoint_contracts']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info("Initialized Gate.io futures handler")

    def update_redis_data(self):
        """
        Override base method to fetch from TWO endpoints
        Combines ticker data with contract data for funding information
        """
        try:
            # Fetch tickers data
            self.logger.debug(f"Fetching ticker data from {self.api_endpoint}")
            tickers_response = requests.get(self.api_endpoint, timeout=30)
            tickers_response.raise_for_status()
            tickers_list = tickers_response.json()

            if not isinstance(tickers_list, list):
                self.logger.error("Invalid API response from Gate.io tickers endpoint")
                return False

            # Fetch contracts data
            self.logger.debug(f"Fetching contracts data from {self.api_endpoint_contracts}")
            contracts_response = requests.get(self.api_endpoint_contracts, timeout=30)
            contracts_response.raise_for_status()
            contracts_list = contracts_response.json()

            if not isinstance(contracts_list, list):
                self.logger.error("Invalid API response from Gate.io contracts endpoint")
                return False

            self.logger.debug(f"Found {len(tickers_list)} tickers and {len(contracts_list)} contracts")

            # Create lookup dictionary for contracts
            contracts_map = {contract['name']: contract for contract in contracts_list}

            # Process and combine data
            parsed_data = self._parse_combined_data(tickers_list, contracts_map)

            if not parsed_data:
                self.logger.warning("No data returned from combined parsing")
                return False

            # Store in Redis
            count = self._store_data_in_redis(parsed_data)
            self.logger.info(f"Successfully updated {count} futures symbols in Redis")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch data from Gate.io API: {e}")
            return False
        except json.JSONDecodeError:
            self.logger.error("Failed to decode idl from Gate.io API response")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during update: {e}")
            return False

    def _parse_combined_data(self, tickers_list: List, contracts_map: Dict) -> List[Dict[str, Any]]:
        """
        Parse combined ticker and contract data

        Gate.io Futures Ticker format:
        {
            "contract": "ME_USDT",
            "highest_bid": "50000.1",
            "lowest_ask": "50000.2",
            "last": "50000.15",
            "funding_rate": "0.0001",
            "volume_24h_quote": "123456.78",
            "mark_price": "50000.12",
            "index_price": "50000.10",
            ...
        }

        Contract format (for funding_next_apply):
        {
            "name": "ME_USDT",
            "funding_next_apply": 1234567890,
            ...
        }
        """
        parsed_data = []

        for ticker in tickers_list:
            try:
                # Extract symbol (convert ME_USDT to MEUSDT)
                native_symbol_raw = ticker.get("contract")
                if not native_symbol_raw:
                    continue

                symbol = native_symbol_raw.replace("_", "")

                # Get next funding time timestamp from contract data
                next_funding_time = None
                contract_details = contracts_map.get(native_symbol_raw)
                if contract_details:
                    funding_next_apply = contract_details.get("funding_next_apply")
                    if funding_next_apply:
                        next_funding_time = funding_next_apply  # Already in seconds

                # Calculate funding rate percentage
                try:
                    funding_rate = float(ticker.get("funding_rate", "0.0"))
                    funding_rate_percent = funding_rate * 100
                except (ValueError, TypeError):
                    funding_rate_percent = 0.0

                # Calculate volume
                try:
                    volume_24h_usdt = float(ticker.get("volume_24h_quote", "0.0"))
                except (ValueError, TypeError):
                    volume_24h_usdt = 0.0

                # Extract price data
                best_bid = ticker.get("highest_bid")
                best_ask = ticker.get("lowest_ask")
                last_price = ticker.get("last")
                index_price = ticker.get("index_price")
                mark_price = ticker.get("mark_price")

                # Assemble data in consistent format
                symbol_data = {
                    'symbol': symbol,
                    'data': {
                        "24h_volume_usdt": f"{volume_24h_usdt:,.2f}",
                        "best_bid": best_bid,
                        "best_ask": best_ask,
                        "lastPrice": last_price,
                        "indexPrice": index_price,
                        "markPrice": mark_price,
                        "funding_rate_percent": funding_rate_percent,
                        "next_funding_time": next_funding_time
                    }
                }

                parsed_data.append(symbol_data)

            except Exception as e:
                self.logger.warning(f"Error processing ticker {ticker.get('contract', 'unknown')}: {e}")
                continue

        return parsed_data

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Not used for Gate.io futures (override update_redis_data instead)
        """
        return []


# Main execution function for standalone running
async def main():
    """Main function for running Gate.io futures handler standalone"""
    import logging
    import asyncio

    # Setup logging
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create Gate.io futures handler
    config = get_market_config('gateio', 'futures')
    if not config or not config.get('enabled', False):
        print("Gate.io futures market data not enabled in configuration!")
        return

    handler = GateioFuturesHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize Gate.io futures handler!")
        return

    print("Starting Gate.io Futures market data handler...")

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


