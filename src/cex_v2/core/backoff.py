#!/usr/bin/env python3
"""Exponential-backoff-with-jitter (carried over verbatim from the proven legacy helper)."""
import asyncio
import random
import time
from typing import Optional


class RestartBackoff:
    def __init__(self, base: float = 5.0, cap: float = 60.0, factor: float = 2.0,
                 jitter: float = 0.3, reset_after: float = 30.0,
                 max_attempts: Optional[int] = None):
        self.base = base
        self.cap = cap
        self.factor = factor
        self.jitter = jitter
        self.reset_after = reset_after
        self.max_attempts = max_attempts
        self.attempt = 0

    def next_delay(self) -> float:
        raw = min(self.base * (self.factor ** self.attempt), self.cap)
        self.attempt += 1
        return raw + random.uniform(0, raw * self.jitter)

    def reset(self) -> None:
        self.attempt = 0

    def note_uptime(self, uptime_seconds: float) -> None:
        if uptime_seconds >= self.reset_after:
            self.reset()

    def should_give_up(self) -> bool:
        return self.max_attempts is not None and self.attempt >= self.max_attempts

    def sleep_sync(self) -> float:
        d = self.next_delay(); time.sleep(d); return d

    async def sleep_async(self) -> float:
        d = self.next_delay(); await asyncio.sleep(d); return d
