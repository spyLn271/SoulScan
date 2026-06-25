import abc
import asyncio
import logging
import math
import random
import time
from collections import deque, namedtuple
from typing import Any, Dict, List, Optional, Set

import redis.asyncio as redis

from src.cex.config import (
    get_exchange_config, get_redis_config, get_stream_key, get_heartbeat_key,
    get_active_symbols_key, get_inactive_symbols_key, get_market_data_key,
    MONITORING, SCHEMA_VERSION, ORDERBOOK_MAXLEN, LOGGING,
)
from src.cex.core.jsonio import dumps as _dumps
from src.cex.core.ws_connect import connect_with_proxy_config
from src.cex.observability import emit_perf
from src.cex.observability import metrics as _m



Book = namedtuple("Book", "symbol bids asks event_ts_ms")


class ResyncRequired(Exception):
    """"""


def coerce_levels(levels) -> List[List[float]]:
    out = []
    for lvl in levels:
        try:
            p, q = float(lvl[0]), float(lvl[1])
        except (TypeError, ValueError, IndexError):
            continue

        if not (math.isfinite(p) and math.isfinite(q)):
            continue

        out.append([p, q])

    return out


class OrderBookConnector(abc.ABC):
    def __init__(
            self,
            exchange: str,
            market_type: str = "spot",
            worker_id: int = None,
            num_workers: int = None
    ):
        self.exchange = exchange
        self.market_type = market_type
        self.worker_id = worker_id
        self.num_workers = num_workers
        self.is_distributed = worker_id is not None and num_workers is not None

        cfg = get_exchange_config(exchange) or {}
        self.config = cfg
        mc = cfg.get(market_type, {})
        self.market_config = mc
        self.use_proxy = bool(cfg.get("proxy", {}).get("use_proxy"))
        self.connection_type = mc.get("connection_type", "batched")
        self.symbols_per_connection = 1 if self.connection_type == "individual" else \
            int(mc.get("symbols_per_connection", 20) or 20)
        self.ping_interval = mc.get("ping_interval")
        self.flush_interval = float(mc.get("flush_interval", MONITORING["flush_interval"]))
        self.reconnect_base = float(mc.get("reconnect_delay_base", 2.0))
        self.reconnect_max = float(mc.get("reconnect_delay_max", 60))
        self.special_params = mc.get("special_params", {})
        self.cleanup_after_failures = mc.get("cleanup_after_failures", MONITORING["cleanup_after_failures"])
        self.stale_symbol_age = mc.get("stale_symbol_age", MONITORING["stale_symbol_age"])

        suffix = "" if worker_id is None else f"-w{worker_id}"
        self.logger = logging.getLogger(f"cexv2.{exchange}.{market_type}{suffix}")

        self.redis: Optional[redis.Redis] = None
        self.shutdown = asyncio.Event()
        self._latest: Dict[str, tuple] = {}
        self.active: Set[str] = set()
        self._pending_activate: Set[str] = set()
        self.last_update_wall: Dict[str, float] = {}
        self.monitored: Set[str] = set()
        self._absent_scans: Dict[str, int] = {}
        self._msgs = 0
        self._backpressured = False
        self._conn_tasks: Dict[str, asyncio.Task] = {}
        self._conn_stats: Dict[str, dict] = {}
        self._t0 = time.time()
        self._reconnects = 0
        self._conn_errors = 0
        self._flushes = 0
        self._flush_ms = deque(maxlen=2000)
        self._last_perf = (time.time(), 0)
        self.perf_interval = float(LOGGING.get("perf_interval", 30))

    @abc.abstractmethod
    async def ws_url(self) -> str: ...

    @abc.abstractmethod
    async def subscribe(self, ws, symbols: List[str]) -> None: ...

    @abc.abstractmethod
    def parse(self, raw) -> Optional[List[Book]]:
        """SYNC, fast: one raw frame -> list[Book] (or None for control frames)."""

    async def handle_control(self, ws, raw) -> bool:
        return False

    async def ping_message(self) -> Optional[str]:
        return None

    async def proxy_config(self) -> Optional[Dict[str, Any]]:
        return None

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.upper()

    async def get_symbols(self) -> List[str]:
        data = await self.redis.hgetall(get_market_data_key(self.exchange, self.market_type))
        syms = [s for s in (data or {}) if not s.startswith("_")]

        return self._filter_for_worker(sorted(syms))

    def _filter_for_worker(self, symbols: List[str]) -> List[str]:
        if not self.is_distributed:
            return symbols

        return [s for i, s in enumerate(symbols) if i % self.num_workers == self.worker_id]

    def _batches(self, symbols: List[str]) -> List[List[str]]:
        n = self.symbols_per_connection
        return [symbols[i:i + n] for i in range(0, len(symbols), n)]

    async def start(self):
        rc = get_redis_config()
        wid = "none" if self.worker_id is None else self.worker_id
        self.redis = redis.Redis(
            host=rc["host"],
            port=rc["port"],
            db=rc.get("db", 0),
            password=rc.get("password"), decode_responses=True,
            client_name=f"cexv2:ob:{self.exchange}:{self.market_type}:{wid}"
        )
        await self.redis.ping()
        symbols = await self.get_symbols()
        self.monitored = set(symbols)
        await self._reconcile_orphans(set(symbols))

        self.logger.info("start %s/%s: %d symbols, %s %d/conn, flush=%ss, proxy=%s",
                         self.exchange, self.market_type, len(symbols), self.connection_type,
                         self.symbols_per_connection, self.flush_interval, self.use_proxy)

        tasks = [
            asyncio.create_task(self._flush_loop()),
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._monitor_loop()),
            asyncio.create_task(self._perf_loop())
        ]
        for bid, batch in enumerate(self._batches(symbols)):
            self._conn_tasks[f"b{bid}"] = asyncio.create_task(self._connection_loop(f"b{bid}", batch))

        tasks.extend(self._conn_tasks.values())

        await asyncio.gather(*tasks, return_exceptions=True)

    async def cleanup(self):
        self.shutdown.set()
        if self.redis:
            try:
                await self.redis.aclose()
            except Exception:
                pass


    async def _connection_kwargs(self, proxied: bool) -> Dict[str, Any]:
        return {
            "open_timeout": MONITORING["connection_timeout"],
            "close_timeout": 10,
            "ping_interval": 15 if proxied else None,
            "ping_timeout": 20 if proxied else None,
            "compression": None,
        }

    async def _connection_loop(self, name: str, symbols: List[str]):
        failures = 0
        established = 0
        delay = self.reconnect_base
        self._conn_stats[name] = {"syms": symbols, "up": False, "reconnects": 0, "conn_errors": 0}
        while not self.shutdown.is_set():
            ws = None
            ping_task = None
            try:
                pc = await self.proxy_config()
                ws = await connect_with_proxy_config(
                    await self.ws_url(),
                    pc,
                    **(await self._connection_kwargs(pc is not None))
                )

                if established:
                    self._reconnects += 1
                    _m.OB_RECONNECTS.labels(self.exchange, self.market_type).inc()

                established += 1
                failures = 0
                delay = self.reconnect_base
                st = self._conn_stats.get(name)
                if st is not None:
                    st["up"] = True
                    if established > 1:
                        st["reconnects"] += 1

                await self.subscribe(ws, symbols)
                if self.ping_interval:
                    ping_task = asyncio.create_task(self._ping_loop(ws))

                await self._recv_loop(ws, symbols)
            except asyncio.CancelledError:
                break
            except ResyncRequired as e:
                failures = 0
                self.logger.info("[%s] resync: %s", name, e)
            except Exception as e:
                failures += 1
                self._conn_errors += 1
                _m.OB_CONN_ERRORS.labels(self.exchange, self.market_type).inc()
                st = self._conn_stats.get(name)
                if st is not None:
                    st["conn_errors"] += 1
                    st["up"] = False

                self.logger.warning("[%s] conn error (%d): %s: %s", name, failures,
                                    type(e).__name__, str(e)[:160])
                if failures >= self.cleanup_after_failures:
                    await self._mark_inactive(symbols)
            finally:
                if ping_task:
                    ping_task.cancel()
                if ws is not None:
                    try:
                        await ws.close()
                    except Exception:
                        pass
                if name in self._conn_stats:
                    self._conn_stats[name]["up"] = False
            if not self.shutdown.is_set():
                capped = min(delay, self.reconnect_max)
                await asyncio.sleep(capped + random.uniform(0, capped * 0.3))
                delay *= 2

    async def _recv_loop(self, ws, symbols: List[str]):
        timeout = MONITORING["stale_stream_timeout"]
        recv_timeout = min(timeout, MONITORING["recv_poll_timeout"]) if timeout else None
        last = time.time()
        while not self.shutdown.is_set():
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=recv_timeout) if recv_timeout else await ws.recv()
            except asyncio.TimeoutError:
                if timeout and (time.time() - last) > timeout:
                    raise TimeoutError(f"no data for {timeout}s (stale)")
                continue
            last = time.time()
            try:
                if await self.handle_control(ws, raw):
                    continue
            except Exception:
                pass
            try:
                books = self.parse(raw)
            except ResyncRequired:
                raise
            except Exception as e:
                self.logger.warning("parse error (frame dropped): %s: %s", type(e).__name__, str(e)[:140])
                continue
            if books:
                self._on_books(books)

    def _on_books(self, books: List[Book]):
        now_ms = int(time.time() * 1000)
        wall = time.time()
        for bk in books:
            sym = self.normalize_symbol(bk.symbol)
            self._latest[sym] = (bk.bids, bk.asks, bk.event_ts_ms, now_ms)
            self._msgs += 1
            self.last_update_wall[sym] = wall
            if sym not in self.active:
                self._pending_activate.add(sym)

    async def _ping_loop(self, ws):
        msg = await self.ping_message()
        if msg is None:
            return
        interval = max((self.ping_interval or 20000) / 1000.0, 5)
        while not self.shutdown.is_set():
            try:
                await ws.send(msg)
            except Exception:
                break
            await asyncio.sleep(interval)

    async def _flush_loop(self):
        while not self.shutdown.is_set():
            try:
                await asyncio.sleep(self.flush_interval)
                if not self._latest:
                    continue
                batch = self._latest
                self._latest = {}
                pipe = self.redis.pipeline(transaction=False)
                for sym, (bids, asks, event_ts, recv_ts) in batch.items():
                    pipe.xadd(get_stream_key(self.exchange, self.market_type, sym), {
                        "timestamp_ms": event_ts if event_ts is not None else recv_ts,
                        "recv_ts_ms": recv_ts,
                        "symbol": sym,
                        "bids": _dumps(coerce_levels(bids)),
                        "asks": _dumps(coerce_levels(asks)),
                        "schema_version": SCHEMA_VERSION,
                        "worker_id": "none" if self.worker_id is None else self.worker_id,
                    }, id="*", maxlen=ORDERBOOK_MAXLEN, approximate=True)
                _t = time.perf_counter()
                await pipe.execute()
                _dt = time.perf_counter() - _t
                self._flush_ms.append(_dt * 1000.0)
                self._flushes += 1
                _m.OB_FLUSH.labels(self.exchange, self.market_type).observe(_dt)
                _m.OB_MSGS.labels(self.exchange, self.market_type).inc(len(batch))
                self._backpressured = False
                if self._pending_activate:
                    await self._activate(self._pending_activate)
                    self._pending_activate = set()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._backpressured = True
                self.logger.error("flush failed: %s: %s", type(e).__name__, str(e)[:160])

    async def _activate(self, symbols: Set[str]):
        syms = list(symbols)
        try:
            pipe = self.redis.pipeline(transaction=False)
            pipe.sadd(get_active_symbols_key(self.exchange, self.market_type), *syms)
            pipe.srem(get_inactive_symbols_key(self.exchange, self.market_type), *syms)
            await pipe.execute()
            self.active.update(syms)
        except Exception as e:
            self.logger.debug("activate failed: %s", e)

    async def _mark_inactive(self, symbols: List[str]):
        syms = [self.normalize_symbol(s) for s in symbols]
        try:
            pipe = self.redis.pipeline(transaction=False)
            pipe.srem(get_active_symbols_key(self.exchange, self.market_type), *syms)
            pipe.sadd(get_inactive_symbols_key(self.exchange, self.market_type), *syms)
            for s in syms:
                pipe.delete(get_stream_key(self.exchange, self.market_type, s))
            await pipe.execute()
            self.active.difference_update(syms)
            self.logger.warning("marked %d symbols inactive (sustained failure)", len(syms))
        except Exception as e:
            self.logger.debug("mark_inactive failed: %s", e)

    async def _evict(self, symbols: List[str]):
        syms = [self.normalize_symbol(s) for s in symbols]
        try:
            pipe = self.redis.pipeline(transaction=False)
            pipe.srem(get_active_symbols_key(self.exchange, self.market_type), *syms)
            pipe.srem(get_inactive_symbols_key(self.exchange, self.market_type), *syms)
            for s in syms:
                pipe.delete(get_stream_key(self.exchange, self.market_type, s))
            await pipe.execute()
        except Exception as e:
            self.logger.debug("evict failed: %s", e)
        self.active.difference_update(syms)
        self.monitored.difference_update(syms)
        for s in syms:
            self._absent_scans.pop(s, None)
            self._latest.pop(s, None)
        self.logger.warning("evicted %d delisted symbols", len(syms))

    async def _reconcile_orphans(self, universe: Set[str]):
        if not universe:
            return
        if self.is_distributed:
            return
        try:
            active = await self.redis.smembers(get_active_symbols_key(self.exchange, self.market_type))
            inactive = await self.redis.smembers(get_inactive_symbols_key(self.exchange, self.market_type))
        except Exception as e:
            self.logger.debug("orphan reconcile read failed: %s", e)
            return
        known = {self.normalize_symbol(s) for s in universe}
        existing = set(active or []) | set(inactive or [])
        floor = MONITORING.get("reconcile_min_fraction", 0.5)
        if existing and len(known) < floor * len(existing):
            self.logger.warning("startup: SKIP orphan reconcile (universe=%d << active+inactive=%d; "
                                "feeder likely degraded/cold)", len(known), len(existing))
            return
        orphans = [s for s in existing if self.normalize_symbol(s) not in known]
        if orphans:
            self.logger.warning("startup: reconciling %d orphan symbols (gone from feeder universe)",
                                len(orphans))
            await self._evict(orphans)

    def _heartbeat_payload(self) -> dict:
        now = time.time()
        stale = sum(1 for s in self.active
                    if now - self.last_update_wall.get(s, 0) > self.stale_symbol_age)
        return {
            "ts": int(now * 1000), "msgs": self._msgs, "active_symbols": len(self.active),
            "monitored_symbols": len(self.monitored), "stale_symbols": stale,
            "buffered_streams": len(self._latest), "redis_backpressured": self._backpressured,
            "connections": len(self._conn_stats),
            "connections_up": sum(1 for st in self._conn_stats.values() if st.get("up")),
            "reconnects": self._reconnects, "conn_errors": self._conn_errors,
            "monitoring_healthy": True, "current_proxy": "direct" if not self.use_proxy else "socks5",
            "proxy_rotations": 0, "worker_id": "none" if self.worker_id is None else self.worker_id,
            "schema_version": SCHEMA_VERSION,
        }

    async def _heartbeat_loop(self):
        while not self.shutdown.is_set():
            try:
                payload = self._heartbeat_payload()
                await self.redis.set(get_heartbeat_key(self.exchange, self.market_type, self.worker_id),
                                     _dumps(payload), ex=MONITORING["heartbeat_ttl"])
                if self.active:
                    await self.redis.sadd(
                        get_active_symbols_key(self.exchange, self.market_type), *self.active)
            except Exception as e:
                self.logger.debug("heartbeat failed: %s", e)
            await asyncio.sleep(MONITORING["heartbeat_interval"])

    async def _monitor_loop(self):
        evict_after = MONITORING.get("evict_after_scans", 3)
        while not self.shutdown.is_set():
            await asyncio.sleep(MONITORING["symbol_refresh_interval"])
            try:
                current = set(await self.get_symbols())
                if not current:
                    continue
                new = current - self.monitored
                if new:
                    self.monitored |= new
                    for bid, batch in enumerate(self._batches(sorted(new))):
                        name = f"add{int(time.time())}_{bid}"
                        self._conn_tasks[name] = asyncio.create_task(self._connection_loop(name, batch))
                    self.logger.info("added %d new symbols", len(new))
                if not self.is_distributed:
                    now = time.time()
                    for s in current:
                        self._absent_scans.pop(s, None)
                    evict = []
                    for s in (self.monitored - current):
                        if now - self.last_update_wall.get(s, 0) < self.stale_symbol_age:
                            self._absent_scans.pop(s, None)   # still streaming -> not a delist
                            continue
                        self._absent_scans[s] = self._absent_scans.get(s, 0) + 1
                        if self._absent_scans[s] >= evict_after:
                            evict.append(s)
                    if evict:
                        await self._evict(evict)
            except Exception as e:
                self.logger.error("monitor error: %s", e)

    async def _perf_loop(self):
        while not self.shutdown.is_set():
            await asyncio.sleep(self.perf_interval)
            try:
                self._emit_perf()
            except Exception as e:
                self.logger.debug("perf emit failed: %s", e)

    def _emit_perf(self):
        now = time.time()
        lt, lm = self._last_perf
        dt = max(now - lt, 1e-6)
        mps = (self._msgs - lm) / dt
        self._last_perf = (now, self._msgs)
        fl = sorted(self._flush_ms)

        def pct(p):
            return round(fl[min(len(fl) - 1, int(len(fl) * p))], 3) if fl else 0.0

        _m.OB_ACTIVE.labels(self.exchange, self.market_type).set(len(self.active))
        _m.OB_MONITORED.labels(self.exchange, self.market_type).set(len(self.monitored))
        _m.OB_BACKPRESSURE.labels(self.exchange, self.market_type).set(1 if self._backpressured else 0)
        emit_perf({
            "exchange": self.exchange, "market": self.market_type,
            "worker": "none" if self.worker_id is None else self.worker_id,
            "uptime_s": round(now - self._t0, 1),
            "msgs_total": self._msgs, "msgs_per_s": round(mps, 1),
            "active": len(self.active), "monitored": len(self.monitored),
            "buffered": len(self._latest), "backpressured": self._backpressured,
            "reconnects": self._reconnects, "conn_errors": self._conn_errors,
            "flushes": self._flushes,
            "flush_p50_ms": pct(0.5), "flush_p99_ms": pct(0.99),
            "flush_max_ms": round(max(fl), 3) if fl else 0.0,
        })
        try:
            for cname, st in list(self._conn_stats.items()):
                syms = st.get("syms") or []
                last = max((self.last_update_wall.get(s, 0) for s in syms), default=0)
                emit_perf({
                    "exchange": self.exchange, "market": self.market_type, "kind_detail": "ob_conn",
                    "conn": cname, "symbols": len(syms), "up": st.get("up", False),
                    "reconnects": st.get("reconnects", 0), "conn_errors": st.get("conn_errors", 0),
                    "last_data_age_s": round(now - last, 1) if last else None,
                })
            emit_perf({"exchange": self.exchange, "market": self.market_type,
                       "kind_detail": "ob_conn_summary", "conns": len(self._conn_stats)})
        except Exception:
            pass
