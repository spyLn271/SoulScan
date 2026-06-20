"""Core per-connection observability: OrderBookConnector._emit_perf emits one `ob_conn` line per connection
(symbol count, up/down, per-conn reconnects + conn_errors, last-data age) + an `ob_conn_summary` line. This
is venue-agnostic (lives in the core connector) — instrumentation only, no behavior change."""
import time

from src.cex_v2.plugins.binance import BinanceSpotConnector


def _emit_and_capture(c, monkeypatch):
    import src.cex_v2.core.connector as conn
    captured = []
    monkeypatch.setattr(conn, "emit_perf", lambda rec: captured.append(rec))
    c._emit_perf()
    return captured


def test_emit_perf_emits_per_connection_lines(monkeypatch):
    c = BinanceSpotConnector()   # any concrete connector; observability is in the shared base
    now = time.time()
    c._conn_stats = {
        "b0": {"syms": ["BTCUSDT", "ETHUSDT"], "up": True, "reconnects": 2, "conn_errors": 1},
        "b1": {"syms": ["SOLUSDT"], "up": False, "reconnects": 0, "conn_errors": 0},
    }
    c.last_update_wall = {"BTCUSDT": now - 0.5, "ETHUSDT": now - 3, "SOLUSDT": 0}
    recs = _emit_and_capture(c, monkeypatch)

    conns = {r["conn"]: r for r in recs if r.get("kind_detail") == "ob_conn"}
    assert set(conns) == {"b0", "b1"}
    assert conns["b0"]["symbols"] == 2 and conns["b0"]["up"] is True
    assert conns["b0"]["reconnects"] == 2 and conns["b0"]["conn_errors"] == 1
    assert conns["b0"]["last_data_age_s"] is not None and conns["b0"]["last_data_age_s"] < 1.0   # max(0.5,3)->0.5
    assert conns["b1"]["up"] is False and conns["b1"]["last_data_age_s"] is None  # no data -> None

    summary = [r for r in recs if r.get("kind_detail") == "ob_conn_summary"]
    assert len(summary) == 1 and summary[0]["conns"] == 2

    agg = [r for r in recs if "msgs_per_s" in r]
    assert len(agg) == 1   # the aggregate line still fires exactly once (unchanged)


def test_emit_perf_no_connections_only_aggregate(monkeypatch):
    c = BinanceSpotConnector()
    c._conn_stats = {}
    recs = _emit_and_capture(c, monkeypatch)
    assert not [r for r in recs if r.get("kind_detail") == "ob_conn"]
    assert [r for r in recs if r.get("kind_detail") == "ob_conn_summary"][0]["conns"] == 0
    assert len([r for r in recs if "msgs_per_s" in r]) == 1   # aggregate unaffected


def test_heartbeat_payload_carries_connection_health():
    """The heartbeat ('health') surfaces WS connection summary fields, not just symbol health."""
    c = BinanceSpotConnector()
    c._conn_stats = {
        "b0": {"syms": ["BTCUSDT"], "up": True, "reconnects": 1, "conn_errors": 0},
        "b1": {"syms": ["ETHUSDT"], "up": False, "reconnects": 0, "conn_errors": 2},
        "b2": {"syms": ["SOLUSDT"], "up": True, "reconnects": 0, "conn_errors": 0},
    }
    c._reconnects = 1
    c._conn_errors = 2
    c.active = {"BTCUSDT", "SOLUSDT"}

    hb = c._heartbeat_payload()
    # new connection-health fields
    assert hb["connections"] == 3
    assert hb["connections_up"] == 2          # b0 + b2 up; b1 down
    assert hb["reconnects"] == 1 and hb["conn_errors"] == 2
    # existing symbol-health fields still present (no regression)
    for k in ("ts", "msgs", "active_symbols", "monitored_symbols", "stale_symbols",
              "buffered_streams", "redis_backpressured", "schema_version"):
        assert k in hb
    assert hb["active_symbols"] == 2


def test_heartbeat_payload_no_connections():
    c = BinanceSpotConnector()   # fresh: _conn_stats empty, counters 0
    hb = c._heartbeat_payload()
    assert hb["connections"] == 0 and hb["connections_up"] == 0
    assert hb["reconnects"] == 0 and hb["conn_errors"] == 0
