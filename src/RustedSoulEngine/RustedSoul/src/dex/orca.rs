use std::collections::HashMap;
use serde::Deserialize;

#[derive(Copy, Clone, Debug)]
#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AdaptiveFeeConstants {
    pub filter_period: u16,
    pub decay_period: u16,
    pub reduction_factor: u16,
    pub adaptive_fee_control_factor: u32,
    pub max_volatility_accumulator: u32,
    pub tick_group_size: u16,
    pub major_swap_threshold_ticks: u16
}

#[derive(Copy, Clone, Debug)]
#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AdaptiveFeeVariables {
    pub last_reference_update_timestamp: u64,
    pub last_major_swap_timestamp: u64,
    pub volatility_reference: u32,
    pub tick_group_index_reference: i32,
    pub volatility_accumulator: u32,
}

#[derive(Deserialize, Debug, Clone)]
#[serde(rename_all = "camelCase")]
pub struct Oracle {
    pub adaptive_fee_constants: AdaptiveFeeConstants,
    pub adaptive_fee_variables: AdaptiveFeeVariables
}

#[derive(Deserialize, Debug, Copy, Clone)]
#[serde(rename_all = "camelCase")]
pub struct BaseInfo {
    pub tick_spacing: u16,
    pub fee_rate: u16,
    pub liquidity: u128,
    pub sqrt_price: u128,
    pub tick_current_index: i32,
    pub reward_last_updated_timestamp: u64,

    // P.S for SmartRouter V2
    #[serde(default)]
    pub crossed_tick_groups: u16,
}

#[derive(Deserialize, Debug, Copy, Clone)]
#[serde(rename_all = "camelCase")]
pub struct TickData {
    pub liquidity_net: i128,
    pub liquidity_gross: u128,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Whirlpool {
    pub base_info: BaseInfo,
    pub ticks: HashMap<i32, TickData>,
    pub oracle: Option<Oracle>,
}