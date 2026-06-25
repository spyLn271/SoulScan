"""
BingX exchange implementation.
"""
import hmac
import hashlib
import time
from typing import List
import aiohttp

from .base import BaseExchange, CoinEntry


class BingxExchange(BaseExchange):
    """BingX coin fetcher with HMAC-SHA256 authentication."""

    def _sign(self, params: str) -> str:
        """Generate HMAC-SHA256 signature."""
        return hmac.new(
            self.config.secret_key.encode('utf-8'),
            params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    async def fetch_all_coins(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        endpoint = "/openApi/wallets/v1/capital/config/getall"
        timestamp = int(time.time() * 1000)
        params = f"timestamp={timestamp}"
        signature = self._sign(params)

        url = f"{self.config.base_url}{endpoint}?{params}&signature={signature}"
        headers = {"X-BX-APIKEY": self.config.api_key}

        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as resp:
            data = await resp.json()

        if data.get("code") != 0:
            raise Exception(f"BingX API error: {data}")

        results = []
        for coin_data in data.get("data", []):
            coin = coin_data.get("coin", "")
            for net in coin_data.get("networkList", []):
                results.append(CoinEntry(
                    coin=coin,
                    network=net.get("network", ""),
                    contract_address=net.get("contractAddress", "") or ""
                ))

        return results
