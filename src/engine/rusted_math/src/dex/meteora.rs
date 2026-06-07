use std::collections::BTreeMap;
use serde::Deserialize;

#[derive(Copy, Clone, Debug, Deserialize, PartialEq, Eq, Hash)]
pub struct ConstantParameters {
    pub base_factor: u16,
    pub filter_period: u16,
    pub decay_period: u16,
    pub reduction_factor: u16,
    pub variable_fee_control: u32,
    pub max_volatility_accumulator: u32,
    pub min_bin_id: i32,
    pub max_bin_id: i32,
    pub protocol_share: u16,
    pub base_fee_power_factor: u8
}

#[derive(Copy, Clone, Debug, Deserialize, PartialEq, Eq, Hash)]
pub struct VariableParameters {
    pub volatility_accumulator: u32,
    pub volatility_reference: u32,
    pub index_reference: i32,
    pub last_update_timestamp: u64,

    // P.S for SmartRouter V2
    #[serde(default)]
    pub crossed_bins: u16
}

#[derive(Deserialize, Clone, Debug, PartialEq, Eq, Hash)]
pub struct LbPair {
    pub parameters: ConstantParameters,
    pub v_parameters: VariableParameters,
    pub active_id: i32,
    pub bin_step: u32,
    pub oracle: String
}

#[derive(Deserialize, Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct Bin {
    pub amount_x: u128,
    pub amount_y: u128,
}

#[derive(Deserialize, Debug, Clone, PartialEq, Eq, Hash)]
pub struct MeteoraDlmmPool {
    #[serde(rename = "LbPair")]
    pub lb_pair: LbPair,

    pub bins: BTreeMap<i32, Bin>
}
