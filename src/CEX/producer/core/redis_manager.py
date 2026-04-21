#!/usr/bin/env python3
"""
Redis Connection Manager - Shared connection pool for all exchange components

This module provides a singleton RedisManager that maintains a single shared
connection pool for the entire application, preventing the creation of hundreds
of individual Redis connections.

Key benefits:
- Single shared connection pool instead of per-component pools
- Limited max_connections (50) for the entire application
- Automatic connection health monitoring and keepalive
- Thread-safe singleton pattern
- Proper cleanup and resource management
"""

import asyncio
import logging
from typing import Optional
import redis.asyncio as redis

from src.CEX.producer.config import get_redis_config


class RedisManager:
    """
    Singleton Redis connection manager with shared connection pool

    Manages a single Redis connection pool that is shared across all
    exchange components, preventing connection proliferation.
    """

    _instance: Optional['RedisManager'] = None
    _pool: Optional[redis.ConnectionPool] = None
    _client: Optional[redis.Redis] = None
    _lock: Optional[asyncio.Lock] = None
    _logger = logging.getLogger("redis_manager")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def get_client(cls) -> redis.Redis:
        """
        Get a Redis client using the shared connection pool

        Returns:
            Redis client connected to the shared pool

        Note:
            This method is thread-safe and will create the pool on first call
        """
        if cls._client is None:
            if cls._lock is None:
                cls._lock = asyncio.Lock()

            async with cls._lock:
                # Double-check pattern for thread safety
                if cls._client is None:
                    await cls._create_pool()

        return cls._client

    @classmethod
    async def _create_pool(cls):
        """Create the shared Redis connection pool"""
        redis_config = get_redis_config()

        # Remove decode_responses from config as we'll handle it in Redis client
        pool_config = redis_config.copy()
        decode_responses = pool_config.pop('decode_responses', True)

        cls._logger.info("Creating shared Redis connection pool...")

        # Create connection pool with strict limits and health monitoring
        cls._pool = redis.ConnectionPool(
            **pool_config,
            max_connections=1000,  # Large pool for 10+ exchanges with high concurrency (e.g., Gate.io with 2000+ individual connections)
            socket_keepalive=True,
            health_check_interval=30,  # Check connection health every 30 seconds
            retry_on_timeout=True,
            socket_connect_timeout=10,
            socket_timeout=10,
        )

        # Create Redis client using the shared pool
        cls._client = redis.Redis(
            connection_pool=cls._pool,
            decode_responses=decode_responses
        )

        # Test the connection
        try:
            await cls._client.ping()
            cls._logger.info(f"Successfully connected to Redis at {redis_config['host']}:{redis_config['port']}")
            cls._logger.info(f"Shared pool configured with max_connections=1000")
        except Exception as e:
            cls._logger.error(f"Failed to connect to Redis: {e}")
            await cls.close_pool()
            raise

    @classmethod
    async def get_pool_info(cls) -> dict:
        """
        Get information about the current connection pool

        Returns:
            Dictionary with pool statistics
        """
        if cls._pool is None:
            return {"status": "not_initialized"}

        # Try to get pool statistics
        try:
            pool_stats = {
                "status": "active",
                "max_connections": cls._pool.max_connections,
                "created_connections": cls._pool.created_connections,
                "available_connections": len(cls._pool._available_connections),
                "in_use_connections": len(cls._pool._in_use_connections),
            }
            return pool_stats
        except Exception as e:
            cls._logger.warning(f"Could not get pool statistics: {e}")
            return {"status": "error", "error": str(e)}

    @classmethod
    async def close_pool(cls):
        """
        Close the shared Redis connection pool and cleanup resources

        This should be called during application shutdown to ensure
        all connections are properly closed.
        """
        if cls._client:
            try:
                cls._logger.info("Closing shared Redis connection pool...")
                await cls._client.aclose()
                cls._logger.info("Redis connection pool closed successfully")
            except Exception as e:
                cls._logger.error(f"Error closing Redis pool: {e}")
            finally:
                cls._client = None
                cls._pool = None

    @classmethod
    async def health_check(cls) -> bool:
        """
        Perform a health check on the Redis connection

        Returns:
            True if Redis is healthy, False otherwise
        """
        try:
            if cls._client is None:
                return False

            await cls._client.ping()
            return True
        except Exception as e:
            cls._logger.warning(f"Redis health check failed: {e}")
            return False


# Convenience function for easy import
async def get_redis_client() -> redis.Redis:
    """
    Convenience function to get a Redis client

    Returns:
        Redis client using the shared connection pool
    """
    return await RedisManager.get_client()


# Cleanup function for application shutdown
async def cleanup_redis():
    """
    Cleanup function to be called during application shutdown
    """
    await RedisManager.close_pool()