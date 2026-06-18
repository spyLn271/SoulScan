#!/usr/bin/env python3
"""
Error Reporter - Centralized error reporting and management

Handles error reporting to Redis queues and provides error analytics
"""

import gzip
import json
import logging
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import redis.asyncio as redis

from src.cex.producer.core.redis_manager import RedisManager
from src.cex.producer.config import get_error_queue_key, get_redis_config, STREAM_CONFIG


class ErrorReporter:
    """
    Centralized error reporting for exchange connectors
    """

    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name
        self.logger = logging.getLogger(f"error_reporter_{exchange_name}")
        self.redis_client: Optional[redis.Redis] = None

    async def initialize(self):
        """Initialize Redis connection using shared connection pool"""
        if not self.redis_client:
            self.redis_client = await RedisManager.get_client()

    async def report_error(self,
                          symbols: List[str],
                          error_type: str,
                          error_message: str,
                          traceback_str: str = "",
                          market_type: str = "spot",
                          source_script: str = None):
        """
        Report error to Redis error queue

        Args:
            symbols: List of affected symbols
            error_type: Type of error (e.g., ConnectionError, ParseError)
            error_message: Error message
            traceback_str: Full traceback string
            market_type: Market type (spot/futures)
            source_script: Source script name
        """
        try:
            await self.initialize()

            error_entry = {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "source_script": source_script or f"{self.exchange_name}_{market_type}_plugin",
                "exchange": self.exchange_name,
                "market_type": market_type,
                "affected_symbols": symbols,
                "error_type": error_type,
                "error_message": error_message,
                "traceback": traceback_str
            }

            error_queue_key = get_error_queue_key(self.exchange_name)
            # Bounded push: cap the queue to the most recent N entries (see STREAM_CONFIG).
            max_entries = STREAM_CONFIG.get('error_queue_max_entries', 5000)
            pipe = self.redis_client.pipeline()
            pipe.lpush(error_queue_key, json.dumps(error_entry))
            pipe.ltrim(error_queue_key, 0, max_entries - 1)
            await pipe.execute()

            self.logger.debug(f"Reported {error_type} for {len(symbols)} symbols")

        except Exception as e:
            self.logger.error(f"Failed to report error to Redis: {e}")

    async def cleanup_error_queue_for_symbols(self, symbols: List[str]):
        """
        Clean up error queue entries for successfully reconnected symbols

        Args:
            symbols: List of symbols that have successfully reconnected
        """
        try:
            await self.initialize()

            error_queue_key = get_error_queue_key(self.exchange_name)

            # Get all error entries
            error_entries = await self.redis_client.lrange(error_queue_key, 0, -1)

            # Filter out entries for reconnected symbols
            filtered_entries = []
            cleaned_count = 0

            for entry_str in error_entries:
                try:
                    entry = json.loads(entry_str)
                    affected_symbols = entry.get("affected_symbols", [])

                    # Keep entry if it doesn't affect any of the reconnected symbols
                    if not any(symbol in symbols for symbol in affected_symbols):
                        filtered_entries.append(entry_str)
                    else:
                        cleaned_count += 1

                except json.JSONDecodeError:
                    # Keep malformed entries for manual review
                    filtered_entries.append(entry_str)

            # Replace queue with filtered entries
            if cleaned_count > 0:
                await self.redis_client.delete(error_queue_key)
                if filtered_entries:
                    # filtered_entries is newest-first (lrange 0..-1). Use rpush to append
                    # in-order so the newest-first invariant is preserved (lpush would
                    # reverse it), then cap so the queue can't grow unbounded.
                    max_entries = STREAM_CONFIG.get('error_queue_max_entries', 5000)
                    await self.redis_client.rpush(error_queue_key, *filtered_entries)
                    await self.redis_client.ltrim(error_queue_key, 0, max_entries - 1)

                self.logger.info(f"Cleaned {cleaned_count} error entries for {len(symbols)} reconnected symbols")

        except Exception as e:
            self.logger.error(f"Failed to cleanup error queue: {e}")

    async def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get error statistics for this exchange

        Returns:
            Dict with error statistics
        """
        try:
            await self.initialize()

            error_queue_key = get_error_queue_key(self.exchange_name)
            error_entries = await self.redis_client.lrange(error_queue_key, 0, -1)

            stats = {
                "total_errors": len(error_entries),
                "error_types": {},
                "recent_errors": [],
                "affected_symbols": set()
            }

            for entry_str in error_entries[-10:]:  # Last 10 errors
                try:
                    entry = json.loads(entry_str)
                    error_type = entry.get("error_type", "Unknown")

                    # Count error types
                    stats["error_types"][error_type] = stats["error_types"].get(error_type, 0) + 1

                    # Add to recent errors
                    stats["recent_errors"].append({
                        "timestamp": entry.get("timestamp_utc"),
                        "error_type": error_type,
                        "message": entry.get("error_message", ""),
                        "symbols": entry.get("affected_symbols", [])
                    })

                    # Track affected symbols
                    stats["affected_symbols"].update(entry.get("affected_symbols", []))

                except json.JSONDecodeError:
                    continue

            stats["affected_symbols"] = list(stats["affected_symbols"])

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get error statistics: {e}")
            return {"total_errors": 0, "error_types": {}, "recent_errors": [], "affected_symbols": []}

    async def close(self):
        """Close Redis connection - using shared pool, no individual close needed"""
        if self.redis_client:
            # Redis connection is managed by shared pool - no individual close needed
            self.redis_client = None


# --- Standalone Error Queue Rotation Functions ---

async def get_error_queue_size(redis_client, exchange: str) -> int:
    """
    Get error queue size in bytes using MEMORY USAGE command.

    Args:
        redis_client: Redis async client
        exchange: Exchange name

    Returns:
        Size in bytes, or 0 if queue doesn't exist
    """
    queue_key = get_error_queue_key(exchange)
    size = await redis_client.memory_usage(queue_key)
    return size or 0


async def rotate_error_queue(redis_client, exchange: str, logger) -> bool:
    """
    Rotate error queue if it exceeds max size.
    Archives to gzipped log file and clears Redis list.

    Args:
        redis_client: Redis async client
        exchange: Exchange name
        logger: Logger instance

    Returns:
        True if rotation occurred, False otherwise
    """
    queue_key = get_error_queue_key(exchange)
    max_size = STREAM_CONFIG.get('error_queue_max_size_bytes', 500 * 1024 * 1024)
    archive_dir = STREAM_CONFIG.get('error_archive_dir', './error_archive')

    # Check size using MEMORY USAGE
    size = await redis_client.memory_usage(queue_key)
    if not size or size < max_size:
        return False

    logger.info(f"[{exchange}] Error queue size {size / 1024 / 1024:.1f}MB exceeds limit ({max_size / 1024 / 1024:.0f}MB), rotating...")

    # Ensure archive directory exists
    os.makedirs(archive_dir, exist_ok=True)

    # Fetch all entries from the queue
    entries = await redis_client.lrange(queue_key, 0, -1)
    if not entries:
        return False

    # Generate archive filename with timestamp
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
    archive_path = os.path.join(archive_dir, f"{exchange}_errors_{timestamp}.log.gz")

    # Write to gzipped archive (one idl entry per line)
    with gzip.open(archive_path, 'wt', encoding='utf-8') as f:
        for entry in entries:
            f.write(entry + '\n')

    # Clear Redis list
    await redis_client.delete(queue_key)

    logger.info(f"[{exchange}] Rotated {len(entries)} errors to {archive_path}")
    return True


async def check_and_rotate_all_queues(redis_client, exchanges: list, logger):
    """
    Check all exchange error queues and rotate if needed.

    Args:
        redis_client: Redis async client
        exchanges: List of exchange names to check
        logger: Logger instance
    """
    for exchange in exchanges:
        try:
            await rotate_error_queue(redis_client, exchange, logger)
        except Exception as e:
            logger.error(f"[{exchange}] Error queue rotation failed: {e}")