use std::collections::BTreeMap;
use serde::{Deserialize, Deserializer};
use serde::de::{Error};
use crate::math::u512::U512;


// Uniswap V3
#[derive(Debug, Deserialize, Copy, Clone, PartialEq, Eq, Hash)]
pub struct Slot0 {
    #[serde(deserialize_with = "deserialize_sqrt_price")]
    pub sqrt_price_x96: U512,

    pub tick_current: i32,

    #[serde(deserialize_with = "deserialize_liquidity")]
    pub liquidity: U512
}

fn deserialize_sqrt_price<'de, D>(deserializer: D) -> Result<U512, D::Error>
where
    D: Deserializer<'de>,
{
    let s: String = String::deserialize(deserializer)?;

    if s.is_empty() {
        return Err(D::Error::custom("empty binary string"));
    }

    if s.len() > 512 {
        return Err(D::Error::custom(format!(
            "binary string too long: {} bits (max 512)",
            s.len()
        )))
    }

    let mut parts = [0u128; 4];

    for (i, chunk) in s.as_bytes().rchunks(128).enumerate() {
        let chunk_str = std::str::from_utf8(chunk)
            .map_err(|_| D::Error::custom("error while bytes -> str"))?;

        parts[i] = u128::from_str_radix(chunk_str, 2)
            .map_err(|_| D::Error::custom("error while str -> u128"))?
    }

    Ok(
        U512::new(
            parts[3], parts[2], parts[1], parts[0]
        )
    )
}

fn deserialize_liquidity<'de, D>(deserializer: D) -> Result<U512, D::Error>
where
    D: Deserializer<'de>
{
    let s: u128 = u128::deserialize(deserializer)?;

    Ok(
        U512::new(
            0, 0, 0, s
        )
    )
}

#[derive(Deserialize, Debug, Copy, Clone, PartialEq, Eq, Hash)]
#[serde(rename_all = "camelCase")]
pub struct TickData {
    pub liquidity_net: i128,
    pub liquidity_gross: u128,
}

// what the functions will work with
#[derive(Debug, Clone)]
pub struct UniswapClmm {
    pub slot0: Slot0,
    pub tick: BTreeMap<i32, TickData>,
}

// how Smart Routers will save it
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct UniswapClmmPools {
    pub slot0s: BTreeMap<String, Slot0>,
    pub ticks: BTreeMap<String, BTreeMap<i32, TickData>>
}


// Uniswap V2
#[derive(Debug, Deserialize, Copy, Clone, PartialEq, Eq, Hash)]
pub struct UniswapAmm {
    pub reserve0: u128,
    pub reserve1: u128
}