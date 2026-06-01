"""P1 reliability-core tests: no-silent-loss buffer + drain, stale-stream loop,
control-message hook, parse-error escalation, heartbeat, gap markers, ping-task
cleanup, and proxy rotation-on-disconnect.
"""
import json
import time
import asyncio
import pytest

from src.cex.producer.core.base_connector import BaseExchangeConnector, StaleStreamError
from src.cex.producer.config import get_stream_key, get_heartbeat_key


class _Dummy(BaseExchangeConnector):
    async def get_websocket_url(self, symbol: str = None) -> str:
        return "wss://example.invalid"

    async def parse_message(self, message):
        return None

    async def subscribe_to_symbols(self, websocket, symbols):
        return None


@pytest.fixture
def conn():
    return _Dummy("bybit", "spot")


class _FlakyRedis:
    def __init__(self, inner):
        self.inner = inner
        self.broken = True

    def heal(self):
        self.broken = False

    async def xadd(self, *a, **kw):
        if self.broken:
            raise ConnectionError("simulated redis down")
        return await self.inner.xadd(*a, **kw)

    def __getattr__(self, name):
        return getattr(self.inner, name)


async def test_xadd_failure_buffers_then_drains(conn, fake_redis, monkeypatch):
    flaky = _FlakyRedis(fake_redis)
    conn.redis_client = flaky
    conn._backpressure_max_streams = 1
    await conn._process_orderbook_data({
        "symbol": "BTCUSDT", "timestamp_ms": int(time.time() * 1000),
        "bids": [["100.0", "1.0"]], "asks": [["101.0", "1.0"]],
    })
    key = get_stream_key("bybit", "spot", "BTCUSDT")
    assert key in conn._pending_xadds
    assert conn._redis_backpressured is True

    from src.cex.producer.core.redis_manager import RedisManager
    async def _ok():
        return True
    monkeypatch.setattr(RedisManager, "health_check", classmethod(lambda cls: _ok()))
    flaky.heal()
    await conn._flush_pending_xadds()
    assert key not in conn._pending_xadds
    assert conn._redis_backpressured is False
    assert await fake_redis.xrevrange(key, count=1)


async def test_buffer_collapses_to_newest(conn, fake_redis):
    conn.redis_client = _FlakyRedis(fake_redis)
    key = get_stream_key("bybit", "spot", "ETHUSDT")
    for i in range(5):
        await conn._process_orderbook_data({
            "symbol": "ETHUSDT", "timestamp_ms": int(time.time() * 1000) + i,
            "bids": [[str(100 + i), "1.0"]], "asks": [[str(200 + i), "1.0"]],
        })
    assert list(conn._pending_xadds.keys()) == [key]
    assert json.loads(conn._pending_xadds[key]["bids"]) == [[104.0, 1.0]]


async def test_stale_stream_raises(conn, monkeypatch):
    import src.cex.producer.core.base_connector as bc
    conn.stale_stream_timeout = 5
    clock = {"now": 1000.0}
    monkeypatch.setattr(bc.time, "time", lambda: clock["now"])

    class _IdleWS:
        async def recv(self):
            clock["now"] += 3
            raise asyncio.TimeoutError()

    with pytest.raises(StaleStreamError):
        await asyncio.wait_for(conn._handle_messages(_IdleWS(), ["BTCUSDT"]), timeout=5)


async def test_control_message_hook_consumes(fake_redis):
    seen = {}

    class _CtrlDummy(_Dummy):
        async def handle_control_message(self, websocket, message):
            if message == "PING":
                await websocket.send("PONG")
                seen["ping"] = True
                return True
            return False

        async def parse_message(self, message):
            seen.setdefault("parsed", []).append(message)
            return None

    c = _CtrlDummy("bybit", "spot")
    c.redis_client = fake_redis
    c.stale_stream_timeout = 0

    class _WS:
        def __init__(self, msgs):
            self._m = list(msgs)
            self.sent = []
        async def recv(self):
            if self._m:
                return self._m.pop(0)
            raise asyncio.CancelledError()
        async def send(self, m):
            self.sent.append(m)

    ws = _WS(["PING", "DATA"])
    with pytest.raises(asyncio.CancelledError):
        await c._handle_messages(ws, ["BTCUSDT"])
    assert seen.get("ping") is True
    assert "PONG" in ws.sent
    assert "PING" not in seen.get("parsed", [])
    assert "DATA" in seen.get("parsed", [])


async def test_parse_error_escalates_to_reconnect(fake_redis):
    class _BoomDummy(_Dummy):
        async def parse_message(self, message):
            raise ValueError("bad frame")

    c = _BoomDummy("bybit", "spot")
    c.redis_client = fake_redis
    c.stale_stream_timeout = 0
    c.max_consecutive_parse_errors = 3

    class _WS:
        async def recv(self):
            return "garbage"
        async def send(self, m):
            pass

    with pytest.raises(ValueError):
        await asyncio.wait_for(c._handle_messages(_WS(), ["BTCUSDT"]), timeout=5)


async def test_heartbeat_written(conn, fake_redis):
    conn.redis_client = fake_redis
    conn._messages_processed = 42
    conn.active_symbols = {"BTCUSDT", "ETHUSDT"}
    await conn._write_heartbeat()
    raw = await fake_redis.get(get_heartbeat_key("bybit", "spot", None))
    assert raw is not None
    hb = json.loads(raw)
    assert hb["msgs"] == 42
    assert hb["active_symbols"] == 2
    assert hb["current_proxy"] == "direct"
    assert "ts" in hb and hb["schema_version"] >= 1


async def test_gap_marker_written(conn, fake_redis):
    conn.redis_client = fake_redis
    await conn._write_gap_markers(["BTCUSDT"])
    key = get_stream_key("bybit", "spot", "BTCUSDT")
    entries = await fake_redis.xrevrange(key, count=1)
    assert entries
    _id, fields = entries[0]
    assert fields["gap"] == "reconnect"
    assert json.loads(fields["bids"]) == [] and json.loads(fields["asks"]) == []


async def test_cleanup_cancels_ping_tasks(conn, fake_redis):
    conn.redis_client = fake_redis

    async def _sleeper():
        await asyncio.sleep(3600)

    t = asyncio.create_task(_sleeper())
    conn.ping_tasks["BTCUSDT"] = t
    conn.currently_monitored_symbols = set()
    await conn.cleanup()
    await asyncio.sleep(0)
    assert t.cancelled() or t.done()
    assert conn.ping_tasks == {}


def test_proxy_rotates_on_disconnect():
    from src.cex.producer.core.proxy_manager import ProxyManager, ProxyInfo
    pm = ProxyManager.__new__(ProxyManager)
    pm.mode = "load_balance"
    pm.logger = __import__("logging").getLogger("t")
    pm.proxies = [ProxyInfo(host="a", port=1, protocol="socks5"),
                  ProxyInfo(host="b", port=2, protocol="socks5")]
    pm.current_proxy_index = 0
    pm.symbol_proxy_mapping = {"BTCUSDT": 0}
    pm.symbol_route_mapping_flex = {}
    pm.flex_routes = []
    pm.current_route_index = 0
    pm.rotations = 0
    pm.connection_stats = {"rotations": 0}
    before = pm.current_proxy_label()
    asyncio.run(pm.rotate_on_disconnect("BTCUSDT"))
    after = pm.current_proxy_label()
    assert pm.rotations == 1
    assert "BTCUSDT" not in pm.symbol_proxy_mapping
    assert before != after
    assert pm.current_proxy_index == 1
