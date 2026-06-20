#!/usr/bin/env python3
"""
Centralized, production-grade logging for cex_v2.

One call — setup_logging(component, exchange, market, worker_id) — configures THIS process:
  - a structured **JSON** rotating file in the single central dir (config.LOGGING["dir"]);
  - an opt-in human console (off by default — no tmux flooding, the kucoin lesson);
  - a dedicated **performance** log (perf_<name>.log) fed by emit_perf();
  - noisy third-party loggers (websockets/asyncio/urllib3/redis/requests) pinned to WARNING.

Every process owns its own files (no cross-process file contention / rotation races):
  supervisor.log | orderbook_<ex>_<mt>[_w<n>].log | marketdata.log   (+ perf_<same>.log)

Records carry structured context (component/exchange/market/worker/pid/host) for ingestion
(grep/jq/Loki/ELK). Idempotent: safe to call once per process; re-calling won't leak handlers.
"""
import logging
import logging.handlers
import os
import socket
import sys
import time

from src.cex.config import LOGGING
from src.cex.core.jsonio import dumps as _dumps

_HANDLER_TAG = "_cexv2_managed"          # marks handlers we own (for idempotent re-setup)
_CONTEXT = {"pid": os.getpid(), "host": socket.gethostname()}
_PERF: logging.Logger = None
_NOISY = ("websockets", "websockets.client", "websockets.server",
          "asyncio", "urllib3", "redis", "requests")


def _iso(epoch: float) -> str:
    """Millisecond UTC ISO-8601 (sortable, ingestion-friendly)."""
    ms = int((epoch - int(epoch)) * 1000)
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(epoch)) + f".{ms:03d}Z"


class _ContextFilter(logging.Filter):
    """Stamp every record with the process-wide context."""
    def filter(self, record):
        for k, v in _CONTEXT.items():
            setattr(record, k, v)
        return True


class JsonFormatter(logging.Formatter):
    _CTX = ("component", "exchange", "market", "worker", "pid", "host")

    def format(self, record):
        rec = {
            "ts": _iso(record.created),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }
        for k in self._CTX:
            v = getattr(record, k, None)
            if v is not None:
                rec[k] = v
        if record.exc_info:
            rec["exc"] = self.formatException(record.exc_info)
        return _dumps(rec)


class TextFormatter(logging.Formatter):
    def __init__(self):
        super().__init__("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s", datefmt="%H:%M:%S")


def _rotating(path: str, formatter: logging.Formatter) -> logging.Handler:
    h = logging.handlers.RotatingFileHandler(
        path, maxBytes=LOGGING["max_bytes"], backupCount=LOGGING["backup_count"], encoding="utf-8")
    h.setFormatter(formatter)
    h.addFilter(_ContextFilter())
    setattr(h, _HANDLER_TAG, True)
    return h


def _drop_managed(logger: logging.Logger):
    for h in [h for h in logger.handlers if getattr(h, _HANDLER_TAG, False)]:
        logger.removeHandler(h)
        h.close()


def file_name(component, exchange=None, market=None, worker_id=None) -> str:
    parts = [component] + [x for x in (exchange, market) if x]
    if worker_id is not None:
        parts.append(f"w{worker_id}")
    return "_".join(parts)


def setup_logging(component, exchange=None, market=None, worker_id=None) -> logging.Logger:
    """Configure logging for this process. Returns the perf logger (use emit_perf())."""
    global _PERF
    cfg = LOGGING
    os.makedirs(cfg["dir"], exist_ok=True)
    _CONTEXT.update({"component": component, "exchange": exchange, "market": market,
                     "worker": worker_id, "pid": os.getpid()})
    name = file_name(component, exchange, market, worker_id)
    level = getattr(logging, cfg["level"], logging.INFO)

    # Root gets the file handler (everything propagates up: cexv2.* + third-party warnings).
    root = logging.getLogger()
    _drop_managed(root)
    root.setLevel(level)
    root.addHandler(_rotating(os.path.join(cfg["dir"], f"{name}.log"),
                              JsonFormatter() if cfg["json"] else TextFormatter()))
    if cfg["console"]:
        ch = logging.StreamHandler(sys.stderr)
        ch.setFormatter(TextFormatter())
        ch.addFilter(_ContextFilter())
        setattr(ch, _HANDLER_TAG, True)
        root.addHandler(ch)

    logging.getLogger("cexv2").setLevel(level)
    for noisy in _NOISY:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Perf log: its own file, never mixed into the main log.
    perf = logging.getLogger("cexv2.perf")
    perf.setLevel(logging.INFO)
    perf.propagate = False
    _drop_managed(perf)
    ph = logging.handlers.RotatingFileHandler(
        os.path.join(cfg["dir"], f"perf_{name}.log"),
        maxBytes=cfg["max_bytes"], backupCount=cfg["backup_count"], encoding="utf-8")
    ph.setFormatter(logging.Formatter("%(message)s"))  # message is a pre-serialized JSON line
    setattr(ph, _HANDLER_TAG, True)
    perf.addHandler(ph)
    _PERF = perf

    logging.getLogger("cexv2.observability").info(
        "logging initialized dir=%s file=%s.log json=%s console=%s level=%s",
        cfg["dir"], name, cfg["json"], cfg["console"], cfg["level"])
    return perf


def emit_perf(record: dict) -> None:
    """Write one structured performance record (its own perf_<name>.log). No-op if not set up."""
    if _PERF is None:
        return
    rec = {"ts": _iso(time.time()), "kind": "perf",
           "component": _CONTEXT.get("component"), "pid": _CONTEXT.get("pid")}
    rec.update(record)
    _PERF.info(_dumps(rec))
