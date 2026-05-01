"""
Redis client for storing and retrieving exchange data.
"""
import json
import time
from typing import Dict, List, Optional
import redis

from .config import REDIS_CONFIG
from .exchanges.base import CoinEntry


_EVM_HEX = set("0123456789abcdefABCDEF")


def _normalize_address(addr: str) -> str:
    """EVM addresses are case-insensitive hex (`0x` + 40 hex chars) — lowercase
    them so different casings collide on the same index entry. Solana base58
    and other non-EVM formats are case-sensitive: preserve them verbatim."""
    if len(addr) == 42 and addr.startswith("0x") and all(c in _EVM_HEX for c in addr[2:]):
        return addr.lower()
    return addr


class RedisClient:
    """Redis operations for cex data storage and lookup."""

    def __init__(self):
        self.client = redis.Redis(
            host=REDIS_CONFIG.host,
            port=REDIS_CONFIG.port,
            db=REDIS_CONFIG.db,
            password=REDIS_CONFIG.password,
            decode_responses=True
        )

    def store_exchange_data(self, exchange_name: str, entries: List[CoinEntry]) -> None:
        """Store raw exchange data as idl."""
        key = REDIS_CONFIG.exchange_data_key.format(exchange=exchange_name)
        data = [e.to_dict() for e in entries]
        self.client.set(key, json.dumps(data))

        # Update timestamp
        ts_key = REDIS_CONFIG.last_update_key.format(exchange=exchange_name)
        self.client.set(ts_key, str(int(time.time())))

    def rebuild_contract_index(self, all_exchange_data: Dict[str, List[CoinEntry]]) -> None:
        """
        Rebuild the contract address index from all exchange data.

        Uses a temporary key and atomic rename for zero-downtime updates.
        """
        temp_key = f"{REDIS_CONFIG.contract_index_key}:temp"

        # Build index: contract_address -> {exchange: coin_name}
        index: Dict[str, Dict[str, str]] = {}

        for exchange_name, entries in all_exchange_data.items():
            for entry in entries:
                if entry.contract_address:  # Skip empty addresses
                    addr = _normalize_address(entry.contract_address)
                    if addr not in index:
                        index[addr] = {}
                    index[addr][exchange_name] = entry.coin

        # Write to temp key using pipeline for efficiency
        pipe = self.client.pipeline()
        pipe.delete(temp_key)

        for contract_addr, exchange_map in index.items():
            pipe.hset(temp_key, contract_addr, json.dumps(exchange_map))

        # Atomic rename (only if temp key exists)
        if index:
            pipe.rename(temp_key, REDIS_CONFIG.contract_index_key)

        pipe.execute()

    def lookup_contract(self, contract_address: str) -> Optional[Dict[str, str]]:
        """
        Look up a contract address and return exchanges that have it.

        Args:
            contract_address: The mint/contract address to look up

        Returns:
            Dict of {exchange_name: coin_name} or None if not found
        """
        result = self.client.hget(REDIS_CONFIG.contract_index_key, _normalize_address(contract_address))

        if result:
            return json.loads(result)
        return None

    def get_index_stats(self) -> Dict:
        """Get statistics about the contract index."""
        return {
            "total_contracts": self.client.hlen(REDIS_CONFIG.contract_index_key),
        }

    def get_last_update(self, exchange_name: str) -> Optional[int]:
        """Get the last update timestamp for an exchange."""
        ts_key = REDIS_CONFIG.last_update_key.format(exchange=exchange_name)
        result = self.client.get(ts_key)
        return int(result) if result else None
