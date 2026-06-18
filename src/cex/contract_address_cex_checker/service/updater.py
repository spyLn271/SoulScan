"""
Redis updater service - fetches from all exchanges and updates Redis.
Runs in a loop: update -> sleep 20 min -> repeat
"""
import asyncio
from typing import Dict, List, Optional
import aiohttp

from .config import (
    UPDATE_INTERVAL_SECONDS,
    BACKFILL_MIN_WITNESSES,
    PRICE_MATCH_ENABLED,
    PRICE_MATCH_MAX_DEVIATION,
    PRICE_MATCH_STREAM_MAX_AGE,
    FetchStrategy,
    get_backfill_exchanges,
    validate_exchange_credentials,
)
from .exchanges import get_all_exchanges
from .exchanges.base import BaseExchange, CoinEntry
from .redis_client import RedisClient
from src.logger_handler.logger import get_logger

# The supervisor (or run_updater.py for standalone use) installs the root
# handler. Internal getLogger calls (here and in exchanges/base.py) propagate
# up to root, which writes to LogFolder/cex-contracts/cex-Contracts.log.
logger = get_logger("cex-Contracts.updater")


class UpdaterService:
    """Main service that orchestrates fetching and storing."""

    def __init__(self):
        self.exchanges = get_all_exchanges()
        validate_exchange_credentials()  # fail-fast if required CEX creds are missing
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

        # Merge fresh results
        fresh_results = {**bulk_results, **sequential_results}

        # Store fresh data per exchange (updates its last-good cache + timestamp)
        for exchange_name, entries in fresh_results.items():
            self.redis.store_exchange_data(exchange_name, entries)
            logger.info(f"Stored {len(entries)} entries for {exchange_name}")

        # Per-exchange last-good fallback: for every configured exchange that did
        # NOT return fresh data this cycle, reuse its last successful snapshot so a
        # transient fetch failure (bad key / rate-limit) doesn't drop the whole
        # exchange from the index. Flag which exchanges are serving stale data.
        rebuild_input: Dict[str, List[CoinEntry]] = dict(fresh_results)
        stale = []
        for name in self.exchanges:
            if name in rebuild_input:
                continue
            cached = self.redis.load_exchange_data(name)
            if cached:
                rebuild_input[name] = cached
                stale.append(name)
        if stale:
            logger.warning(
                "Serving LAST-GOOD cached data for %d exchange(s) that failed this "
                "cycle: %s", len(stale), stale,
            )

        if not rebuild_input:
            logger.error("No fresh or cached exchange data available, skipping Redis update")
            return

        logger.info(
            "Rebuilding index from %d exchanges (%d fresh, %d cached)",
            len(rebuild_input), len(fresh_results), len(stale),
        )

        # Rebuild the contract index. Back-fill-only exchanges (e.g. LBank, which
        # exposes no contract addresses) are attached to addresses other exchanges
        # resolved, gated by the witness threshold.
        self.redis.rebuild_contract_index(
            rebuild_input,
            backfill_exchanges=get_backfill_exchanges(),
            min_witnesses=BACKFILL_MIN_WITNESSES,
            price_match=PRICE_MATCH_ENABLED,
            price_match_max_deviation=PRICE_MATCH_MAX_DEVIATION,
            price_match_stream_max_age=PRICE_MATCH_STREAM_MAX_AGE,
        )
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
