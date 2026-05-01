"""
Abstract base class for exchange fetchers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Optional
import aiohttp
import asyncio
import logging

from ..config import ExchangeConfig


@dataclass
class CoinEntry:
    """Standardized coin/network/contract data."""
    coin: str
    network: str
    contract_address: str  # Empty string if not available

    def to_dict(self) -> dict:
        return asdict(self)


class BaseExchange(ABC):
    """Abstract base class for all exchange implementations."""

    def __init__(self, config: ExchangeConfig):
        self.config = config
        self.logger = logging.getLogger(f"exchange.{config.name}")

    @abstractmethod
    async def fetch_all_coins(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        """
        Fetch all coins with their networks and contract addresses.

        Returns:
            List of CoinEntry objects

        Raises:
            Exception on API errors (caller handles retries)
        """
        pass

    async def fetch_with_retry(self, session: aiohttp.ClientSession) -> Optional[List[CoinEntry]]:
        """Fetch with retry logic and error handling."""
        for attempt in range(self.config.max_retries):
            try:
                result = await self.fetch_all_coins(session)
                self.logger.info(f"Fetched {len(result)} entries")
                return result
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)

        self.logger.error(f"All {self.config.max_retries} attempts failed")
        return None
