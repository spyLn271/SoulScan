"""
Redis client for storing and retrieving exchange data.
"""
import json
import time
from typing import Dict, List, Optional
import redis

from .config import REDIS_CONFIG
from .exchanges.base import CoinEntry
from src.logger_handler.logger import get_logger


logger = get_logger("cex-Contracts.redis_client")

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

        Safety (PRC-01): if a rebuild cycle produced NO contract addresses at all
        (every exchange fetch failed / returned nothing), the swap is SKIPPED and
        the previous index is kept — stale-but-present beats silently blanking the
        index, which would make every downstream address lookup miss. The skip is
        logged at WARNING so a total fetch failure is visible, not masked.
        """
        temp_key = f"{REDIS_CONFIG.contract_index_key}:temp"

        # Build index: contract_address -> {exchange: coin_name}
        index: Dict[str, Dict[str, str]] = {}

        # Per-exchange counts for observability (fetched vs. with-contract-address).
        counts: Dict[str, Dict[str, int]] = {}
        for exchange_name, entries in all_exchange_data.items():
            with_addr = 0
            for entry in entries:
                if entry.contract_address:  # Skip empty addresses
                    addr = _normalize_address(entry.contract_address)
                    if addr not in index:
                        index[addr] = {}
                    index[addr][exchange_name] = entry.coin
                    with_addr += 1
            counts[exchange_name] = {"fetched": len(entries), "with_contract": with_addr}

        logger.info(
            "Contract index rebuild: %d unique addresses across %d exchanges | per-exchange %s",
            len(index), len(all_exchange_data), counts,
        )

        # Guard: never blank a populated index because a whole cycle failed.
        if not index:
            logger.warning(
                "Contract index rebuild produced 0 addresses — SKIPPING swap, "
                "keeping previous index to avoid blanking lookups. per-exchange %s",
                counts,
            )
            # Clean up any leftover temp key from a prior interrupted run.
            self.client.delete(temp_key)
            return

        # Write to temp key using pipeline for efficiency, then atomically swap.
        pipe = self.client.pipeline()
        pipe.delete(temp_key)

        for contract_addr, exchange_map in index.items():
            pipe.hset(temp_key, contract_addr, json.dumps(exchange_map))

        # Stamp a freshness version (additive field; the Rust reader ignores
        # unknown hash fields, and "_version" can never collide with a 0x address).
        pipe.hset(temp_key, "_version", str(int(time.time())))
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
