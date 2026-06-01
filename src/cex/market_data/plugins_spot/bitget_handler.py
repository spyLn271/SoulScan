#!/usr/bin/env python3
"""
Bitget Market Data Handler Plugin

Fetches market data from Bitget REST API and stores in Redis
Demonstrates the market data plugin architecture with manual coin mapping
"""

# Fix Python path for imports
import sys
import os

import asyncio
from typing import Dict, Any, List

from src.cex.market_data.core.base_handler import BaseMarketDataHandler
from src.cex.market_data.config import get_market_config


class BitgetMarketDataHandler(BaseMarketDataHandler):
    """
    Bitget market data handler - fetches spot market data from Bitget API
    """

    # Manual mapping for coins where 'coinRealName' differs from 'coinName'
    # This map contains coins where the 'coinRealName' is different from the 'coinName'.
    # We cannot fetch this dynamically because the endpoint is protected by Cloudflare.
    MANUAL_COIN_REAL_NAME_MAP = {
        "TON": "TONCOIN",
        "BOMB": "BOMBNEW",
        "TOMA": "TOMANEW",
        "DEGEN": "$DEGEN",
        "SOPH": "SOPHNEW",
        "AIN": "AINBSC",
        "PRIME": "PRIME1",
        "ZK": "ZKSYNC",
        "RED": "REDNEW",
        "KAIA": "KLAY",
        "BOOM": "BOOMNEW",
        "ZKJ": "ZK",
        "ALT": "$ALT",
        "THE": "THENA",
        "MAX": "MAXNEW",
        "AI": "$AI",
        "AXL": "WAXL",
        "ANLOG": "ANALOG",
        "MEME": "MEMECOIN",
        "VELODROME": "VELO",
        "X": "XNEW",
        "TAIKO": "TKO",
        "PUMP": "PUMPFUN",
        "BLUE": "BLUENEW",
        "SOON": "SOONNEW",
        "NEIROETH": "NEIRO",
        "PUMPBTC": "PUMPNEW",
    }

    def __init__(self, market_type: str = 'spot'):
        super().__init__('bitget', market_type)

        # Get Bitget-specific configuration
        config = get_market_config('bitget', market_type)
        if not config:
            raise ValueError(f"Bitget {market_type} configuration not found")

        self.api_endpoint = config['api_endpoint']
        self.redis_key = config['redis_key']
        self.update_interval = config['update_interval']

        self.logger.info(f"Initialized Bitget {market_type} handler")

    def parse_api_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Bitget API response format

        Bitget Response format:
        {
            "code": "00000",
            "msg": "success",
            "requestTime": 1703123456789,
            "data": [
                {
                    "symbol": "TONUSDT",
                    "bidPr": "2.123",
                    "askPr": "2.124",
                    "lastPr": "2.1235",
                    "quoteVolume": "1234567.89",
                    ...
                }
            ]
        }
        """
        if response_data.get('code') != '00000':
            self.logger.error(f"Invalid API response from Bitget. Code: {response_data.get('code')}, Message: {response_data.get('msg')}")
            return []

        tickers_list = response_data.get('data', [])
        if not isinstance(tickers_list, list):
            self.logger.error("Invalid data format in Bitget Tickers API response.")
            return []

        self.logger.debug(f"Found {len(tickers_list)} tickers from Bitget")

        parsed_data = []
        for ticker in tickers_list:
            try:
                native_symbol = ticker.get("symbol")
                # We are only interested in USDT pairs for this logic
                if not native_symbol or not native_symbol.endswith("USDT"):
                    continue

                # Extract base currency (e.g., "TON" from "TONUSDT")
                base_currency = native_symbol[:-4]
                quote_currency = "USDT"

                # Check our manual map for a special 'real name'.
                # If it's in our map (like TON), use the value (TONCOIN).
                # If not, the real name is the same as the base currency (like BTC).
                real_name_base = self.MANUAL_COIN_REAL_NAME_MAP.get(base_currency, base_currency)

                # Construct the final real name symbol (e.g., "TONCOINUSDT" or "BTCUSDT")
                final_real_name = f"{real_name_base}{quote_currency}"

                # Extract volume (quoteVolume is the 24h volume in quote currency)
                try:
                    volume_24h_usdt = float(ticker.get("quoteVolume", "0.0"))
                except (ValueError, TypeError):
                    volume_24h_usdt = 0.0

                # Extract price data
                best_bid = ticker.get("bidPr")
                best_ask = ticker.get("askPr")
                last_price = ticker.get("lastPr")

                # Calculate scale based on price precision
                scale = self._calculate_scale(best_bid, best_ask, last_price)

                # Assemble data in consistent format with coin_real_name and scale
                symbol_data = {
                    'symbol': native_symbol,  # Use original ticker symbol as the key
                    'data': {
                        "coin_real_name": final_real_name,
                        "24h_volume_usdt": volume_24h_usdt,
                        "best_bid": best_bid,
                        "best_ask": best_ask,
                        "lastPrice": last_price,
                        "scale": scale,
                    }
                }

                parsed_data.append(symbol_data)

            except Exception as e:
                self.logger.warning(f"Error processing ticker {ticker.get('symbol', 'unknown')}: {e}")
                continue

        return parsed_data

    def _calculate_scale(self, best_bid, best_ask, last_price) -> str:
        """
        Calculate scale based on price precision from Bitget ticker data

        Logic:
        1. Find the maximum number of decimal places among price values
        2. Construct scale string based on maximum decimals found
        3. If no price data available, fall back to default "0.01"

        Returns scale string like "0.01", "0.001", "1", etc.
        """
        default_scale = "0.01"  # Fallback when no price data available

        # Start with -1 to distinguish between "no prices found" and "prices are whole numbers"
        max_decimals = -1

        # Check all price fields
        for price in [last_price, best_ask, best_bid]:
            if price is not None:
                # A price field was found, so minimum precision is 0 decimal places
                if max_decimals == -1:
                    max_decimals = 0

                price_str = str(price)
                if '.' in price_str:
                    # Update max_decimals with the longest decimal part found
                    decimal_places = len(price_str.split('.')[-1])
                    max_decimals = max(max_decimals, decimal_places)

        if max_decimals == -1:
            # No price keys found, use default
            return default_scale
        elif max_decimals == 0:
            # For whole numbers (e.g., 10, 9, 8), the scale is '1'
            return "1"
        else:
            # For decimals, format the scale string (e.g., 2 decimals -> "0.01", 6 decimals -> "0.000001")
            if max_decimals == 1:
                return "0.1"
            else:
                return f"0.{'0' * (max_decimals - 1)}1"


class BitgetSpotHandler(BitgetMarketDataHandler):
    """Bitget Spot market data handler"""

    def __init__(self):
        super().__init__('spot')


# Main execution function for standalone running
async def main():
    """Main function for running Bitget handler standalone"""
    import logging

    # Setup logging (only if not already configured)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        )

    # Create Bitget handler
    config = get_market_config('bitget', 'spot')
    if not config or not config.get('enabled', False):
        print("Bitget spot market data not enabled in configuration!")
        return

    handler = BitgetSpotHandler()

    # Initialize Redis connection
    if not handler.initialize():
        print("Failed to initialize Bitget handler!")
        return

    print("Starting Bitget Spot market data handler...")

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


