"""
Gate.io exchange implementation.

BULK: GET /spot/currencies returns, for EVERY currency, a `chains[]` array whose entries carry the
chain `name` and the on-chain contract `addr` — so a single call yields all (coin, network, address)
tuples. (The old per-currency /wallet/currency_chains path made ~5150 sequential calls, ~2h/cycle.)
"""
from typing import List
import aiohttp

from .base import BaseExchange, CoinEntry


class GateioExchange(BaseExchange):
    """Gate.io coin fetcher — single bulk /spot/currencies call; chains[] carry name + contract addr."""

    async def fetch_all_coins(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        url = f"{self.config.base_url}/spot/currencies"
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as resp:
            currencies = await resp.json()

        results: List[CoinEntry] = []
        for c in currencies:
            ccy = c.get("currency")
            if not ccy:
                continue
            for chain in (c.get("chains") or []):
                results.append(CoinEntry(
                    coin=ccy,
                    network=chain.get("name", "") or "",
                    contract_address=chain.get("addr", "") or "",
                ))
        self.logger.info(
            f"Fetched {len(results)} chain entries from {len(currencies)} currencies (bulk)"
        )
        return results
