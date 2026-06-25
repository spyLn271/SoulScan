"""
cex Contract Address Lookup Service.

Usage:
    # Lookup a token by (network, address)
    from .lookup import lookup_token
    result = lookup_token("eth", "0xdac17f958d2ee523a2206206994597c13d831ec7")

    # Run the updater service
    python -m service.updater
"""
from .lookup import lookup_token

__all__ = ["lookup_token"]
