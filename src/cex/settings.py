from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]


class CexV2Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CEX_V2_",
        env_file=str(_REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    log_dir: Path = _REPO_ROOT / "logs" / "cex_v2"
    log_level: str = "INFO"
    log_json: bool = True
    console_log: bool = False
    log_max_bytes: int = 100 * 1024 * 1024
    log_backups: int = 10
    perf_interval: float = 30.0

    metrics_enabled: bool = True
    metrics_port_base: int = 9400
    metrics_bind_host: str = "127.0.0.1"

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
def settings() -> CexV2Settings:
    return CexV2Settings()