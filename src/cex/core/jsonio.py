#!/usr/bin/env python3
"""Fast JSON for cex_v2 — orjson when available (2-5x faster encode on the flush hot path + logging),
stdlib json otherwise. One module so the connector, logging, and market-data all encode identically."""
import json as _json

try:
    import orjson

    HAVE_ORJSON = True

    def dumps(obj) -> str:
        return orjson.dumps(obj).decode()

    def loads(s):
        return orjson.loads(s)
except ImportError:  # graceful fallback — cex_v2 runs without orjson, just slower
    HAVE_ORJSON = False

    def dumps(obj) -> str:
        # no default=str: surface a non-serializable value loudly, same as the orjson path (which
        # raises) — a silent str() coercion would mask a real bug on the no-orjson fallback.
        return _json.dumps(obj, separators=(",", ":"))

    def loads(s):
        return _json.loads(s)
