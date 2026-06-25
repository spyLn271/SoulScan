"""
BitMart exchange implementation.
"""
from typing import List
import aiohttp

from .base import BaseExchange, CoinEntry


class BitmartExchange(BaseExchange):
    """BitMart coin fetcher - public currencies endpoint.

    `/account/v1/currencies` returns one entry per (currency, network) with a
    `contract_address` field (null for native assets).
    """

    async def fetch_all_coins(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        url = f"{self.config.base_url}/account/v1/currencies"

        async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as resp:
            data = await resp.json()

        if data.get("code") != 1000:
            raise Exception(f"BitMart API error: {data.get('message', 'Unknown error')}")

        results = []
        for c in data.get("data", {}).get("currencies", []):
            results.append(CoinEntry(
                coin=c.get("currency", ""),
                network=c.get("network", ""),
                contract_address=c.get("contract_address", "") or ""
            ))

        return results
