"""cex_v2 observability: centralized structured logging + performance metrics."""
from src.cex_v2.observability.logging_setup import setup_logging, emit_perf, file_name

__all__ = ["setup_logging", "emit_perf", "file_name"]
