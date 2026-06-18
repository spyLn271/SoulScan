#!/usr/bin/env python3
"""
Typed, validated cex_v2 runtime settings (pydantic-settings) — the single source for cex_v2's own
env-sourced knobs, so there is NO raw os.environ parsing anywhere in cex_v2. Every field maps to a
CEX_V2_* variable read from the environment or .env (e.g. log_dir -> CEX_V2_LOG_DIR).

Shared redis / exchange-credential settings still come from src.settings.cex_config (also
pydantic-settings); this model only owns cex_v2-specific runtime configuration.
"""
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]


class Cexv2Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CEX_V2_", env_file=str(_REPO_ROOT / ".env"),  # repo-root .env (CWD-independent)
        env_file_encoding="utf-8", extra="ignore",
    )

    # --- centralized logging (see observability/logging_setup.py) ---
    log_dir: Path = _REPO_ROOT / "logs" / "cex_v2"   # CEX_V2_LOG_DIR
    log_level: str = "INFO"                           # CEX_V2_LOG_LEVEL
    log_json: bool = True                             # CEX_V2_LOG_JSON   (structured JSON lines)
    console_log: bool = False                         # CEX_V2_CONSOLE_LOG (stderr echo; off => no tmux spam)
    log_max_bytes: int = 100 * 1024 * 1024            # CEX_V2_LOG_MAX_BYTES (rotate at 100MB)
    log_backups: int = 10                             # CEX_V2_LOG_BACKUPS  (rotations to keep)
    perf_interval: float = 30.0                       # CEX_V2_PERF_INTERVAL (perf snapshot cadence, s)

    # --- prometheus metrics (/metrics per process; see observability/metrics.py) ---
    metrics_enabled: bool = True                      # CEX_V2_METRICS_ENABLED
    metrics_port_base: int = 9400                     # CEX_V2_METRICS_PORT_BASE (ob workers base+1.., md base+500)
    metrics_bind_host: str = "127.0.0.1"              # CEX_V2_METRICS_BIND_HOST (localhost: not public by default)

    @field_validator("log_level")
    @classmethod
    def _upper(cls, v: str) -> str:
        v = v.upper()
        if v not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ValueError(f"invalid log level: {v}")
        return v

    @field_validator("log_dir", mode="before")
    @classmethod
    def _abs(cls, v):
        p = Path(v)
        return p if p.is_absolute() else (_REPO_ROOT / p)


@lru_cache
def settings() -> Cexv2Settings:
    return Cexv2Settings()
