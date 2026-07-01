pub const SWAP_SUPPORTED_MARKETS: [(&str, &str); 7] = [
    ("meteora", "dlmm"),
    ("orca", "clmm"),
    ("raydium", "clmm"),
    ("raydium", "amm"),
    ("uniswap", "v2"), // and his forks pancakeswap and sushiswap
    ("uniswap", "v3"), // and his forks pancakeswap and sushiswap
    ("uniswap", "v4"),
];

pub const COLD_PATH_KEY: &str = "snapshot:cold_path";

pub const DECAY_PERIOD_COLD_PATH: u64 = 10000000000000; // 15 mins