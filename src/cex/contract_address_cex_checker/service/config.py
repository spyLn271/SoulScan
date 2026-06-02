"""
Centralized configuration for all exchange-specific settings.
API keys, rate limits, wait times, base URLs, etc.

All environment-sourced values come from the typed `src.settings.cex_config`
settings object (no scattered os.getenv here).
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum

from src.settings.cex_config import get_cex_config

_cfg = get_cex_config()


class FetchStrategy(Enum):
    BULK = "bulk"           # Single API call returns all data
    SEQUENTIAL = "sequential"  # Need to iterate per-token


@dataclass
class ExchangeConfig:
    """Configuration for a single exchange."""
    name: str
    base_url: str

    # Auth credentials (None if public API)
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    passphrase: Optional[str] = None  # OKX only

    # Rate limiting
    request_delay: float = 0.0         # Delay between requests (seconds)
    rate_limit_wait: float = 20.0      # Wait time on 429 response
    timeout: int = 30                   # Request timeout

    # Fetch behavior
    fetch_strategy: FetchStrategy = FetchStrategy.BULK
    requires_auth: bool = False

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 5.0


# Exchange configurations
EXCHANGE_CONFIGS: dict[str, ExchangeConfig] = {
    "binance": ExchangeConfig(
        name="binance",
        base_url="https://api.binance.com",
        api_key=_cfg.BINANCE_API_KEY,
        secret_key=_cfg.BINANCE_SECRET_KEY,
        requires_auth=True,
        fetch_strategy=FetchStrategy.BULK,
    ),

    "bybit": ExchangeConfig(
        name="bybit",
        base_url="https://api.bybit.com",
        api_key=_cfg.BYBIT_API_KEY,
        secret_key=_cfg.BYBIT_SECRET_KEY,
        requires_auth=True,
        fetch_strategy=FetchStrategy.BULK,
    ),

    "okx": ExchangeConfig(
        name="okx",
        base_url="https://www.okx.com",
        api_key=_cfg.OKX_API_KEY,
        secret_key=_cfg.OKX_SECRET_KEY,
        passphrase=_cfg.OKX_PASSPHRASE,
        requires_auth=True,
        fetch_strategy=FetchStrategy.SEQUENTIAL,
        request_delay=1.0,        # 1 second between requests
        rate_limit_wait=20.0,     # 20 seconds on 429
    ),

    "mexc": ExchangeConfig(
        name="mexc",
        base_url="https://api.mexc.com",
        api_key=_cfg.MEXC_API_KEY,
        secret_key=_cfg.MEXC_SECRET_KEY,
        requires_auth=True,
        fetch_strategy=FetchStrategy.BULK,
    ),

    "bingx": ExchangeConfig(
        name="bingx",
        base_url="https://open-api.bingx.com",
        api_key=_cfg.BINGX_API_KEY,
        secret_key=_cfg.BINGX_SECRET_KEY,
        requires_auth=True,
        fetch_strategy=FetchStrategy.BULK,
    ),

    "coinex": ExchangeConfig(
        name="coinex",
        base_url="https://api.coinex.com/v2",
        api_key=_cfg.COINEX_API_KEY,
        secret_key=_cfg.COINEX_SECRET_KEY,
        requires_auth=False,  # Public endpoint works
        fetch_strategy=FetchStrategy.BULK,
    ),

    "kucoin": ExchangeConfig(
        name="kucoin",
        base_url="https://api.kucoin.com",
        requires_auth=False,
        fetch_strategy=FetchStrategy.BULK,
    ),

    "bitget": ExchangeConfig(
        name="bitget",
        base_url="https://api.bitget.com",
        requires_auth=False,
        fetch_strategy=FetchStrategy.BULK,
    ),

    "htx": ExchangeConfig(
        name="htx",
        base_url="https://api.huobi.pro",
        requires_auth=False,
        fetch_strategy=FetchStrategy.BULK,
        timeout=15,
    ),

    "gateio": ExchangeConfig(
        name="gateio",
        base_url="https://api.gateio.ws/api/v4",
        requires_auth=False,
        fetch_strategy=FetchStrategy.SEQUENTIAL,
        request_delay=0.1,        # 100ms between requests
        rate_limit_wait=20.0,
    ),
}


# Redis configuration
@dataclass
class RedisConfig:
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None

    # Key patterns
    exchange_data_key: str = "cex:data:{exchange}"
    contract_index_key: str = "cex:contract_index"
    last_update_key: str = "cex:last_update:{exchange}"

    def __post_init__(self):
        self.host = _cfg.REDIS.HOST
        self.port = _cfg.REDIS.PORT
        self.db = _cfg.REDIS_DB
        self.password = _cfg.REDIS_PASSWORD


REDIS_CONFIG = RedisConfig()

# Update interval in seconds (20 minutes)
UPDATE_INTERVAL_SECONDS = _cfg.UPDATE_INTERVAL


def validate_exchange_credentials() -> None:
    """Fail-fast: raise if any auth-required exchange is missing its credentials.

    Call this from the worker entrypoint (e.g. UpdaterService.__init__) so a
    misconfigured deploy fails loudly and is restarted by the supervisor, rather
    than silently fetching nothing.
    """
    missing = []
    for name, ec in EXCHANGE_CONFIGS.items():
        if not ec.requires_auth:
            continue
        if not ec.api_key or not ec.secret_key:
            missing.append(name)
        if name == "okx" and not ec.passphrase:
            missing.append("okx:passphrase")
    if missing:
        raise RuntimeError(
            "Missing required CEX API credentials in environment: "
            + ", ".join(sorted(set(missing)))
            + ". Set them as env vars (see .env.example); no hardcoded fallbacks remain."
        )
