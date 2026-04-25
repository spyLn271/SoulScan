import os
from pathlib import Path
import pydantic
import time

SOLANA_RPC_ENDPOINT = "https://solana-mainnet.g.alchemy.com/v2/ws5O2-Cjjmaf5ulBS5kx2"

REDIS_HOST = "localhost"
REDIS_PORT = 6379

REDIS_METADATA_KEY = 'snapshot:metadata:%s:%s'  # market and version
POOLS_CURRENT_STATE_DICT_REDIS_KEY = 'snapshot:state:%s:%s'  # market and version
REDIS_KEY_COLD_PATH = "snapshot:cold_path"
REDIS_SOLANA_DEX_MINTS = "snapshot:solana_dex_mints"

BASE_DIR = Path(__file__).resolve().parent
LOG_MAIN_FOLDER = ''

for file in BASE_DIR.parts:
    LOG_MAIN_FOLDER = os.path.join(LOG_MAIN_FOLDER, file)
    if file == "SoulScan":
        LOG_MAIN_FOLDER = os.path.join(LOG_MAIN_FOLDER, "LogFolder/")
        break

OSR_LOG_FOLDER = os.path.join(LOG_MAIN_FOLDER, "osr/")
SCANNER_LOG_FOLDER = os.path.join(LOG_MAIN_FOLDER, "scanner/")
DATA_FETCHER_LOG_FOLDER = os.path.join(LOG_MAIN_FOLDER, "data-fetcher/")
SUPERVISOR_LOG_FOLDER = os.path.join(LOG_MAIN_FOLDER, "supervisor/")
CEX_LOG_FOLDER = os.path.join(LOG_MAIN_FOLDER, "cex/")
CEX_MARKET_DATA_LOG_FOLDER = os.path.join(LOG_MAIN_FOLDER, "cex-market-data/")
CEX_CONTRACTS_LOG_FOLDER = os.path.join(LOG_MAIN_FOLDER, "cex-contracts/")

ORCA_CLMM_PROGRAM_ID = 'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc'
METEORA_DLMM_PROGRAM_ID = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
MAX_BIN_PER_ARRAY_DLMM = 70
TICK_ARRAY_SIZE_ORCA_CLMM = 88
TICK_ARRAY_SIZE_RAYDIUM_CLMM = 60

RAYDIUM_CLMM_PROGRAM_ID = 'CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK'


MIN_VOL24 = 30_000
MIN_TVL = 10_000
POOL_STATE_DECAY_TIME = 1000000000000000  # 5 seconds

MARKETS = {
    "meteora_dlmm": {"market": "meteora", "version": "dlmm"},
    "meteora_dammV2": {"market": "meteora", "version": "dammV2"},
    "orca_clmm": {"market": "orca", "version": "clmm"},
    "raydium_clmm": {"market": "raydium", "version": "clmm"},
    "raydium_amm": {"market": "raydium", "version": "amm"},
}
ACTIVE_MARKETS = ['meteora_dlmm', 'orca_clmm', 'raydium_clmm', 'raydium_amm']

MINIMAL_PROFIT = 1
SWAPPER_FEE = 0.005  # 0.5 %