"""
Redis updater service - fetches from all exchanges and updates Redis.
Runs in a loop: update -> sleep 20 min -> repeat lol
"""
import asyncio
import logging
from typing import Dict, List, Optional
import aiohttp

from .config import UPDATE_INTERVAL_SECONDS, FetchStrategy
from .exchanges import get_all_exchanges
from .exchanges.base import BaseExchange, CoinEntry
from .redis_client import RedisClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("updater")


class UpdaterService:
    """Main service that orchestrates fetching and storing."""

    def __init__(self):
        self.exchanges = get_all_exchanges()
        self.redis = RedisClient()

    async def fetch_exchange(
        self,
        session: aiohttp.ClientSession,
        exchange: BaseExchange
    ) -> Optional[List[CoinEntry]]:
        """Fetch data from a single exchange with error handling."""
        try:
            return await exchange.fetch_with_retry(session)
        except Exception as e:
            logger.error(f"Failed to fetch {exchange.config.name}: {e}")
            return None

    async def fetch_all_bulk_exchanges(
        self,
        session: aiohttp.ClientSession
    ) -> Dict[str, List[CoinEntry]]:
        """
        Fetch all bulk exchanges concurrently.

        Returns dict of exchange_name -> entries (only successful ones)
        """
        bulk_exchanges = {
            name: ex for name, ex in self.exchanges.items()
            if ex.config.fetch_strategy == FetchStrategy.BULK
        }

        logger.info(f"Fetching {len(bulk_exchanges)} bulk exchanges concurrently")

        # Run all bulk fetches concurrently
        tasks = {
            name: self.fetch_exchange(session, ex)
            for name, ex in bulk_exchanges.items()
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        successful = {}
        for name, result in zip(tasks.keys(), results):
            if isinstance(result, list):
                successful[name] = result
            elif isinstance(result, Exception):
                logger.warning(f"{name} fetch raised exception: {result}")
            else:
                logger.warning(f"{name} fetch returned None")

        return successful

    async def fetch_sequential_exchanges(
        self,
        session: aiohttp.ClientSession
    ) -> Dict[str, List[CoinEntry]]:
        """
        Fetch sequential exchanges (OKX, Gate.io) one at a time.

        These have per-token requests and rate limits.
        """
        sequential_exchanges = {
            name: ex for name, ex in self.exchanges.items()
            if ex.config.fetch_strategy == FetchStrategy.SEQUENTIAL
        }

        results = {}
        for name, exchange in sequential_exchanges.items():
            logger.info(f"Starting sequential fetch for {name}")
            data = await self.fetch_exchange(session, exchange)
            if data:
                results[name] = data
                logger.info(f"Completed {name} with {len(data)} entries")
            else:
                logger.warning(f"Failed to fetch {name}")

        return results

    async def run_update_cycle(self) -> None:
        """Run a single update cycle for all exchanges."""
        logger.info("=" * 50)
        logger.info("Starting update cycle")

        async with aiohttp.ClientSession() as session:
            # Fetch bulk exchanges concurrently
            bulk_results = await self.fetch_all_bulk_exchanges(session)
            logger.info(f"Bulk exchanges completed: {len(bulk_results)} successful")

            # Fetch sequential exchanges (these take longer)
            sequential_results = await self.fetch_sequential_exchanges(session)
            logger.info(f"Sequential exchanges completed: {len(sequential_results)} successful")

        # Merge results
        all_results = {**bulk_results, **sequential_results}

        if not all_results:
            logger.error("No exchanges returned data, skipping Redis update")
            return

        # Store raw data per exchange
        for exchange_name, entries in all_results.items():
            self.redis.store_exchange_data(exchange_name, entries)
            logger.info(f"Stored {len(entries)} entries for {exchange_name}")

        # Rebuild the contract index
        self.redis.rebuild_contract_index(all_results)
        stats = self.redis.get_index_stats()
        logger.info(f"Rebuilt contract index: {stats['total_contracts']} unique contracts")

        logger.info("Update cycle complete")
        logger.info("=" * 50)

    async def run_forever(self) -> None:
        """Run the updater in an infinite loop."""
        while True:
            try:
                await self.run_update_cycle()
            except Exception as e:
                logger.exception(f"Update cycle failed: {e}")

            logger.info(f"Sleeping for {UPDATE_INTERVAL_SECONDS // 60} minutes")
            await asyncio.sleep(UPDATE_INTERVAL_SECONDS)


async def main():
    """Entry point for the updater service."""
    service = UpdaterService()
    await service.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
