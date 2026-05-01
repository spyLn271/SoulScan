"""
Gate.io exchange implementation.
Sequential per-token fetching with rate limiting.
"""
import asyncio
from typing import List
import aiohttp

from .base import BaseExchange, CoinEntry


class GateioExchange(BaseExchange):
    """Gate.io coin fetcher - sequential per-token requests."""

    async def fetch_all_coins(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        # Step 1: Get all currencies
        currencies_url = f"{self.config.base_url}/spot/currencies"

        async with session.get(
            currencies_url,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as resp:
            currencies = await resp.json()

        total = len(currencies)
        self.logger.info(f"Total currencies: {total}")

        # Step 2: Fetch chain info for each currency
        results = []

        for i, c in enumerate(currencies):
            ccy = c.get("currency")

            try:
                chains_url = f"{self.config.base_url}/wallet/currency_chains"
                async with session.get(
                    chains_url,
                    params={"currency": ccy},
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as resp:
                    if resp.status == 429:
                        self.logger.warning(f"Rate limited, waiting {self.config.rate_limit_wait}s...")
                        await asyncio.sleep(self.config.rate_limit_wait)
                        async with session.get(
                            chains_url,
                            params={"currency": ccy},
                            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                        ) as retry:
                            chains = await retry.json()
                    else:
                        chains = await resp.json()

                if chains and isinstance(chains, list):
                    for chain in chains:
                        results.append(CoinEntry(
                            coin=ccy,
                            network=chain.get("chain", ""),
                            contract_address=chain.get("contract_address", "") or ""
                        ))

                if (i + 1) % 100 == 0:
                    self.logger.info(f"[{i + 1}/{total}] processed")

            except Exception as e:
                self.logger.warning(f"Failed to get chains for {ccy}: {e}")

            await asyncio.sleep(self.config.request_delay)

        return results
