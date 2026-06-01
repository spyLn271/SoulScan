"""
KuCoin exchange implementation.
"""
from typing import List
import aiohttp

from .base import BaseExchange, CoinEntry


class KucoinExchange(BaseExchange):
    """KuCoin coin fetcher - public endpoint."""

    async def fetch_all_coins(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        url = f"{self.config.base_url}/api/v3/currencies"

        async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as resp:
            data = await resp.json()

        if data.get("code") != "200000":
            raise Exception(f"KuCoin API error: {data.get('msg')}")

        results = []
        for coin in data["data"]:
            coin_name = coin.get("currency", "")
            for chain in coin.get("chains") or []:
                results.append(CoinEntry(
                    coin=coin_name,
                    network=chain.get("chainName", ""),
                    contract_address=chain.get("contractAddress", "") or ""
                ))

        return results
