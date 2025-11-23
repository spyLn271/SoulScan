SOLANA_RPC_ENDPOINT = "https://solana-mainnet.core.chainstack.com/d70aa036553f9b407feda39c2d88a5f0"

REDIS_HOST = "localhost"
REDIS_PORT = 6379

REDIS_METADATA_KEY = 'snapshot:metadata:%s:%s'  # market and version
POOLS_CURRENT_STATE_DICT_REDIS_KEY = 'snapshot:state:%s:%s'  # market and version

LOG_MAIN_FOLDER = 'LogFolder/'

ORCA_CLMM_PROGRAM_ID = 'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc'
METEORA_DLMM_PROGRAM_ID = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
MAX_BIN_PER_ARRAY_DLMM = 70
TICK_ARRAY_SIZE_ORCA_CLMM = 88
TICK_ARRAY_SIZE_RAYDIUM_CLMM = 60

RAYDIUM_CLMM_PROGRAM_ID = 'CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK'


JUPITER_PLATFORM_FEE = 0.001
MIN_VOL24 = 30_000
MIN_TVL = 10_000

MARKETS = {
    "meteora_dlmm": {"market": "meteora", "version": "dlmm"},
    "meteora_dammV2": {"market": "meteora", "version": "dammV2"},
    "orca_clmm": {"market": "orca", "version": "clmm"},
    "raydium_clmm": {"market": "raydium", "version": "clmm"},
    "raydium_amm": {"market": "raydium", "version": "amm"},
}
ACTIVE_MARKETS = ['meteora_dlmm', 'orca_clmm', 'raydium_clmm', 'raydium_amm']