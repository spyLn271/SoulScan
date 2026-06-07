use std::collections::HashMap;
use std::sync::LazyLock;

pub type Market = str;
pub type Version = str;
pub type Network = str;

pub const SUPPORTED_CEX_LIST: [&str; 12] = [
    "binance",
    "bybit",
    "okx",
    "mexc",
    "bingx",
    "bitget",
    "bitmart",
    "coinex",
    "htx",
    "lbank",
    "gateio",
    "kucoin"
];

pub const SUPPORTED_NETWORK_LIST: [&Network; 5] = [
    "eth",
    "base",
    "arbitrum",
    "bsc",
    "solana"
];

pub static MARKETS_SUPPORTED_IN_NETWORK: LazyLock<HashMap<&Network, Vec<(&Market, &Version)>>> = LazyLock::new(|| {
    HashMap::from([
        ("eth", vec![("uniswap", "v2"), ("uniswap", "v3"), ("uniswap", "v4")]),
        ("base", vec![("uniswap", "v2"), ("uniswap", "v3"), ("uniswap", "v4")]),
        ("arbitrum", vec![("uniswap", "v2"), ("uniswap", "v3"), ("uniswap", "v4")]),
        ("bsc", vec![("uniswap", "v2"), ("uniswap", "v3"), ("uniswap", "v4")]),
        ("solana", vec![("meteora", "dlmm"), ("orca", "clmm"), ("raydium", "clmm"), ("raydium", "amm")]),
    ])
});

pub const POOL_STATE_DECAY: u64 = 10; // 10 seconds
pub const POOL_TICK_DATA_DECAY: u64 = 40; // 40 seconds (used for Uniswap V3/V4)