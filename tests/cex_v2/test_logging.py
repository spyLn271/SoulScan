"""Centralized logging + perf: structured JSON files in one dir, context fields, perf log, idempotency."""
import json
import logging

import pytest

from src.cex_v2 import config
from src.cex_v2.observability.logging_setup import setup_logging, emit_perf, file_name, _HANDLER_TAG


@pytest.fixture(autouse=True)
def _isolate(tmp_path):
    """Point logs at a temp dir; tear down managed handlers after each test (no cross-test leak)."""
    config.LOGGING["dir"] = str(tmp_path)
    config.LOGGING["console"] = False
    config.LOGGING["json"] = True
    yield
    for lg in (logging.getLogger(), logging.getLogger("cexv2.perf")):
        for h in [h for h in lg.handlers if getattr(h, _HANDLER_TAG, False)]:
            lg.removeHandler(h); h.close()


def _flush(logger):
    for h in logger.handlers:
        h.flush()


def test_filename_dedicated_per_component():
    assert file_name("supervisor") == "supervisor"
    assert file_name("orderbook", "binance", "spot") == "orderbook_binance_spot"
    assert file_name("orderbook", "binance", "spot", 0) == "orderbook_binance_spot_w0"
    assert file_name("marketdata") == "marketdata"


def test_structured_file_with_context(tmp_path):
    setup_logging("orderbook", "binance", "spot", 0)
    logging.getLogger("cexv2.binance.spot").info("hello %s", "world")
    _flush(logging.getLogger())
    f = tmp_path / "orderbook_binance_spot_w0.log"
    assert f.exists()
    rec = json.loads(f.read_text().strip().splitlines()[-1])
    assert rec["msg"] == "hello world" and rec["level"] == "INFO"
    assert rec["logger"] == "cexv2.binance.spot"
    assert rec["component"] == "orderbook" and rec["exchange"] == "binance"
    assert rec["market"] == "spot" and rec["worker"] == 0 and "pid" in rec and "ts" in rec


def test_perf_log_separate_file(tmp_path):
    setup_logging("marketdata")
    emit_perf({"exchange": "binance", "market": "spot", "msgs_per_s": 123.4, "flush_p99_ms": 2.1})
    _flush(logging.getLogger("cexv2.perf"))
    # perf goes to its OWN file, never the main log
    perf = tmp_path / "perf_marketdata.log"
    main = tmp_path / "marketdata.log"
    rec = json.loads(perf.read_text().strip().splitlines()[-1])
    assert rec["kind"] == "perf" and rec["msgs_per_s"] == 123.4 and rec["exchange"] == "binance"
    main_lines = [l for l in (main.read_text().splitlines() if main.exists() else []) if l.strip()]
    assert not any(json.loads(l).get("kind") == "perf" for l in main_lines)  # perf never in main log


def test_idempotent_no_handler_leak():
    setup_logging("supervisor")
    n1 = len(logging.getLogger().handlers)
    setup_logging("supervisor")
    setup_logging("supervisor")
    n2 = len(logging.getLogger().handlers)
    assert n1 == n2  # re-setup replaces, never accumulates


def test_emit_perf_noop_without_setup():
    # tear down so _PERF-less path is exercised; should not raise
    import src.cex_v2.observability.logging_setup as ls
    ls._PERF = None
    emit_perf({"x": 1})  # no exception
