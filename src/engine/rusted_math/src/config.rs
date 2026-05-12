pub const SWAP_SUPPORTED_MARKETS: [(&str, &str); 7] = [
    ("meteora", "dlmm"),
    ("orca", "clmm"),
    ("raydium", "clmm"),
    ("raydium", "amm"),
    ("uniswap", "v2"),
    ("uniswap", "v3"),
    ("uniswap", "v4"),
];

pub const COLD_PATH_KEY: &str = "snapshot:cold_path";

pub const DECAY_PERIOD_COLD_PATH: u64 = 300; // 5 mins