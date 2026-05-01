pub const MARKET_METADATA_KEYS: [&str; 4] = [
    "snapshot:metadata:solana:meteora:dlmm",
    "snapshot:metadata:solana:orca:clmm",
    "snapshot:metadata:solana:raydium:clmm",
    "snapshot:metadata:solana:raydium:amm"
];

pub const MARKET_STATE_KEYS: [&str; 4] = [
    "snapshot:state:solana:meteora:dlmm",
    "snapshot:state:solana:orca:clmm",
    "snapshot:state:solana:raydium:clmm",
    "snapshot:state:solana:raydium:amm"
];

pub const SWAP_SUPPORTED_MARKETS: [(&str, &str); 4] = [
    ("meteora", "dlmm"),
    ("orca", "clmm"),
    ("raydium", "clmm"),
    ("raydium", "amm"),
];

pub const COLD_PATH_KEY: &str = "snapshot:cold_path";

pub const DECAY_PERIOD_COLD_PATH: u64 = 300; // 5 mins