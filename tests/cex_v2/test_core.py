"""cex_v2 OrderBookConnector invariant tests (ORDERBOOK_PRODUCER_SPEC.md), via binance."""
import asyncio
import json

import fakeredis.aioredis

from src.cex_v2.config import get_stream_key, get_active_symbols_key, get_inactive_symbols_key
from src.cex_v2.core.connector import Book, coerce_levels
from src.cex_v2.plugins.binance import BinanceSpotConnector

ACTIVE = get_active_symbols_key("binance", "spot")
INACTIVE = get_inactive_symbols_key("binance", "spot")


def _conn():
    c = BinanceSpotConnector()
    c.redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    c.flush_interval = 0.02
    return c


# I1/I2/I7 — collapse-to-latest + pipelined flush is the primary path; recv_ts stamped.
def test_collapse_and_flush():
    async def run():
        c = _conn()
        c._on_books([Book("BTCUSDT", [["1", "2"]], [["1.1", "3"]], None)])
        c._on_books([Book("BTCUSDT", [["9", "2"]], [["9.1", "3"]], None),
                     Book("ETHUSDT", [["5", "1"]], [["5.1", "1"]], None)])
        t = asyncio.create_task(c._flush_loop())
        await asyncio.sleep(0.08)
        c.shutdown.set(); t.cancel()
        await asyncio.gather(t, return_exceptions=True)
        btc = await c.redis.xrevrange(get_stream_key("binance", "spot", "BTCUSDT"), count=1)
        eth = await c.redis.xrevrange(get_stream_key("binance", "spot", "ETHUSDT"), count=1)
        active = await c.redis.smembers(ACTIVE)
        return btc, eth, active, dict(c._latest)

    btc, eth, active, pending = asyncio.run(run())
    assert btc and json.loads(btc[0][1]["bids"]) == [[9.0, 2.0]]   # collapsed to latest
    assert int(btc[0][1]["recv_ts_ms"]) > 0                        # recv-time stamped
    assert eth and json.loads(eth[0][1]["bids"]) == [[5.0, 1.0]]
    assert active == {"BTCUSDT", "ETHUSDT"}
    assert pending == {}


# I2/I3 — hot path is sync, non-blocking, normalizes to uppercase.
def test_hot_path_sync_nonblocking():
    import inspect
    c = BinanceSpotConnector()
    c.redis = None
    c._on_books([Book("btcusdt", [["1", "2"]], [["1.1", "3"]], None)])
    assert not inspect.iscoroutinefunction(c._on_books)
    assert "BTCUSDT" in c._latest and "BTCUSDT" in c._pending_activate and c._msgs == 1


# I6 — inactivation evicts + deletes the stream.
def test_mark_inactive():
    async def run():
        c = _conn()
        sk = get_stream_key("binance", "spot", "BTCUSDT")
        await c.redis.sadd(ACTIVE, "BTCUSDT")
        await c.redis.xadd(sk, {"x": "1"})
        c.active.add("BTCUSDT")
        await c._mark_inactive(["BTCUSDT"])
        return (await c.redis.sismember(ACTIVE, "BTCUSDT"),
                await c.redis.sismember(INACTIVE, "BTCUSDT"),
                await c.redis.exists(sk))

    in_a, in_i, exists = asyncio.run(run())
    assert not in_a and in_i and not exists


# Delist-eviction removes from BOTH sets + deletes the stream (vs _mark_inactive which keeps inactive).
def test_evict_delisted():
    async def run():
        c = _conn()
        sk = get_stream_key("binance", "spot", "DEADUSDT")
        await c.redis.sadd(ACTIVE, "DEADUSDT")
        await c.redis.sadd(INACTIVE, "DEADUSDT")
        await c.redis.xadd(sk, {"x": "1"})
        c.active.add("DEADUSDT"); c.monitored.add("DEADUSDT")
        await c._evict(["DEADUSDT"])
        return (await c.redis.sismember(ACTIVE, "DEADUSDT"),
                await c.redis.sismember(INACTIVE, "DEADUSDT"),
                await c.redis.exists(sk), "DEADUSDT" in c.monitored, "DEADUSDT" in c.active)

    in_a, in_i, exists, mon, act = asyncio.run(run())
    assert not in_a and not in_i and not exists and not mon and not act


# Startup reconcile prunes orphan active/inactive members + streams not in the current universe,
# but keeps symbols that ARE listed (and no-ops on an empty universe).
def test_reconcile_orphans():
    live = [f"S{i}USDT" for i in range(10)]

    async def run():
        c = _conn()
        await c.redis.sadd(ACTIVE, *live, "DEADUSDT")
        await c.redis.sadd(INACTIVE, "GONEUSDT")
        live_sk = get_stream_key("binance", "spot", "S0USDT")
        orphan_sk = get_stream_key("binance", "spot", "DEADUSDT")
        await c.redis.xadd(live_sk, {"x": "1"}); await c.redis.xadd(orphan_sk, {"x": "1"})
        await c._reconcile_orphans(set(live))   # only the 10 live symbols are listed
        keep = await c.redis.sismember(ACTIVE, "S0USDT")
        dead = await c.redis.sismember(ACTIVE, "DEADUSDT")
        gone = await c.redis.sismember(INACTIVE, "GONEUSDT")
        await c._reconcile_orphans(set())   # empty universe must be a no-op (feeder not ready)
        keep2 = await c.redis.sismember(ACTIVE, "S0USDT")
        return keep, dead, gone, await c.redis.exists(orphan_sk), await c.redis.exists(live_sk), keep2

    keep, dead, gone, orphan_stream, live_stream, keep2 = asyncio.run(run())
    assert keep and not dead and not gone and not orphan_stream and live_stream and keep2


# Reconcile SKIPS when the universe is implausibly small vs the existing active+inactive set
# (degraded/cold feeder) — must never mass-evict live symbols on a respawn against a partial feed.
def test_reconcile_skips_on_collapsed_universe():
    live = [f"S{i}USDT" for i in range(10)]

    async def run():
        c = _conn()
        await c.redis.sadd(ACTIVE, *live)
        await c._reconcile_orphans({"S0USDT"})   # universe=1 << active=10 -> SKIP
        return await c.redis.scard(ACTIVE)

    assert asyncio.run(run()) == 10   # nothing evicted


# Reconcile is a no-op for a multi-worker (distributed) connector — its universe is only a shard,
# so a full-set reconcile would evict other workers' live symbols.
def test_reconcile_skips_for_distributed_worker():
    async def run():
        c = BinanceSpotConnector(worker_id=0, num_workers=2)
        c.redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        assert c.is_distributed
        await c.redis.sadd(ACTIVE, "BTCUSDT", "DEADUSDT")
        await c._reconcile_orphans({"BTCUSDT"})   # would evict DEADUSDT if not gated
        return await c.redis.scard(ACTIVE)

    assert asyncio.run(run()) == 2   # untouched


# Eviction only fires after N CONSECUTIVE absent scans; a reappearance resets the counter.
def test_monitor_evicts_only_after_consecutive_absence():
    from src.cex_v2.config import MONITORING

    async def run():
        c = _conn()
        c.monitored = {"GONEUSDT", "ALIVEUSDT"}   # ALIVE stays listed every scan (non-empty universe)
        c._batches = lambda syms: []              # don't spawn real connections for re-adds
        evicted = []

        async def fake_evict(s):
            evicted.extend(s)
        c._evict = fake_evict

        a = {"ALIVEUSDT"}
        # present, absent(1), present(reset), absent(1), absent(2), absent(3 -> evict)
        seq = iter([a | {"GONEUSDT"}, a, a | {"GONEUSDT"}, a, a, a])

        async def fake_syms():
            try:
                return list(next(seq))
            except StopIteration:
                c.shutdown.set()
                return ["GONEUSDT"]
        c.get_symbols = fake_syms

        orig = dict(MONITORING)
        MONITORING["symbol_refresh_interval"] = 0
        MONITORING["evict_after_scans"] = 3
        try:
            await c._monitor_loop()
        finally:
            MONITORING.update(orig)
        return evicted

    assert asyncio.run(run()) == ["GONEUSDT"]


# A symbol absent from the feeder universe but STILL streaming books (fresh last_update_wall) is a
# feeder hiccup / brief halt, NOT a delist — it must never be evicted (counter stays reset).
def test_monitor_keeps_absent_but_streaming_symbol():
    import time as _t
    from src.cex_v2.config import MONITORING

    async def run():
        c = _conn()
        c.monitored = {"HALTUSDT", "ALIVEUSDT"}
        c._batches = lambda syms: []
        evicted = []

        async def fake_evict(s):
            evicted.extend(s)
        c._evict = fake_evict
        c.last_update_wall["HALTUSDT"] = _t.time()   # still writing -> not a delist

        a = {"ALIVEUSDT"}
        seq = iter([a, a, a, a, a])   # HALTUSDT absent from the feeder every scan

        async def fake_syms():
            try:
                return list(next(seq))
            except StopIteration:
                c.shutdown.set()
                return ["ALIVEUSDT"]
        c.get_symbols = fake_syms

        orig = dict(MONITORING)
        MONITORING["symbol_refresh_interval"] = 0
        MONITORING["evict_after_scans"] = 3
        try:
            await c._monitor_loop()
        finally:
            MONITORING.update(orig)
        return evicted, c._absent_scans.get("HALTUSDT", 0)

    evicted, cnt = asyncio.run(run())
    assert evicted == [] and cnt == 0


def test_coerce_levels():
    assert coerce_levels([["1.5", "2"], ["x", "y"], ["3", "4"]]) == [[1.5, 2.0], [3.0, 4.0]]


def test_binance_parse_and_subscribe():
    c = BinanceSpotConnector()
    ob = json.dumps({"stream": "btcusdt@depth20@100ms", "data": {"bids": [["6", "1"]], "asks": [["6.1", "1"]]}})
    books = c.parse(ob)
    assert books and books[0].symbol == "BTCUSDT" and books[0].event_ts_ms is None
    assert c.parse('{"result":null,"id":1}') is None and c.parse("nope") is None

    sent = []

    class _WS:
        async def send(self, m): sent.append(json.loads(m))

    asyncio.run(c.subscribe(_WS(), ["BTCUSDT", "ETHUSDT"]))
    assert sent[0]["method"] == "SUBSCRIBE"
    assert sent[0]["params"] == ["btcusdt@depth20@100ms", "ethusdt@depth20@100ms"]


def test_supervisor_discovers_binance():
    from src.cex_v2.supervisor import _discover
    t = {x.name: x for x in _discover() if x.exchange == "binance"}
    assert t["binance_spot"].class_name == "BinanceSpotConnector"
    assert t["binance_futures"].class_name == "BinanceFuturesConnector"
