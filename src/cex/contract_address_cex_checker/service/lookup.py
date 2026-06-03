"""
Contract address lookup module.

The contract index is keyed by (network, address) — see canonical.py — so a lookup
needs both the chain and the address. DEX pools are chain-scoped, so the caller
always knows the network.

Usage:
    from service.lookup import lookup_token

    result = lookup_token("solana", "So11111111111111111111111111111111111111112")
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


def lookup_token(network: str, contract_address: str) -> Optional[Dict[str, str]]:
    """
    Look up a token by (network, address) across all exchanges.

    Args:
        network: chain name (raw or canonical, e.g. "eth", "ERC20", "solana")
        contract_address: the on-chain address / mint

    Returns:
        Dict of {exchange_name: tradable_base_symbol} for exchanges that trade this
        token, or None if not found anywhere.

    Example:
        >>> lookup_token("eth", "0xdac17f958d2ee523a2206206994597c13d831ec7")
        {"binance": "USDT", "okx": "USDT", "kucoin": "USDT"}

        >>> lookup_token("solana", "So11111111111111111111111111111111111111112")
        {"binance": "SOL", "gateio": "SOL", ...}

        >>> lookup_token("eth", "0xnonexistent")
        None
    """
    return _get_redis_client().lookup_contract(network, contract_address)
