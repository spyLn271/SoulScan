"""
Bybit exchange implementation.
"""
import hmac
import hashlib
import time
from typing import List
import aiohttp

from .base import BaseExchange, CoinEntry


class BybitExchange(BaseExchange):
    """Bybit coin fetcher with HMAC-SHA256 authentication."""

    def _sign(self, sign_str: str) -> str:
        """Generate HMAC-SHA256 signature."""
        return hmac.new(
            self.config.secret_key.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    async def fetch_all_coins(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        endpoint = "/v5/asset/coin/query-info"
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
        query_string = ""

        # Bybit V5 signature: timestamp + api_key + recv_window + query_string
        sign_str = timestamp + self.config.api_key + recv_window + query_string
        signature = self._sign(sign_str)

        headers = {
            "X-BAPI-API-KEY": self.config.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window
        }

        url = f"{self.config.base_url}{endpoint}"

        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as resp:
            data = await resp.json()

        if data.get("retCode") != 0:
            raise Exception(f"Bybit API error: {data.get('retMsg')}")

        results = []
        for coin_data in data["result"]["rows"]:
            coin = coin_data.get("coin", "")
            for chain in coin_data.get("chains", []):
                results.append(CoinEntry(
                    coin=coin,
                    network=chain.get("chain", ""),
                    contract_address=chain.get("contractAddress", "") or ""
                ))

        return results
