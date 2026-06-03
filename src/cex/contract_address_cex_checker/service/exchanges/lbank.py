"""
LBank exchange implementation.

NOTE: LBank's public API does NOT expose on-chain contract addresses. Its
withdraw-config endpoint (`/v2/withdrawConfigs.do`) only returns
`assetCode`/`chain`/fees — verified live, zero address-bearing fields across all
~2000 entries. So this fetcher cannot contribute addresses to the contract index,
and is intentionally a no-op that returns an empty list (kept so the checker's
exchange set matches the producer set, and so a future LBank address source can be
slotted in here without touching the rest of the pipeline).
"""
from typing import List
import aiohttp

from .base import BaseExchange, CoinEntry


class LbankExchange(BaseExchange):
    """LBank coin fetcher - NO contract addresses available from the public API."""

    async def fetch_all_coins(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        # Touch the endpoint so failures are still visible/logged, but return
        # nothing: there is no contract-address field to extract.
        try:
            url = f"{self.config.base_url}/v2/withdrawConfigs.do"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as resp:
                await resp.read()
        except Exception as e:
            self.logger.debug(f"LBank reachability check failed (non-fatal): {e}")
        self.logger.info("LBank public API exposes no contract addresses; contributing 0 entries")
        return []
