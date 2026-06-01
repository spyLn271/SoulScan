"""
Bitget exchange implementation.
"""
from typing import List
import aiohttp

from .base import BaseExchange, CoinEntry


class BitgetExchange(BaseExchange):
    """Bitget coin fetcher - public endpoint."""

    async def fetch_all_coins(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        url = f"{self.config.base_url}/api/v2/spot/public/coins"

        async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as resp:
            data = await resp.json()

        if data.get("code") != "00000":
            raise Exception(f"Bitget API error: {data.get('msg')}")

        results = []
        for coin_data in data["data"]:
            coin = coin_data.get("coin", "")
            for chain in coin_data.get("chains", []):
                results.append(CoinEntry(
                    coin=coin,
                    network=chain.get("chain", ""),
                    contract_address=chain.get("contractAddress", "") or ""
                ))

        return results
