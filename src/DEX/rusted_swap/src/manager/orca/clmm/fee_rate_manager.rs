use crate::manager::errors::SoulManagerError;
use crate::math::orca::clmm::find_tick_group_index;

use serde::Deserialize;

const VOLATILITY_ACCUMULATOR_SCALE_FACTOR: u32 = 10_000;
const ADAPTIVE_FEE_CONTROL_FACTOR_DENOMINATOR: u32 = 100_000;

const REDUCTION_FACTOR_DENOMINATOR: u32 = 10_000;

const MAX_FEE: u32 = 100_000;

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
    pub volatility_accumulator: u32
}

#[derive(Deserialize, Debug)]
#[serde(rename_all = "camelCase")]
pub struct Oracle {
    pub adaptive_fee_constants: AdaptiveFeeConstants,
    pub adaptive_fee_variables: AdaptiveFeeVariables
}

#[derive(Debug)]
pub enum  FeeRateManager {
    Adaptive {
        x_to_y: bool,
        start_tick_group_index: i32,
        static_fee_rate: u16,
        timestamp: u64,
        adaptive_fee_constants: AdaptiveFeeConstants,
        adaptive_fee_variables: AdaptiveFeeVariables
    },
    Static {
        static_fee_rate: u16
    }
}



impl FeeRateManager {
    pub fn new(
        x_to_y: bool,
        current_tick_index: i32,
        timestamp: u64,
        static_fee_rate: u16,
        adaptive_fee_info: &Option<Oracle>
    ) -> Result<Self, SoulManagerError> {
        match adaptive_fee_info {
            None => Ok(Self::Static { static_fee_rate }),
            Some(adaptive_fee_info)=> {
                let start_tick_group_index = find_tick_group_index(
                    current_tick_index,
                    adaptive_fee_info.adaptive_fee_constants.tick_group_size
                )?;

                let adaptive_fee_constants = adaptive_fee_info.adaptive_fee_constants;
                let adaptive_fee_variables = adaptive_fee_info.adaptive_fee_variables;

                Ok(Self::Adaptive {
                    x_to_y,
                    start_tick_group_index,
                    static_fee_rate,
                    timestamp,
                    adaptive_fee_constants,
                    adaptive_fee_variables
                })
            }
        }
    }

    pub fn get_fee_rate(&self, crossed_tick_group: u16) -> u32 {
        match self {
            Self::Static { static_fee_rate } => *static_fee_rate as u32,
            Self::Adaptive {
                x_to_y,
                start_tick_group_index,
                static_fee_rate,
                timestamp,
                adaptive_fee_constants,
                adaptive_fee_variables
            } => {
                let delta_time = (timestamp - adaptive_fee_variables.last_reference_update_timestamp) as u128;
                let filter_period = adaptive_fee_constants.filter_period as u128;
                let decay_period = adaptive_fee_constants.decay_period as u128;

                let v_r = if delta_time < filter_period {
                    adaptive_fee_variables.volatility_reference
                } else if delta_time < decay_period {
                    (adaptive_fee_variables.volatility_accumulator * adaptive_fee_constants.reduction_factor as u32)
                        / REDUCTION_FACTOR_DENOMINATOR
                } else {
                    0
                };

                let tick_group_index_reference = if delta_time < filter_period {
                    adaptive_fee_variables.tick_group_index_reference
                } else {
                    *start_tick_group_index
                };

                let delta_tick_group_index = if *x_to_y {
                    (tick_group_index_reference - (start_tick_group_index - crossed_tick_group as i32))
                        .unsigned_abs()
                } else {
                    (tick_group_index_reference - (start_tick_group_index + crossed_tick_group as i32))
                        .unsigned_abs()
                };

                let v_a = {
                    let v_a_calc = v_r + delta_tick_group_index * VOLATILITY_ACCUMULATOR_SCALE_FACTOR;

                    if v_a_calc > adaptive_fee_constants.max_volatility_accumulator {
                        adaptive_fee_constants.max_volatility_accumulator as u128
                    } else {
                        v_a_calc as u128
                    }
                };


                let a = adaptive_fee_constants.adaptive_fee_control_factor as u128;
                let s = adaptive_fee_constants.tick_group_size as u128;


                let dividend = a * v_a * v_a * s * s;
                let divisor = ADAPTIVE_FEE_CONTROL_FACTOR_DENOMINATOR as u128 *
                    VOLATILITY_ACCUMULATOR_SCALE_FACTOR as u128 *
                    VOLATILITY_ACCUMULATOR_SCALE_FACTOR as u128;

                let quotient = (dividend / divisor) as u32;
                let remainder = dividend % divisor;

                let fee_variable = if remainder == 0 {
                    quotient
                } else {
                    quotient + 1
                };
                let fee_base = *static_fee_rate as u32;

                let total_fee = fee_variable + fee_base;

                if total_fee > MAX_FEE {
                    MAX_FEE
                } else {
                    total_fee
                }
            }
        }
    }
}