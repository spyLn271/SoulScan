"""
Centralized configuration for all exchange-specific settings.
API keys, rate limits, wait times, base URLs, etc. lol
"""
import os
from dataclasses import dataclass
from typing import Optional
from enum import Enum


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
        api_key=os.getenv("BINANCE_API_KEY", "0Sdsm77CodRIi4Q8YWXPD3ApHgh3KadcRJVEM9uSMJBpbk5IFxgRb8a6HrgBgCKh"),
        secret_key=os.getenv("BINANCE_SECRET_KEY", "iEH9TqBBRcosRw9RijmrtLd7FTScMxeS8ZhyxdF80V7Cy2x9WpynkhVIEg1SzxyY"),
        requires_auth=True,
        fetch_strategy=FetchStrategy.BULK,
    ),

    "bybit": ExchangeConfig(
        name="bybit",
        base_url="https://api.bybit.com",
        api_key=os.getenv("BYBIT_API_KEY", "8ekAOltxIY3RObMROO"),
        secret_key=os.getenv("BYBIT_SECRET_KEY", "UGl4uGHerXIWuTZCXMezNiU5MLSdizKVEyr4"),
        requires_auth=True,
        fetch_strategy=FetchStrategy.BULK,
    ),

    "okx": ExchangeConfig(
        name="okx",
        base_url="https://www.okx.com",
        api_key=os.getenv("OKX_API_KEY", "a02bf8c7-92f6-4f7e-ab89-ed887baee1b1"),
        secret_key=os.getenv("OKX_SECRET_KEY", "0C503A77BFAD53768C83E5B6A82ED22C"),
        passphrase=os.getenv("OKX_PASSPHRASE", "Arbitrage-password-b0t"),
        requires_auth=True,
        fetch_strategy=FetchStrategy.SEQUENTIAL,
        request_delay=1.0,        # 1 second between requests
        rate_limit_wait=20.0,     # 20 seconds on 429
    ),

    "mexc": ExchangeConfig(
        name="mexc",
        base_url="https://api.mexc.com",
        api_key=os.getenv("MEXC_API_KEY", "mx0vglIlkE3kwwQI3a"),
        secret_key=os.getenv("MEXC_SECRET_KEY", "a361d4dea53c4d3f8c563e4c76276ef8"),
        requires_auth=True,
        fetch_strategy=FetchStrategy.BULK,
    ),

    "bingx": ExchangeConfig(
        name="bingx",
        base_url="https://open-api.bingx.com",
        api_key=os.getenv("BINGX_API_KEY", "U2hGqxMmEWVLklrQlMJANKTPwI30tn55uQgvJxSoZPbWJaS0Mu6nJkADVb06IlKnOKlcZeIBm4pXbbUUdLeA"),
        secret_key=os.getenv("BINGX_SECRET_KEY", "ntutN2dkqReuzy3wknyf93aZa6lUrAcjLmU4hEIGeVTBJhnbrZWzYfX6SUNaNWYg9VOBxYZd6lnasViW6wDVQ"),
        requires_auth=True,
        fetch_strategy=FetchStrategy.BULK,
    ),

    "coinex": ExchangeConfig(
        name="coinex",
        base_url="https://api.coinex.com/v2",
        api_key=os.getenv("COINEX_API_KEY", "9A61A81A84654C9CB6C34DD7094AB992"),
        secret_key=os.getenv("COINEX_SECRET_KEY", "3D355B98E840F94AF8BD6557CEDEA18239AA4BAF3B915C50"),
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
        self.host = os.getenv("REDIS_HOST", self.host)
        self.port = int(os.getenv("REDIS_PORT", self.port))
        self.db = int(os.getenv("REDIS_DB", self.db))
        self.password = os.getenv("REDIS_PASSWORD", self.password)


REDIS_CONFIG = RedisConfig()

# Update interval in seconds (20 minutes)
UPDATE_INTERVAL_SECONDS = int(os.getenv("UPDATE_INTERVAL", 20 * 60))
