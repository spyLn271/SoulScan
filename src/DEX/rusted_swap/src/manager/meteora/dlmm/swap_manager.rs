use crate::math::meteora::dlmm::calculate_swap;
use crate::manager::meteora::dlmm::fee_rate_manager::*;
use crate::manager::errors::SoulManagerError;

use serde::Deserialize;
use std::collections::HashMap;

#[derive(Deserialize, Clone, Debug)]
pub struct LbPair {
    pub parameters: ConstantParameters,
    pub v_parameters: VariableParameters,
    pub active_id: i32,
    pub bin_step: u32,
    pub oracle: String
}

#[derive(Deserialize, Clone, Copy, Debug)]
pub struct Bin {
    pub amount_x: u128,
    pub amount_y: u128,
}

#[derive(Deserialize, Debug)]
pub struct MeteoraDlmmPool {
    #[serde(rename = "LbPair")]
    pub lb_pair: LbPair,

    pub bins: HashMap<i32, Bin>
}

#[derive(Copy, Clone, Debug)]
pub struct SwapResult {
    pub total_amount_in: u128,
    pub total_amount_out: u128,
    pub total_fee_amount: u128
}

pub fn swap_manager(
    x_to_y: bool,
    amount_specified_is_in: bool,
    delta_amount: u128,
    timestamp: u64,
    meteora_dlmm_pool: &MeteoraDlmmPool
) -> Result<SwapResult, SoulManagerError> {
    let mut result = SwapResult {
        total_amount_in: 0,
        total_amount_out: 0,
        total_fee_amount: 0
    };

    let mut active_bin_id = meteora_dlmm_pool.lb_pair.active_id;
    let mut crossed_bins = 0;

    let fee_rate_manger = FeeRateManager::new(
        meteora_dlmm_pool.lb_pair.parameters,
        meteora_dlmm_pool.lb_pair.v_parameters,
        x_to_y,
        meteora_dlmm_pool.lb_pair.bin_step,
        active_bin_id,
        timestamp
    );

    let mut amount_remaining: i128 = delta_amount
        .try_into()
        .map_err(|_| SoulManagerError::AmountOverflow)?;

    while amount_remaining > 0 {
        let fee_rate = fee_rate_manger.get_fee_rate(crossed_bins);
        let bin = meteora_dlmm_pool.bins
            .get(&active_bin_id)
            .ok_or(SoulManagerError::RunOutOfLiquidity)?;

        let amount_x = bin.amount_x;
        let amount_y = bin.amount_y;

        let swap_within_active_bin = calculate_swap(
            amount_x, amount_y, active_bin_id, meteora_dlmm_pool.lb_pair.bin_step,
            amount_remaining as u128, fee_rate, x_to_y, amount_specified_is_in
        )?;

        result.total_fee_amount += swap_within_active_bin.fee_amount;

        if amount_specified_is_in {
            amount_remaining -= (swap_within_active_bin.amount_in + swap_within_active_bin.fee_amount) as i128;
            result.total_amount_out += swap_within_active_bin.amount_out;
            result.total_amount_in += swap_within_active_bin.amount_in + swap_within_active_bin.fee_amount;
        } else {
            amount_remaining -= swap_within_active_bin.amount_out as i128;
            result.total_amount_out += swap_within_active_bin.amount_out;
            result.total_amount_in += swap_within_active_bin.amount_in + swap_within_active_bin.fee_amount;
        }

        if swap_within_active_bin.is_max {
            if x_to_y {
                active_bin_id -= 1;
            } else {
                active_bin_id += 1;
            }

            crossed_bins += 1;
        }
    }



    Ok(result)
}