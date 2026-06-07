use std::collections::BTreeMap;
use serde::Deserialize;

#[derive(Deserialize, Debug, Copy, Clone, PartialEq, Eq, Hash)]
pub struct PoolState {
    pub tick_spacing: u16,
    pub liquidity: u128,
    pub sqrt_price_x64: u128,
    pub tick_current: i32,
}

#[derive(Deserialize, Debug, Copy, Clone, PartialEq, Eq, Hash)]
#[serde(rename_all = "camelCase")]
pub struct TickData {
    pub liquidity_net: i128,
    pub liquidity_gross: u128,
}

#[derive(Deserialize, Debug, Clone, PartialEq, Eq, Hash)]
pub struct RayClmmPool {
    #[serde(rename = "PoolState")]
    pub pool_state: PoolState,

    pub ticks: BTreeMap<i32, TickData>
}


#[derive(Deserialize, Debug, Clone, PartialEq, Eq, Hash)]
pub struct Vault {
    pub mint: String,
    pub amount: u128
}

#[derive(Deserialize, Debug, Clone, PartialEq, Eq, Hash)]
#[serde(rename_all = "camelCase")]
pub struct BaseInfo {
    pub status: u8,
    pub base_vault: String,
    pub quote_vault: String,
    pub base_need_take_pnl: u64,
    pub quote_need_take_pnl: u64
}
#[derive(Deserialize, Debug, Clone, PartialEq, Eq, Hash)]
#[serde(rename_all = "camelCase")]
pub struct RayAmmPool {
    pub base_vault: Vault,
    pub quote_vault: Vault,

    #[serde(rename = "BaseInfo")]
    pub base_info: BaseInfo
}