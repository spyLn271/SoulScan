from pathlib import Path

from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator, Field
from functools import lru_cache


class RedisSettings(BaseSettings):
    HOST: str = "localhost"
    PORT: int = 6379

class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        extra="ignore",
        env_nested_delimiter="__",
    )

    SOLANA_RPC_ENDPOINT: str
    ETHEREUM_RPC_ENDPOINT: str
    BNB_RPC_ENDPOINT: str
    ARB_RPC_ENDPOINT: str
    BASE_RPC_ENDPOINT: str

    COINGECKO_API: str

    REDIS: RedisSettings

    MIN_VOL24: int
    MIN_TVL: int

    METADATA_FETCH_INTERVAL: int

    METADATA_DECAY_PERIOD: int

    EVM_TICKS_FETCH_RANGE: int

    POOL_STATE_DECAY_TIME: int

    MINIMAL_PROFIT: int
    SWAPPER_FEE: float

    OSR_V1_LEVEL_DEPTH: int

    LOG_MAIN_FOLDER: Path = Path("./logs")
    OSR_LOG_FOLDER: Path = Path("osr")
    SCANNER_LOG_FOLDER: Path = Path("scanner")
    DATA_FETCHER_LOG_FOLDER: Path = Path("data-fetcher")
    SUPERVISOR_LOG_FOLDER: Path = Path("supervisor")
    CEX_LOG_FOLDER: Path = Path("cex")
    CEX_MARKET_DATA_LOG_FOLDER: Path = Path("cex-market-data")
    CEX_CONTRACTS_LOG_FOLDER: Path = Path("cex-contracts")

    @model_validator(mode="after")
    def _compose_log_folders(self):
        base = self.LOG_MAIN_FOLDER.resolve()
        base.mkdir(parents=True, exist_ok=True)

        for field in (
                "OSR_LOG_FOLDER",
                "SCANNER_LOG_FOLDER",
                "DATA_FETCHER_LOG_FOLDER",
                "SUPERVISOR_LOG_FOLDER",
                "CEX_LOG_FOLDER",
                "CEX_MARKET_DATA_LOG_FOLDER",
                "CEX_CONTRACTS_LOG_FOLDER",
        ):
            setattr(self, field, (base / getattr(self, field)))
            getattr(self, field).mkdir(parents=True, exist_ok=True)

        self.LOG_MAIN_FOLDER = base

        return self



@lru_cache
def get_config() -> Config:
    return Config()


_config = get_config()


SOLANA_RPC_ENDPOINT = _config.SOLANA_RPC_ENDPOINT
EVM_RPC_ENDPOINT = {
    'base': _config.BASE_RPC_ENDPOINT,
    'eth': _config.ETHEREUM_RPC_ENDPOINT,
    'arbitrum': _config.ARB_RPC_ENDPOINT,
    'bsc': _config.BNB_RPC_ENDPOINT,
}

REDIS_HOST = _config.REDIS.HOST
REDIS_PORT = _config.REDIS.PORT

MIN_VOL24 = _config.MIN_VOL24
MIN_TVL = _config.MIN_TVL

REDIS_METADATA_KEY = 'snapshot:metadata:%s:%s:%s'  # network, market and version
POOLS_STATE_DICT_REDIS_KEY = 'snapshot:state:%s:%s:%s'  # network, market and version
REDIS_KEY_COLD_PATH = "snapshot:cold_path"
REDIS_DEX_MINTS = "snapshot:addresses:%s" # network

ENV_CLMM_SLOT_KEY = "slot"
ENV_CLMM_TICKS_KEY = "ticks"

OSR_LOG_FOLDER = str(_config.OSR_LOG_FOLDER) + "/"
SCANNER_LOG_FOLDER = str(_config.SCANNER_LOG_FOLDER) + "/"
DATA_FETCHER_LOG_FOLDER = str(_config.DATA_FETCHER_LOG_FOLDER) + "/"
SUPERVISOR_LOG_FOLDER = str(_config.SUPERVISOR_LOG_FOLDER) + "/"

# Consolidated data-fetcher log files.
EVM_FETCHER_LOG_FILE = DATA_FETCHER_LOG_FOLDER + "evm.fetcher.log"
EVM_SKELETON_LOG_FILE = DATA_FETCHER_LOG_FOLDER + "evm.skeleton.log"
SOLANA_FETCHER_LOG_FILE = DATA_FETCHER_LOG_FOLDER + "solana.fetcher.log"
METADATA_LOG_FILE = DATA_FETCHER_LOG_FOLDER + "metadata.log"
OSR_LOG_FILES = {
    "eth": OSR_LOG_FOLDER + "eth.osr.log",
    "base": OSR_LOG_FOLDER + "base.osr.log",
    "arbitrum": OSR_LOG_FOLDER + "arbitrum.osr.log",
    "bsc": OSR_LOG_FOLDER + "bsc.osr.log",
    "solana": OSR_LOG_FOLDER + "solana.osr.log",
}

ORCA_CLMM_PROGRAM_ID = 'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc'
METEORA_DLMM_PROGRAM_ID = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
MAX_BIN_PER_ARRAY_DLMM = 70
TICK_ARRAY_SIZE_ORCA_CLMM = 88
TICK_ARRAY_SIZE_RAYDIUM_CLMM = 60

RAYDIUM_CLMM_PROGRAM_ID = 'CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK'

EVM_NATIVE_TOKEN_ADDRESSES = {
    "eth": {
        "symbol": "ETH",
        "address": "0x0000000000000000000000000000000000000000",
        "alias": ["WETH"],
        "alias_addresses": ["0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"],
    },
    "arbitrum": {
        "symbol": "ETH",
        "address": "0x0000000000000000000000000000000000000000",
        "alias": ["WETH"],
        "alias_addresses": ["0x82af49447d8a07e3bd95bd0d56f35241523fbab1"],
    },
    "avax": {
        "symbol": "AVAX",
        "address": "0x0000000000000000000000000000000000000000",
        "alias": ["WAVAX"],
        "alias_addresses": ["0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7"],
    },
    "base": {
        "symbol": "ETH",
        "address": "0x0000000000000000000000000000000000000000",
        "alias": ["WETH"],
        "alias_addresses": ["0x4200000000000000000000000000000000000006"],
    },
    "optimism": {
        "symbol": "ETH",
        "address": "0x0000000000000000000000000000000000000000",
        "alias": ["WETH"],
        "alias_addresses": ["0x4200000000000000000000000000000000000006"],
    },
    "polygon": {
        "symbol": "POL",
        "address": "0x0000000000000000000000000000000000000000",
        "alias": ["WPOL", "WMATIC"],
        "alias_addresses": ["0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270"],
    },
    "bsc": {
        "symbol": "BNB",
        "address": "0x0000000000000000000000000000000000000000",
        "alias": ["WBNB"],
        "alias_addresses": ["0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"],
    },
    "unichain": {
        "symbol": "ETH",
        "address": "0x0000000000000000000000000000000000000000",
        "alias": ["WETH"],
        "alias_addresses": ["0x4200000000000000000000000000000000000006"],
    },
}

MARKETS = {
    # Solana
    "meteora_dlmm": {"market": "meteora", "version": "dlmm", "network": "solana"},
    "meteora_dammV2": {"market": "meteora", "version": "dammV2",  "network": "solana"},
    "orca_clmm": {"market": "orca", "version": "clmm",  "network": "solana"},
    "raydium_clmm": {"market": "raydium", "version": "clmm",  "network": "solana"},
    "raydium_amm": {"market": "raydium", "version": "amm",  "network": "solana"},

    # Ethereum
    "eth_uniswap_v2": {"market": "uniswap", "version": "v2",  "network": "eth"},
    "eth_uniswap_v3": {"market": "uniswap", "version": "v3",  "network": "eth"},
    "eth_uniswap_v4": {"market": "uniswap", "version": "v4",  "network": "eth"},

    # Arbitrum
    "arbitrum_uniswap_v2": {"market": "uniswap", "version": "v2", "network": "arbitrum"},
    "arbitrum_uniswap_v3": {"market": "uniswap", "version": "v3", "network": "arbitrum"},
    "arbitrum_uniswap_v4": {"market": "uniswap", "version": "v4", "network": "arbitrum"},

    # Optimism
    "optimism_uniswap_v2": {"market": "uniswap", "version": "v2", "network": "optimism"},
    "optimism_uniswap_v3": {"market": "uniswap", "version": "v3", "network": "optimism"},
    "optimism_uniswap_v4": {"market": "uniswap", "version": "v4", "network": "optimism"},

    # Base
    "base_uniswap_v2": {"market": "uniswap", "version": "v2", "network": "base"},
    "base_uniswap_v3": {"market": "uniswap", "version": "v3", "network": "base"},
    "base_uniswap_v4": {"market": "uniswap", "version": "v4", "network": "base"},

    # Polygon PoS
    "polygon_uniswap_v2": {"market": "uniswap", "version": "v2", "network": "polygon"},
    "polygon_uniswap_v3": {"market": "uniswap", "version": "v3", "network": "polygon"},
    "polygon_uniswap_v4": {"market": "uniswap", "version": "v4", "network": "polygon"},

    # BNB Chain
    "bsc_uniswap_v2": {"market": "uniswap", "version": "v2", "network": "bsc"},
    "bsc_uniswap_v3": {"market": "uniswap", "version": "v3", "network": "bsc"},
    "bsc_uniswap_v4": {"market": "uniswap", "version": "v4", "network": "bsc"},

    # Avalanche
    "avax_uniswap_v2": {"market": "uniswap", "version": "v2", "network": "avax"},
    "avax_uniswap_v3": {"market": "uniswap", "version": "v3", "network": "avax"},
    "avax_uniswap_v4": {"market": "uniswap", "version": "v4", "network": "avax"},
}

ACTIVE_NETWORK_MARKETS = {
    "solana": ['meteora_dlmm', 'orca_clmm', 'raydium_clmm', 'raydium_amm',],
    "eth": ['eth_uniswap_v2', 'eth_uniswap_v3', 'eth_uniswap_v4',],
    "arbitrum": ['arbitrum_uniswap_v2', 'arbitrum_uniswap_v3', 'arbitrum_uniswap_v4',],
    "base": ['base_uniswap_v2', 'base_uniswap_v3', 'base_uniswap_v4',],
    "bsc": ['bsc_uniswap_v2', 'bsc_uniswap_v3', 'bsc_uniswap_v4',],
}

EVM_NETWORKS = ["eth", "base", "arbitrum", "bsc"]

Network = Literal["eth", "base", "arbitrum", "bsc", "solana"]
DEX = Literal["uniswap", "sushiswap", "pancakeswap"]
Version = Literal["v2", "v3", "v4"]


class CexConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

    REDIS: RedisSettings = Field(default_factory=RedisSettings)
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    LOG_MAIN_FOLDER: Path = Path("./logs")
    CEX_LOG_FOLDER: Path = Path("cex")
    CEX_MARKET_DATA_LOG_FOLDER: Path = Path("cex-market-data")
    CEX_CONTRACTS_LOG_FOLDER: Path = Path("cex-contracts")

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

    UPDATE_INTERVAL: int = 20 * 60  # seconds

    BACKFILL_MIN_WITNESSES: int = 2

    PRICE_MATCH_ENABLED: bool = True
    PRICE_MATCH_MAX_DEVIATION: float = 0.15
    PRICE_MATCH_STREAM_MAX_AGE: int = 300

    CEX_TELEGRAM_BOT_TOKEN: Optional[str] = None
    CEX_TELEGRAM_CHAT_ID: Optional[str] = None

    def model_post_init(self, __context) -> None:
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

REDIS_DB: int = _cex.REDIS_DB
REDIS_PASSWORD: Optional[str] = _cex.REDIS_PASSWORD

CEX_LOG_FOLDER: str = str(_cex.CEX_LOG_FOLDER) + "/"
CEX_MARKET_DATA_LOG_FOLDER: str = str(_cex.CEX_MARKET_DATA_LOG_FOLDER) + "/"
CEX_CONTRACTS_LOG_FOLDER: str = str(_cex.CEX_CONTRACTS_LOG_FOLDER) + "/"

UPDATE_INTERVAL_SECONDS: int = _cex.UPDATE_INTERVAL
BACKFILL_MIN_WITNESSES: int = _cex.BACKFILL_MIN_WITNESSES
PRICE_MATCH_ENABLED: bool = _cex.PRICE_MATCH_ENABLED
PRICE_MATCH_MAX_DEVIATION: float = _cex.PRICE_MATCH_MAX_DEVIATION
PRICE_MATCH_STREAM_MAX_AGE: int = _cex.PRICE_MATCH_STREAM_MAX_AGE