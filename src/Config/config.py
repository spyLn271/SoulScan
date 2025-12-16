import os
from pathlib import Path
import pydantic
import time

SOLANA_RPC_ENDPOINT = "https://solana-mainnet.core.chainstack.com/d70aa036553f9b407feda39c2d88a5f0"

REDIS_HOST = "localhost"
REDIS_PORT = 6379

REDIS_METADATA_KEY = 'snapshot:metadata:%s:%s'  # market and version
POOLS_CURRENT_STATE_DICT_REDIS_KEY = 'snapshot:state:%s:%s'  # market and version
REDIS_KEY_COLD_PATH = "snapshot:cold_path"

BASE_DIR = Path(__file__).resolve().parent
LOG_MAIN_FOLDER = ''

for file in BASE_DIR.parts:
    LOG_MAIN_FOLDER = os.path.join(LOG_MAIN_FOLDER, file)
    if file == "SoulScan":
        LOG_MAIN_FOLDER = os.path.join(LOG_MAIN_FOLDER, "LogFolder/")
        break

ORCA_CLMM_PROGRAM_ID = 'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc'
METEORA_DLMM_PROGRAM_ID = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
MAX_BIN_PER_ARRAY_DLMM = 70
TICK_ARRAY_SIZE_ORCA_CLMM = 88
TICK_ARRAY_SIZE_RAYDIUM_CLMM = 60

RAYDIUM_CLMM_PROGRAM_ID = 'CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK'


MIN_VOL24 = 30_000
MIN_TVL = 10_000
POOL_STATE_DECAY_TIME = 5  # 5 seconds

MARKETS = {
    "meteora_dlmm": {"market": "meteora", "version": "dlmm"},
    "meteora_dammV2": {"market": "meteora", "version": "dammV2"},
    "orca_clmm": {"market": "orca", "version": "clmm"},
    "raydium_clmm": {"market": "raydium", "version": "clmm"},
    "raydium_amm": {"market": "raydium", "version": "amm"},
}
ACTIVE_MARKETS = ['meteora_dlmm', 'orca_clmm', 'raydium_clmm', 'raydium_amm']

SIGNAL_STREAM_REDIS_KEY = 'saniya'
MINIMAL_PROFIT = 100
SWAPPER_FEE = 0.005  # 0.5 %

class SignalFormat(pydantic.BaseModel):
    dex: str
    network: str
    cex: str
    mode: str
    token_pair: str
    profit: float | int
    target_token: str
    target_address: str
    base_address: str
    base_token: str
    CEX_amountIn: float | int
    CEX_amountOut: float | int
    DEX_amountIn: float | int
    DEX_amountOut: float | int
    order_number: int
    CEX_start_price: float | int
    CEX_end_price: float | int
    timestamp: float = pydantic.Field(default_factory=time.time)