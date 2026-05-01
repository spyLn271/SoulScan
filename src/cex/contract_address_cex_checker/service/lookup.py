"""
Contract address lookup module.

Usage:
    from service.lookup import lookup_mint

    result = lookup_mint("So11111111111111111111111111111111111111112")
    # Returns: {"bybit": "SOL", "binance": "SOL", ...} or None
"""
from typing import Dict, Optional

from .redis_client import RedisClient


_redis_client: Optional[RedisClient] = None


def _get_redis_client() -> RedisClient:
    """Lazy initialization of Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


def lookup_mint(contract_address: str) -> Optional[Dict[str, str]]:
    """
    Look up a mint/contract address across all exchanges.

    Args:
        contract_address: The contract/mint address to look up

    Returns:
        Dict of {exchange_name: coin_name} for exchanges that have this address,
        or None if not found anywhere

    Example:
        >>> lookup_mint("0xdac17f958d2ee523a2206206994597c13d831ec7")
        {"binance": "USDT", "okx": "USDT", "kucoin": "USDT"}

        >>> lookup_mint("nonexistent_address")
        None
    """
    redis_client = _get_redis_client()
    return redis_client.lookup_contract(contract_address)
