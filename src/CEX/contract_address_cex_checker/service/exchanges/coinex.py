"""
CoinEx exchange implementation. CEX
"""
from typing import List
import aiohttp

from .base import BaseExchange, CoinEntry


class CoinexExchange(BaseExchange):
    """CoinEx coin fetcher - public endpoint."""

    async def fetch_all_coins(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        endpoint = "/assets/info"
        url = f"{self.config.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as resp:
            data = await resp.json()

        if data.get("code") != 0:
            raise Exception(f"CoinEx API error: {data.get('message', 'Unknown error')}")

        results = []
        for coin in data.get("data", []):
            coin_name = coin.get("short_name", "")
            for chain in coin.get("chain_info", []):
                results.append(CoinEntry(
                    coin=coin_name,
                    network=chain.get("chain_name", ""),
                    contract_address=chain.get("identity", "") or ""
                ))

        return results
