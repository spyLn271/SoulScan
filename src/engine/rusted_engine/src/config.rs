use std::collections::HashMap;
use std::sync::LazyLock;

pub type Market = str;
pub type Version = str;
pub type Network = str;

pub type QuoteAddress = str;
pub type QuoteSymbol = str;
pub type QuoteDecimals = u32;

pub static SUPPORTED_CEX_LIST: [&str; 12] = [
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

pub static CEX_TAKER_FEE: LazyLock<HashMap<&str, f64>> = LazyLock::new(|| {
    HashMap::from([
        ("binance", 0.001), // https://www.binance.com/en/fee/trading
        ("bybit", 0.001), // https://tradersunion.com/brokers/crypto/view/binance/fees/
        ("okx", 0.001), // https://www.okx.com/fees
        ("mexc", 0.0005), // https://www.mexc.co/learn/article/mexc-spot-trading-fees-maker-taker-rates-calculator/1
        ("bingx", 0.001), // https://bingx.com/en/learn/article/what-are-bingx-spot-trading-fees-for-makers-and-takers
        ("bitget", 0.001), // https://www.bitget.com/fee
        ("bitmart", 0.0025), // https://www.bitmart.com/en-AU/fee in future need to make it adoptive
        ("coinex", 0.002), // https://www.coinex.com/en/fees
        ("htx", 0.002), // https://www.htx.com/fee
        ("lbank", 0.001), // https://www.lbank.com/vip/my-fee-rate
        ("gateio", 0.001), // https://www.gate.com/fee
        ("kucoin", 0.001), // https://www.kucoin.com/ru/support/360015207133
    ])
});

pub static SUPPORTED_NETWORK_LIST: [&Network; 5] = [
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

pub static NETWORK_QUOTES: LazyLock<HashMap<&Network, Vec<(&QuoteSymbol, &QuoteAddress, QuoteDecimals)>>> = LazyLock::new(|| {
    HashMap::from([
        ("eth", vec![
            ("USDT", "0xdac17f958d2ee523a2206206994597c13d831ec7", 6),
            ("USDC", "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", 6),
        ]),
        ("base", vec![
            ("USDT", "0xfde4c96c8593536e31f229ea8f37b2ada2699bb2", 6),
            ("USDC", "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913", 6),
        ]),
        ("arbitrum", vec![
            ("USDT", "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9", 6),
            ("USDC", "0xaf88d065e77c8cc2239327c5edb3a432268e5831", 6),
        ]),
        ("bsc", vec![
            ("USDT", "0x55d398326f99059ff775485246999027b3197955", 18),
            ("USDC", "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d", 18),
        ]),
        ("solana", vec![
            ("USDT", "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB", 6),
            ("USDC", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", 6),
        ]),
    ])
});

pub const POOL_STATE_DECAY: u64 = 10; // 10 seconds
pub const POOL_TICK_DATA_DECAY: u64 = 40; // 40 seconds (used for Uniswap V3/V4)

pub const SWAP_FEE_RATE: f64 = 0.0015; // 0.15% 0x Swap Fee

pub const MIN_PROFIT: f64 = 5.0;

pub const OPPORTUNITY_STREAM: &str = "opportunity";