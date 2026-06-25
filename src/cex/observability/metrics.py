import logging

log = logging.getLogger("cexv2.metrics")

try:
    from prometheus_client import Counter, Gauge, Histogram, start_http_server
    HAVE_PROM = True
except ImportError:
    HAVE_PROM = False

    class _Stub:
        def labels(self, *a, **k):
            return self

        def inc(self, *a, **k):
            pass

        def observe(self, *a, **k):
            pass

        def set(self, *a, **k):
            pass

    def Counter(*a, **k):
        return _Stub()

    def Gauge(*a, **k):
        return _Stub()

    def Histogram(*a, **k):
        return _Stub()

    def start_http_server(*a, **k):
        raise RuntimeError("prometheus_client not installed")


# --- order-book (label: exchange, market) ---
_FLUSH_BUCKETS = (.001, .0025, .005, .01, .025, .05, .1, .25, .5, 1.0)
OB_MSGS = Counter("cexv2_orderbook_messages_total", "depth messages flushed to redis", ["exchange", "market"])
OB_FLUSH = Histogram("cexv2_orderbook_flush_seconds", "redis flush (pipeline execute) latency",
                     ["exchange", "market"], buckets=_FLUSH_BUCKETS)
OB_ACTIVE = Gauge("cexv2_orderbook_active_symbols", "symbols with a live stream", ["exchange", "market"])
OB_MONITORED = Gauge("cexv2_orderbook_monitored_symbols", "symbols subscribed", ["exchange", "market"])
OB_RECONNECTS = Counter("cexv2_orderbook_reconnects_total", "websocket reconnects", ["exchange", "market"])
OB_CONN_ERRORS = Counter("cexv2_orderbook_conn_errors_total", "websocket connection errors", ["exchange", "market"])
OB_BACKPRESSURE = Gauge("cexv2_orderbook_backpressured", "1 if the last flush failed", ["exchange", "market"])
OB_GAPS = Counter("cexv2_orderbook_gaps_total", "in-stream sequence gaps -> forced resync", ["exchange", "market"])

_FETCH_BUCKETS = (.05, .1, .25, .5, 1.0, 2.0, 5.0, 10.0)
MD_UPDATES = Counter("cexv2_marketdata_updates_total", "update cycles", ["exchange", "market", "result"])
MD_FETCH = Histogram("cexv2_marketdata_fetch_seconds", "REST fetch latency",
                     ["exchange", "market"], buckets=_FETCH_BUCKETS)
MD_STORE = Histogram("cexv2_marketdata_store_seconds", "redis store latency", ["exchange", "market"])
MD_SYMBOLS = Gauge("cexv2_marketdata_symbols", "symbols written last cycle", ["exchange", "market"])


def start_metrics_server(port: int, enabled: bool = True, addr: str = "127.0.0.1") -> bool:
    if not enabled or not HAVE_PROM:
        log.info("metrics disabled (enabled=%s prometheus=%s)", enabled, HAVE_PROM)
        return False

    try:
        start_http_server(port, addr=addr)
        log.info("metrics serving on %s:%d /metrics", addr, port)
        return True
    except Exception as e:
        log.error("metrics server bind FAILED on %s:%d (%s) — port likely in use by another "
                  "supervisor; this process runs WITHOUT metrics", addr, port, e)
        return False
