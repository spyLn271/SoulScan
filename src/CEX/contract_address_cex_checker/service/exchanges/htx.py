"""
HTX (Huobi) exchange implementation. CEX
"""
from typing import List
import aiohttp

from .base import BaseExchange, CoinEntry


class HtxExchange(BaseExchange):
    """HTX coin fetcher - public endpoint."""

    async def fetch_all_coins(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        url = f"{self.config.base_url}/v2/reference/currencies"

        async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as resp:
            data = await resp.json()

        if data.get("code") != 200:
            raise Exception(f"HTX API error: {data}")

        results = []
        for currency in data["data"]:
            coin = currency.get("currency", "").upper()
            for chain in currency.get("chains", []):
                results.append(CoinEntry(
                    coin=coin,
                    network=chain.get("baseChain", ""),
                    contract_address=chain.get("contractAddress", "") or ""
                ))

        return results
