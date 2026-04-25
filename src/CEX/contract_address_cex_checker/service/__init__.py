"""
CEX Contract Address Lookup Service.

Usage:
    # Lookup a mint address
    from .lookup import lookup_mint
    result = lookup_mint("0xdac17f958d2ee523a2206206994597c13d831ec7")

    # Run the updater service
    python -m service.updater
"""
from .lookup import lookup_mint

__all__ = ["lookup_mint"]
