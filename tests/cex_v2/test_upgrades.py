"""Production-grade upgrades: orjson jsonio, concurrent httpx _get_many, httpx fetch, prometheus
metrics (graceful), typed pydantic settings."""
import socket

import httpx
import pytest
import respx

from src.cex_v2.core.jsonio import dumps, loads, HAVE_ORJSON
from src.cex_v2.market_data.handlers.binance import BinanceSpotMarketData


# --- orjson json util ---
def test_jsonio_roundtrip_and_orjson_active():
    assert HAVE_ORJSON is True                       # orjson is installed -> the fast path is live
    obj = {"a": 1, "b": [1, 2, 3], "c": "x"}
    assert loads(dumps(obj)) == obj
    assert dumps([[64623.91, 0.98851]]) == "[[64623.91,0.98851]]"  # compact, no spaces


# --- concurrent multi-endpoint fetch maps strictly by URL (order-independent) ---
def test_get_many_maps_by_url():
    h = BinanceSpotMarketData()
    called = []
    h._get = lambda url: (called.append(url), {"for": url})[1]
    out = h._get_many(["http://a", "http://b", "http://c"])
    assert out == {"http://a": {"for": "http://a"}, "http://b": {"for": "http://b"},
                   "http://c": {"for": "http://c"}}
    assert set(called) == {"http://a", "http://b", "http://c"}   # all fetched


# --- real httpx client path (mocked transport) ---
@respx.mock
def test_fetch_uses_httpx_client():
    h = BinanceSpotMarketData()
    h._http = httpx.Client(timeout=5)
    respx.get(h.api_endpoint).mock(return_value=httpx.Response(200, json=[{"symbol": "BTCUSDT"}]))
    try:
        assert h._fetch() == [{"symbol": "BTCUSDT"}]
    finally:
        h._http.close()


# --- prometheus metrics: record without raising + graceful server ---
def test_metrics_record_and_graceful_server():
    from src.cex_v2.observability import metrics as m
    assert m.HAVE_PROM is True
    m.OB_MSGS.labels("binance", "spot").inc(5)
    m.OB_FLUSH.labels("binance", "spot").observe(0.003)
    m.OB_ACTIVE.labels("binance", "spot").set(700)
    m.MD_UPDATES.labels("binance", "spot", "ok").inc()
    m.MD_FETCH.labels("binance", "spot").observe(0.5)

    assert m.start_metrics_server(0, enabled=False) is False      # disabled -> no server, no raise
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    assert m.start_metrics_server(port, enabled=True) is True     # binds a free port
    assert m.start_metrics_server(port, enabled=True) is False    # port taken -> graceful False, no raise


# --- typed pydantic settings (no raw os.environ) ---
def test_settings_typed_and_validated():
    from src.cex_v2.settings import CexV2Settings
    s = CexV2Settings()
    assert s.log_dir.is_absolute()
    assert s.log_level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    assert isinstance(s.metrics_port_base, int) and s.metrics_enabled in (True, False)
    with pytest.raises(Exception):
        CexV2Settings(log_level="bogus")             # validator rejects an invalid level


# --- review fix: coerce_levels drops non-finite (nan/inf would serialize as JSON null) ---
def test_coerce_levels_drops_non_finite():
    from src.cex_v2.core.connector import coerce_levels
    out = coerce_levels([["1.5", "2"], ["nan", "1"], ["inf", "1"], ["-inf", "1"], ["3", "4"]])
    assert out == [[1.5, 2.0], [3.0, 4.0]]           # nan/inf/-inf dropped, finite kept


# --- review fix: cleanup() releases httpx + redis (httpx has no __del__) ---
def test_base_cleanup_closes_http_and_redis():
    h = BinanceSpotMarketData()

    class _Closeable:
        def __init__(self): self.closed = False
        def close(self): self.closed = True

    h._http, h.redis = _Closeable(), _Closeable()
    http, rds = h._http, h.redis
    h.cleanup()
    assert http.closed and rds.closed and h.shutdown_requested
    assert h._http is None and h.redis is None       # nulled so a double-cleanup is a no-op
    h.cleanup()                                       # idempotent, must not raise


# --- review fix: manager invokes cleanup() on crash-restart AND shutdown (the leak fix) ---
def test_manager_cleans_handler_on_crash(monkeypatch):
    from src.cex_v2.market_data import manager as M
    closed = []
    mgr = M.MarketDataManager()

    class FakeH:
        def __init__(self): self.shutdown_requested = False
        def initialize(self): return True
        def run(self): mgr.stop.set(); raise RuntimeError("boom")   # crash, and stop so the loop exits
        def cleanup(self): closed.append(1)

    monkeypatch.setattr(M, "_make_handler", lambda e, m: FakeH())
    mgr._run_handler("binance_spot", "binance", "spot")
    assert closed == [1]                              # cleanup ran in the finally despite the crash


def test_manager_shutdown_cleans_handlers():
    from src.cex_v2.market_data.manager import MarketDataManager
    closed = []

    class FakeH:
        shutdown_requested = False
        def cleanup(self): closed.append(1)

    mgr = MarketDataManager()
    mgr.handlers["binance_spot"] = FakeH()
    mgr.shutdown()
    assert closed == [1]
