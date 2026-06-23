use std::collections::HashMap;
use std::sync::LazyLock;


pub static SUPPORTED_NETWORK_LIST: [&str; 5] = [
    "eth",
    "base",
    "arbitrum",
    "bsc",
    "solana"
];

pub static INTERMEDIATE_BASES: LazyLock<HashMap<&'static str, Vec<&'static str>>> = LazyLock::new(|| {
    HashMap::from([
        (
            "solana",
            vec![
                "So11111111111111111111111111111111111111112",
                "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
                "cbbtcf3aa214zXHbiAZQwf4122FBYbraNdFqgw4iMij",
                "USD1ttGY1N17NEEHLmELoaybftRBUSErhqYiQzvEmuB"
            ]
        ),
        (
            "eth",
            vec![
                "0x0000000000000000000000000000000000000000",
                "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                "0xdac17f958d2ee523a2206206994597c13d831ec7",
                "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
                "0x6b175474e89094c44da98b954eedeac495271d0f",
            ]
        ),
        (
            "base",
            vec![
                "0x0000000000000000000000000000000000000000",
                "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
                "0xfde4c96c8593536e31f229ea8f37b2ada2699bb2",
                "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf",
                "0x50c5725949a6f0c72e6c4a641f24049a917db0cb",
            ]
        ),
        (
            "arbitrum",
            vec![
                "0x0000000000000000000000000000000000000000",
                "0xaf88d065e77c8cc2239327c5edb3a432268e5831",
                "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9",
                "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f",
                "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1",
            ]
        ),
        (
            "bsc",
            vec![
                "0x0000000000000000000000000000000000000000",
                "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d",
                "0x55d398326f99059ff775485246999027b3197955",
                "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c",
                "0x1af3f329e8be154074d8769d1ffa4ee058b1dbc3",
                "0x2170ed0880ac9a755fd29b2688956bd959f933f8",
            ]
        ),
    ])
});