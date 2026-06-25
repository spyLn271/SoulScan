"""
Binance exchange implementation.
"""
import hmac
import hashlib
import time
from typing import List
import aiohttp

from .base import BaseExchange, CoinEntry


class BinanceExchange(BaseExchange):
    """Binance coin fetcher with HMAC-SHA256 authentication."""

    def _sign(self, query_string: str) -> str:
        """Generate HMAC-SHA256 signature."""
        return hmac.new(
            self.config.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    async def fetch_all_coins(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        endpoint = "/sapi/v1/capital/config/getall"
        timestamp = int(time.time() * 1000)
        query_string = f"timestamp={timestamp}"
        signature = self._sign(query_string)

        url = f"{self.config.base_url}{endpoint}?{query_string}&signature={signature}"
        headers = {"X-MBX-APIKEY": self.config.api_key}

        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as resp:
            data = await resp.json()

        if "code" in data:
            raise Exception(f"Binance API error: {data}")

        results = []
        for coin_info in data:
            coin = coin_info.get("coin", "")
            for network in coin_info.get("networkList", []):
                results.append(CoinEntry(
                    coin=coin,
                    network=network.get("network", ""),
                    contract_address=network.get("contractAddress", "") or ""
                ))

        return results
