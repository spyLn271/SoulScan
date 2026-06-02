"""Centralized, typed configuration for the CEX subsystem.

This is the single source of truth for every environment variable the CEX
producer / market-data / contract-checker code reads. It deliberately holds NO
DEX/engine fields, so a CEX-only deployment needs only CEX + Redis vars in its
`.env` (the shared `src/settings/config.py` still requires the DEX vars and is
used only by the DEX/engine code paths).

Env names follow `.env.example`. Redis uses the nested `REDIS__HOST` / `REDIS__PORT`
form (pydantic `env_nested_delimiter="__"`, matching the existing `config.py`),
while the flat `REDIS_DB` / `REDIS_PASSWORD` and the exchange-credential vars are
read as plain top-level fields.
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class _RedisSettings(BaseSettings):
    # Matches `REDIS__HOST` / `REDIS__PORT` in .env (nested delimiter "__"),
    # same as the shared config.py so a single .env serves both.
    HOST: str = "localhost"
    PORT: int = 6379


class CexConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

    # --- Redis ---
    REDIS: _RedisSettings = Field(default_factory=_RedisSettings)
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # --- CEX log folders (relative names; resolved under LOG_MAIN_FOLDER) ---
    LOG_MAIN_FOLDER: Path = Path("./LogFolder")
    CEX_LOG_FOLDER: Path = Path("cex")
    CEX_MARKET_DATA_LOG_FOLDER: Path = Path("cex-market-data")
    CEX_CONTRACTS_LOG_FOLDER: Path = Path("cex-contracts")

    # --- Contract-address checker: exchange API credentials (None if unset) ---
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_SECRET_KEY: Optional[str] = None
    BYBIT_API_KEY: Optional[str] = None
    BYBIT_SECRET_KEY: Optional[str] = None
    OKX_API_KEY: Optional[str] = None
    OKX_SECRET_KEY: Optional[str] = None
    OKX_PASSPHRASE: Optional[str] = None
    MEXC_API_KEY: Optional[str] = None
    MEXC_SECRET_KEY: Optional[str] = None
    BINGX_API_KEY: Optional[str] = None
    BINGX_SECRET_KEY: Optional[str] = None
    COINEX_API_KEY: Optional[str] = None
    COINEX_SECRET_KEY: Optional[str] = None

    # --- Contract-address checker cadence ---
    UPDATE_INTERVAL: int = 20 * 60  # seconds

    # --- Proxy-rotation Telegram alerts (optional) ---
    CEX_TELEGRAM_BOT_TOKEN: Optional[str] = None
    CEX_TELEGRAM_CHAT_ID: Optional[str] = None

    def model_post_init(self, __context) -> None:
        # Resolve CEX log folders under LOG_MAIN_FOLDER and ensure they exist,
        # mirroring the behaviour of the shared config.py for the CEX dirs only.
        base = self.LOG_MAIN_FOLDER.resolve()
        base.mkdir(parents=True, exist_ok=True)
        for field in ("CEX_LOG_FOLDER", "CEX_MARKET_DATA_LOG_FOLDER", "CEX_CONTRACTS_LOG_FOLDER"):
            resolved = base / getattr(self, field)
            resolved.mkdir(parents=True, exist_ok=True)
            object.__setattr__(self, field, resolved)
        object.__setattr__(self, "LOG_MAIN_FOLDER", base)


@lru_cache
def get_cex_config() -> CexConfig:
    return CexConfig()


_cex = get_cex_config()

# --- Module-level convenience values (mirrors the access style of config.py) ---
REDIS_HOST: str = _cex.REDIS.HOST
REDIS_PORT: int = _cex.REDIS.PORT
REDIS_DB: int = _cex.REDIS_DB
REDIS_PASSWORD: Optional[str] = _cex.REDIS_PASSWORD

# Log folders as trailing-slash strings, matching the existing config.py exports
# that the CEX code already consumes.
CEX_LOG_FOLDER: str = str(_cex.CEX_LOG_FOLDER) + "/"
CEX_MARKET_DATA_LOG_FOLDER: str = str(_cex.CEX_MARKET_DATA_LOG_FOLDER) + "/"
CEX_CONTRACTS_LOG_FOLDER: str = str(_cex.CEX_CONTRACTS_LOG_FOLDER) + "/"

UPDATE_INTERVAL_SECONDS: int = _cex.UPDATE_INTERVAL
