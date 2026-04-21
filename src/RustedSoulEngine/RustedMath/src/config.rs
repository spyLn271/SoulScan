pub const MARKET_METADATA_KEYS: [&str; 4] = [
    "snapshot:metadata:meteora:dlmm",
    "snapshot:metadata:orca:clmm",
    "snapshot:metadata:raydium:clmm",
    "snapshot:metadata:raydium:amm"
];

pub const MARKET_STATE_KEYS: [&str; 4] = [
    "snapshot:state:meteora:dlmm",
    "snapshot:state:orca:clmm",
    "snapshot:state:raydium:clmm",
    "snapshot:state:raydium:amm"
];

pub const SWAP_SUPPORTED_MARKETS: [(&str, &str); 4] = [
    ("meteora", "dlmm"),
    ("orca", "clmm"),
    ("raydium", "clmm"),
    ("raydium", "amm"),
];

pub const COLD_PATH_KEY: &str = "snapshot:cold_path";

pub const DECAY_PERIOD_COLD_PATH: u64 = 300; // 5 mins