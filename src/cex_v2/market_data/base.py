#!/usr/bin/env python3
"""
Hardened base market-data handler (cex_v2). Rebuilt from MARKET_DATA_AUDIT.md.

Each handler: set api_endpoint/redis_key/update_interval, implement parse_api_response(json) ->
[{symbol, data}], where data fields (best_bid/best_ask/lastPrice) are FULL-PRECISION STRINGS.
The base enforces the invariants the old feeder violated:

  - NEVER blank a populated hash: skip the write if 0 valid symbols, OR if the count collapses
    below `min_fraction` of the last good count (catches partial-API breaks). The atomic
    MULTI/EXEC delete+rewrite still prevents partial reads.
  - Drop malformed records (None/empty data) instead of silently writing an empty hash.
  - Backoff + circuit-breaker on fetch failure (no fixed-interval hammering of a down/429 exchange).
  - Clean, responsive shutdown.
"""
import json
import logging
import time
from abc import ABC, abstractmethod
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

import httpx
import redis

from src.cex_v2.config import get_redis_config, LOGGING
from src.cex_v2.core.backoff import RestartBackoff
from src.cex_v2.core.jsonio import dumps as _dumps
from src.cex_v2.observability import emit_perf
from src.cex_v2.observability import metrics as _m


class BaseMarketDataHandler(ABC):
    def __init__(self, exchange: str, market_type: str, api_endpoint: str, redis_key: str,
                 update_interval: float = 3.0, min_fraction: float = 0.5, fetch_timeout: int = 10):
        self.exchange = exchange
        self.market_type = market_type
        self.api_endpoint = api_endpoint
        self.redis_key = redis_key
        self.update_interval = update_interval
        self.min_fraction = min_fraction      # reject a cycle whose count < min_fraction * last good
        self.fetch_timeout = fetch_timeout
        self.shutdown_requested = False
        self.redis = None
        self._http = None
        self._last_count = 0
        self._consecutive_failures = 0
        self.logger = logging.getLogger(f"cexv2.md.{exchange}.{market_type}")
        # --- perf counters ---
        self._t0 = time.time()
        self._updates = self._ok = self._fail = 0
        self._fetch_ms = deque(maxlen=500)
        self._store_ms = deque(maxlen=500)
        self._last_perf = time.time()
        self.perf_interval = float(LOGGING.get("perf_interval", 30))

    # ---- plugin hook ----
    @abstractmethod
    def parse_api_response(self, response_json) -> List[Dict[str, Any]]:
        """Return [{'symbol': str, 'data': {best_bid,best_ask,lastPrice (STRINGS), 24h_volume_usdt, ...}}]."""

    def validate_record(self, data: Dict[str, Any]) -> bool:
        """Drop a record if its data is unusable. Default: non-empty dict. Override for stricter checks
        (e.g. require non-None best_bid/best_ask) per exchange."""
        return isinstance(data, dict) and len(data) > 0

    # ---- lifecycle ----
    def initialize(self) -> bool:
        try:
            rc = get_redis_config()
            self.redis = redis.Redis(host=rc["host"], port=rc["port"], db=rc.get("db", 0),
                                     password=rc.get("password"), decode_responses=True,
                                     client_name=f"cexv2:md:{self.exchange}:{self.market_type}")
            self.redis.ping()
        except redis.RedisError as e:
            self.logger.error("redis connect failed: %s", e)
            return False
        # Persistent keep-alive HTTP client: reuses connections across polls (no per-poll TLS
        # handshake) and lets multi-endpoint handlers fetch concurrently (httpx.Client is thread-safe).
        self._http = httpx.Client(
            timeout=self.fetch_timeout,
            limits=httpx.Limits(max_keepalive_connections=8, max_connections=16),
            headers={"User-Agent": "cexv2-marketdata"},
        )
        return True

    @staticmethod
    def get_decimal_places(s: str) -> int:
        return len(s.split(".")[-1]) if isinstance(s, str) and "." in s else 0

    def _get(self, url: str):
        r = self._http.get(url)
        r.raise_for_status()
        return r.json()

    def _get_many(self, urls: List[str]) -> Dict[str, Any]:
        """Fetch several endpoints CONCURRENTLY over the shared keep-alive client -> {url: json}.
        Wall-clock = slowest single request, not the sum (the futures 3-endpoint merge wants this)."""
        if not urls:
            return {}
        with ThreadPoolExecutor(max_workers=max(1, len(urls))) as ex:
            futs = {ex.submit(self._get, u): u for u in urls}
            return {futs[f]: f.result() for f in futs}

    def _fetch(self):
        return self._get(self.api_endpoint)

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        """Fetch + parse into [{symbol, data}]. Default: single endpoint -> parse_api_response.
        Override for multi-endpoint exchanges (e.g. futures merges 24hr+book+premium)."""
        return self.parse_api_response(self._fetch())

    def _mark_fail(self):
        self._fail += 1
        _m.MD_UPDATES.labels(self.exchange, self.market_type, "fail").inc()

    def update_once(self) -> bool:
        """One fetch+parse+store cycle. Returns True on a successful write (or intentional skip)."""
        self._updates += 1
        _tf = time.perf_counter()
        try:
            parsed = self.fetch_parsed()
        except httpx.HTTPError as e:
            self._mark_fail(); self.logger.warning("fetch failed: %s", e); return False
        except (ValueError, json.JSONDecodeError) as e:
            self._mark_fail(); self.logger.warning("bad JSON: %s", e); return False
        except Exception as e:
            self._mark_fail(); self.logger.error("fetch/parse error: %s", e); return False
        finally:
            # record fetch latency on BOTH success and failure (a timeout/slow-then-fail is the most
            # interesting latency to see, and it was previously invisible)
            _dt = time.perf_counter() - _tf
            self._fetch_ms.append(_dt * 1000.0)
            _m.MD_FETCH.labels(self.exchange, self.market_type).observe(_dt)

        if not parsed:
            self._mark_fail(); self.logger.warning("empty parse; preserving existing hash"); return False
        _ts = time.perf_counter()
        ok = self._store(parsed)
        _sdt = time.perf_counter() - _ts
        self._store_ms.append(_sdt * 1000.0)
        _m.MD_STORE.labels(self.exchange, self.market_type).observe(_sdt)
        _m.MD_UPDATES.labels(self.exchange, self.market_type, "ok" if ok else "fail").inc()
        self._ok += 1 if ok else 0
        self._fail += 0 if ok else 1
        return ok

    def _store(self, parsed: List[Dict[str, Any]]) -> bool:
        valid = [(p["symbol"], p["data"]) for p in parsed
                 if p.get("symbol") and self.validate_record(p.get("data"))]
        count = len(valid)

        # NEVER blank a populated hash.
        if count == 0:
            self.logger.warning("0 valid symbols; preserving existing hash"); return False
        if self._last_count and count < self.min_fraction * self._last_count:
            self.logger.warning("count %d < %.0f%% of last %d; suspected partial break, preserving",
                                count, self.min_fraction * 100, self._last_count)
            return False

        pipe = self.redis.pipeline(transaction=True)  # MULTI/EXEC: readers see old or new, never partial
        pipe.delete(self.redis_key)
        for symbol, data in valid:
            pipe.hset(self.redis_key, symbol, _dumps(data))
        pipe.hset(self.redis_key, "_version", time.time_ns())
        pipe.execute()
        self._last_count = count
        _m.MD_SYMBOLS.labels(self.exchange, self.market_type).set(count)
        self.logger.info("updated %d %s symbols", count, self.market_type)
        return True

    def run(self):
        self.logger.info("start %s %s market-data (interval=%ss)", self.exchange, self.market_type, self.update_interval)
        backoff = RestartBackoff(base=2.0, cap=60.0, jitter=0.3, reset_after=self.update_interval * 2)
        while not self.shutdown_requested:
            t0 = time.monotonic()
            ok = self.update_once()
            if ok:
                self._consecutive_failures = 0
                backoff.reset()
                sleep_for = max(0.0, self.update_interval - (time.monotonic() - t0))
            else:
                self._consecutive_failures += 1
                sleep_for = backoff.next_delay()   # circuit-breaker: back off a failing/429 exchange
                if self._consecutive_failures in (5, 20, 100):
                    self.logger.error("%d consecutive failures", self._consecutive_failures)
            if time.time() - self._last_perf >= self.perf_interval:
                self._emit_perf(); self._last_perf = time.time()
            # poll-sleep so shutdown is observed within ~0.5s
            while sleep_for > 0 and not self.shutdown_requested:
                chunk = min(0.5, sleep_for)
                time.sleep(chunk)
                sleep_for -= chunk
        self.logger.info("stopped %s %s market-data", self.exchange, self.market_type)

    def _emit_perf(self):
        def pct(d, p):
            s = sorted(d)
            return round(s[min(len(s) - 1, int(len(s) * p))], 2) if s else 0.0
        emit_perf({
            "exchange": self.exchange, "market": self.market_type,
            "uptime_s": round(time.time() - self._t0, 1),
            "updates": self._updates, "ok": self._ok, "fail": self._fail,
            "last_count": self._last_count, "consecutive_failures": self._consecutive_failures,
            "fetch_p50_ms": pct(self._fetch_ms, 0.5), "fetch_p99_ms": pct(self._fetch_ms, 0.99),
            "store_p50_ms": pct(self._store_ms, 0.5),
            "store_max_ms": round(max(self._store_ms), 2) if self._store_ms else 0.0,
        })

    def cleanup(self):
        """Release the httpx client + redis connection. Idempotent; safe to call repeatedly. MUST be
        invoked on every handler teardown/restart (the manager does so) — httpx.Client has no __del__,
        so a missed cleanup leaks keep-alive sockets per restart until fd exhaustion."""
        self.shutdown_requested = True
        if self._http is not None:
            try:
                self._http.close()
            except Exception:
                pass
            self._http = None
        if self.redis is not None:
            try:
                self.redis.close()
            except Exception:
                pass
            self.redis = None
