#!/usr/bin/env python3
"""Shared CEX heartbeat reader -> per-pair health verdict. Sync Redis."""
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.cex.producer.config import (
    get_enabled_exchanges, get_exchange_config, STREAM_CONFIG, MONITORING_CONFIG,
)

HEALTH_PREFIX = STREAM_CONFIG.get("health_prefix", "health")


@dataclass
class PairHealth:
    exchange: str
    market_type: str
    heartbeats: int = 0
    fresh_heartbeats: int = 0
    max_age_s: Optional[float] = None
    total_msgs: int = 0
    active_symbols: int = 0
    backpressured: bool = False
    monitoring_healthy: bool = True
    proxies: List[str] = field(default_factory=list)
    proxy_rotations: int = 0

    @property
    def healthy(self) -> bool:
        return (self.fresh_heartbeats > 0
                and not self.backpressured
                and self.monitoring_healthy)


def enabled_pairs() -> List[tuple]:
    pairs = []
    for exchange in get_enabled_exchanges():
        config = get_exchange_config(exchange) or {}
        for market_type in ("spot", "futures"):
            if config.get(market_type, {}).get("enabled", False):
                pairs.append((exchange, market_type))
    return pairs


def evaluate_pair(redis_client, exchange, market_type, hung_timeout=None, now=None,
                  worker_id="*") -> PairHealth:
    """Aggregate heartbeat health for an (exchange, market_type).

    worker_id="*" (default) aggregates ALL workers' heartbeats (health:...:*).
    Pass a specific worker_id (or None for the legacy ':none' key) to evaluate just
    that one worker — used by the supervisor for per-worker hung detection.
    """
    if hung_timeout is None:
        hung_timeout = MONITORING_CONFIG.get("hung_worker_timeout", 120)
    if now is None:
        now = time.time()
    ph = PairHealth(exchange=exchange, market_type=market_type)
    if worker_id == "*":
        pattern = f"{HEALTH_PREFIX}:{exchange}:{market_type}:*"
        if hasattr(redis_client, "scan_iter"):
            keys = list(redis_client.scan_iter(match=pattern))
        else:
            keys = redis_client.keys(pattern)
    else:
        wid = 'none' if worker_id is None else worker_id
        keys = [f"{HEALTH_PREFIX}:{exchange}:{market_type}:{wid}"]
    best_age = None
    for key in keys:
        raw = redis_client.get(key)
        if not raw:
            continue
        try:
            hb = json.loads(raw)
        except (ValueError, TypeError):
            continue
        ph.heartbeats += 1
        age = now - (hb.get("ts", 0) / 1000.0)
        if best_age is None or age < best_age:
            best_age = age
        if age <= hung_timeout:
            ph.fresh_heartbeats += 1
        ph.total_msgs += int(hb.get("msgs", 0) or 0)
        ph.active_symbols += int(hb.get("active_symbols", 0) or 0)
        ph.backpressured = ph.backpressured or bool(hb.get("redis_backpressured", False))
        ph.monitoring_healthy = ph.monitoring_healthy and bool(hb.get("monitoring_healthy", True))
        if hb.get("current_proxy"):
            ph.proxies.append(hb["current_proxy"])
        ph.proxy_rotations += int(hb.get("proxy_rotations", 0) or 0)
    ph.max_age_s = best_age
    return ph


def scan_all(redis_client, hung_timeout=None, now=None) -> List[PairHealth]:
    return [evaluate_pair(redis_client, ex, mt, hung_timeout, now)
            for ex, mt in enabled_pairs()]
