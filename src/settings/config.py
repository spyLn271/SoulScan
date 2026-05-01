from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
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

    COINGECKO_API: str

    REDIS: RedisSettings

    MIN_VOL24: int
    MIN_TVL: int

    POOL_STATE_DECAY_TIME: int

    MINIMAL_PROFIT: int
    SWAPPER_FEE: float

    LOG_MAIN_FOLDER: Path = Path("./LogFolder")
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

REDIS_HOST = _config.REDIS.HOST
REDIS_PORT = _config.REDIS.PORT

REDIS_METADATA_KEY = 'snapshot:metadata:%s:%s'  # market and version
POOLS_STATE_DICT_REDIS_KEY = 'snapshot:state:%s:%s'  # market and version
REDIS_KEY_COLD_PATH = "snapshot:cold_path"
REDIS_SOLANA_DEX_MINTS = "snapshot:solana_dex_mints"

OSR_LOG_FOLDER = str(_config.OSR_LOG_FOLDER) + "/"
SCANNER_LOG_FOLDER = str(_config.SCANNER_LOG_FOLDER) + "/"
DATA_FETCHER_LOG_FOLDER = str(_config.DATA_FETCHER_LOG_FOLDER) + "/"
SUPERVISOR_LOG_FOLDER = str(_config.SUPERVISOR_LOG_FOLDER) + "/"
CEX_LOG_FOLDER = str(_config.CEX_LOG_FOLDER) + "/"
CEX_MARKET_DATA_LOG_FOLDER = str(_config.CEX_MARKET_DATA_LOG_FOLDER) + "/"
CEX_CONTRACTS_LOG_FOLDER = str(_config.CEX_CONTRACTS_LOG_FOLDER) + "/"

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

STATE_VIEW_ADDRESS = {
    "uniswap": {
        'base': '0xa3c0c9b65bad0b08107aa264b0f3db444b867a71',
        'eth': '0x7ffe42c4a5deea5b0fec41c94c136cf115597227',
        'arbitrum': '0x76fd297e2d437cd7f76d50f01afe6160f86e9990',
        'avax': '0xc3c9e198c735a4b97e3e683f391ccbdd60b69286',
        'bsc': '0xd13dd3d6e93f276fafc9db9e6bb47c1180aee0c4',
        'polygon': '0x5ea1bd7974c8a611cbab0bdcafcb1d9cc9b3ba5a',
        'optimism': '0xc18a3169788f4f75a170290584eca6395c75ecdb'
    }
}

CHAIN_ID_DICT = {
    'ethereum': 1,
    'arbitrum': 42161,
    'avalanche': 43114,
    'base': 8453,
    'op_mainnet': 10,
    'polygon': 137,
    'bsc': 56,
    'unichain': 130,
}

MARKETS = {
    # Solana
    "meteora_dlmm": {"market": "solana:meteora", "version": "dlmm"},
    "meteora_dammV2": {"market": "solana:meteora", "version": "dammV2"},
    "orca_clmm": {"market": "solana:orca", "version": "clmm"},
    "raydium_clmm": {"market": "solana:raydium", "version": "clmm"},
    "raydium_amm": {"market": "solana:raydium", "version": "amm"},

    # Ethereum
    "eth_uniswap_v2": {"market": "eth:uniswap", "version": "v2"},
    "eth_uniswap_v3": {"market": "eth:uniswap", "version": "v3"},
    "eth_uniswap_v4": {"market": "eth:uniswap", "version": "v4"},
    "eth_pancakeswap_v2": {"market": "eth:pancakeswap", "version": "v2"},
    "eth_pancakeswap_v3": {"market": "eth:pancakeswap", "version": "v3"},
    "eth_sushiswap_v2": {"market": "eth:sushiswap", "version": "v2"},
    "eth_sushiswap_v3": {"market": "eth:sushiswap", "version": "v3"},

    # Arbitrum
    "arbitrum_uniswap_v2": {"market": "arbitrum:uniswap", "version": "v2"},
    "arbitrum_uniswap_v3": {"market": "arbitrum:uniswap", "version": "v3"},
    "arbitrum_uniswap_v4": {"market": "arbitrum:uniswap", "version": "v4"},
    "arbitrum_pancakeswap_v2": {"market": "arbitrum:pancakeswap", "version": "v2"},
    "arbitrum_pancakeswap_v3": {"market": "arbitrum:pancakeswap", "version": "v3"},
    "arbitrum_sushiswap_v2": {"market": "arbitrum:sushiswap", "version": "v2"},
    "arbitrum_sushiswap_v3": {"market": "arbitrum:sushiswap", "version": "v3"},

    # Optimism
    "optimism_uniswap_v2": {"market": "optimism:uniswap", "version": "v2"},
    "optimism_uniswap_v3": {"market": "optimism:uniswap", "version": "v3"},
    "optimism_uniswap_v4": {"market": "optimism:uniswap", "version": "v4"},
    "optimism_sushiswap_v2": {"market": "optimism:sushiswap", "version": "v2"},
    "optimism_sushiswap_v3": {"market": "optimism:sushiswap", "version": "v3"},

    # Base
    "base_uniswap_v2": {"market": "base:uniswap", "version": "v2"},
    "base_uniswap_v3": {"market": "base:uniswap", "version": "v3"},
    "base_uniswap_v4": {"market": "base:uniswap", "version": "v4"},
    "base_pancakeswap_v2": {"market": "base:pancakeswap", "version": "v2"},
    "base_pancakeswap_v3": {"market": "base:pancakeswap", "version": "v3"},
    "base_sushiswap_v2": {"market": "base:sushiswap", "version": "v2"},
    "base_sushiswap_v3": {"market": "base:sushiswap", "version": "v3"},

    # Polygon PoS
    "polygon_uniswap_v2": {"market": "polygon:uniswap", "version": "v2"},
    "polygon_uniswap_v3": {"market": "polygon:uniswap", "version": "v3"},
    "polygon_uniswap_v4": {"market": "polygon:uniswap", "version": "v4"},
    "polygon_sushiswap_v2": {"market": "polygon:sushiswap", "version": "v2"},
    "polygon_sushiswap_v3": {"market": "polygon:sushiswap", "version": "v3"},

    # BNB Chain
    "bsc_uniswap_v2": {"market": "bsc:uniswap", "version": "v2"},
    "bsc_uniswap_v3": {"market": "bsc:uniswap", "version": "v3"},
    "bsc_uniswap_v4": {"market": "bsc:uniswap", "version": "v4"},
    "bsc_pancakeswap_v2": {"market": "bsc:pancakeswap", "version": "v2"},
    "bsc_pancakeswap_v3": {"market": "bsc:pancakeswap", "version": "v3"},
    "bsc_sushiswap_v2": {"market": "bsc:sushiswap", "version": "v2"},
    "bsc_sushiswap_v3": {"market": "bsc:sushiswap", "version": "v3"},

    # Avalanche
    "avax_uniswap_v2": {"market": "avax:uniswap", "version": "v2"},
    "avax_uniswap_v3": {"market": "avax:uniswap", "version": "v3"},
    "avax_uniswap_v4": {"market": "avax:uniswap", "version": "v4"},
    "avax_sushiswap_v2": {"market": "avax:sushiswap", "version": "v2"},
    "avax_sushiswap_v3": {"market": "avax:sushiswap", "version": "v3"},
}
ACTIVE_MARKETS = [
    'meteora_dlmm',
    'orca_clmm',
    'raydium_clmm',
    'raydium_amm',

    "eth_uniswap_v2",
    "eth_uniswap_v3",
    "eth_uniswap_v4",
    "eth_pancakeswap_v2",
    "eth_pancakeswap_v3",
    "eth_sushiswap_v2",
    "eth_sushiswap_v3",

    "arbitrum_uniswap_v2",
    "arbitrum_uniswap_v3",
    "arbitrum_uniswap_v4",
    "arbitrum_pancakeswap_v2",
    "arbitrum_pancakeswap_v3",
    "arbitrum_sushiswap_v2",
    "arbitrum_sushiswap_v3",

    # "optimism_uniswap_v2",
    # "optimism_uniswap_v3",
    # "optimism_uniswap_v4",
    # "optimism_sushiswap_v2",
    # "optimism_sushiswap_v3",

    "base_uniswap_v2",
    "base_uniswap_v3",
    "base_uniswap_v4",
    "base_pancakeswap_v2",
    "base_pancakeswap_v3",
    "base_sushiswap_v2",
    "base_sushiswap_v3",

    # "polygon_uniswap_v2",
    # "polygon_uniswap_v3",
    # "polygon_uniswap_v4",
    # "polygon_sushiswap_v2",
    # "polygon_sushiswap_v3",

    "bsc_uniswap_v2",
    "bsc_uniswap_v3",
    "bsc_uniswap_v4",
    "bsc_pancakeswap_v2",
    "bsc_pancakeswap_v3",
    "bsc_sushiswap_v2",
    "bsc_sushiswap_v3",

    # "avax_uniswap_v2",
    # "avax_uniswap_v3",
    # "avax_uniswap_v4",
    # "avax_sushiswap_v2",
    # "avax_sushiswap_v3",

]

EVM_MARKETS = [
    "eth_uniswap_v2",
    "eth_uniswap_v3",
    "eth_uniswap_v4",
    "eth_pancakeswap_v2",
    "eth_pancakeswap_v3",
    "eth_sushiswap_v2",
    "eth_sushiswap_v3",

    "arbitrum_uniswap_v2",
    "arbitrum_uniswap_v3",
    "arbitrum_uniswap_v4",
    "arbitrum_pancakeswap_v2",
    "arbitrum_pancakeswap_v3",
    "arbitrum_sushiswap_v2",
    "arbitrum_sushiswap_v3",

    "base_uniswap_v2",
    "base_uniswap_v3",
    "base_uniswap_v4",
    "base_pancakeswap_v2",
    "base_pancakeswap_v3",
    "base_sushiswap_v2",
    "base_sushiswap_v3",

    # "polygon_uniswap_v2",
    # "polygon_uniswap_v3",
    # "polygon_uniswap_v4",
    # "polygon_sushiswap_v2",
    # "polygon_sushiswap_v3",

    "bsc_uniswap_v2",
    "bsc_uniswap_v3",
    "bsc_uniswap_v4",
    "bsc_pancakeswap_v2",
    "bsc_pancakeswap_v3",
    "bsc_sushiswap_v2",
    "bsc_sushiswap_v3",

    # "avax_uniswap_v2",
    # "avax_uniswap_v3",
    # "avax_uniswap_v4",
    # "avax_sushiswap_v2",
    # "avax_sushiswap_v3",
]

GECKO_DEX_IDS = {
    "eth": {
        "uniswap": {
            "v2": "uniswap_v2",
            "v3": "uniswap_v3",
            "v4": "uniswap-v4-ethereum",
        },
        "sushiswap": {
            "v2": "sushiswap",
            "v3": "sushiswap-v3-ethereum",
        },
        "pancakeswap": {
            "v2": "pancakeswap_ethereum",
            "v3": "pancakeswap-v3-ethereum",
        },
    },

    "arbitrum": {
        "uniswap": {
            "v2": "uniswap-v2-arbitrum",
            "v3": "uniswap_v3_arbitrum",
            "v4": "uniswap-v4-arbitrum",
        },
        "sushiswap": {
            "v2": "sushiswap_arbitrum",
            "v3": "sushiswap-v3-arbitrum",
        },
        "pancakeswap": {
            "v2": "pancakeswap-v2-arbitrum",
            "v3": "pancakeswap-v3-arbitrum",
        },
    },

    "optimism": {
        "uniswap": {
            "v2": "uniswap-v2-optimism",
            "v3": "uniswap_v3_optimism",
            "v4": "uniswap-v4-optimism",
        },
        "sushiswap": {
            "v2": "sushiswap-v2-optimism",
            "v3": "sushiswap-v3-optimism",
        },
    },

    "base": {
        "uniswap": {
            "v2": "uniswap-v2-base",
            "v3": "uniswap-v3-base",
            "v4": "uniswap-v4-base",
        },
        "sushiswap": {
            "v2": "sushiswap-v2-base",
            "v3": "sushiswap-v3-base",
        },
        "pancakeswap": {
            "v2": "pancakeswap-v2-base",
            "v3": "pancakeswap-v3-base",
        },
    },

    "polygon": {
        "uniswap": {
            "v2": "uniswap-v2-polygon",
            "v3": "uniswap_v3_polygon_pos",
            "v4": "uniswap-v4-polygon",
        },
        "sushiswap": {
            "v2": "sushiswap_polygon_pos",
            "v3": "sushiswap-v3-polygon",
        },
    },

    "bsc": {
        "uniswap": {
            "v2": "uniswap-v2-bsc",
            "v3": "uniswap-bsc",
            "v4": "uniswap-v4-bsc",
        },
        "sushiswap": {
            "v2": "sushiswap_bsc",
            "v3": "sushiswap-v3-bsc",
        },
        "pancakeswap": {
            "v2": "pancakeswap_v2",
            "v3": "pancakeswap-v3-bsc",
        },
    },

    "avax": {
        "uniswap": {
            "v2": "uniswap-v2-avalanche",
            "v3": "uniswap-v3-avalanche",
            "v4": "uniswap-v4-avalanche",
        },
        "sushiswap": {
            "v2": "sushiswap_avalanche",
            "v3": "sushiswap-v3-avalanche",
        },
    },
}


MIN_VOL24 = _config.MIN_VOL24
MIN_TVL = _config.MIN_TVL
POOL_STATE_DECAY_TIME = _config.POOL_STATE_DECAY_TIME

MINIMAL_PROFIT = _config.MINIMAL_PROFIT
SWAPPER_FEE = _config.SWAPPER_FEE