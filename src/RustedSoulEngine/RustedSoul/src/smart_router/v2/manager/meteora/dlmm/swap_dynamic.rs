use std::collections::HashMap;
use crate::math::meteora::dlmm::calculate_swap;
use crate::smart_router::v2::manager::meteora::dlmm::fee_dynamic::*;
use crate::smart_router::manager_errors::SoulManagerError;
use crate::dex::meteora::{MeteoraDlmmPool, Bin};


#[derive(Debug)]
pub struct DynamicMeteoraResult {
    pub total_amount_in: u128,
    pub total_amount_out: u128,
    pub total_fee_amount: u128,
    pub touched_bins: HashMap<i32, Bin>,
    pub new_bin_id: i32,
    pub crossed_bins: u16
}



pub fn swap_manager(
    x_to_y: bool,
    amount_specified_is_in: bool,
    delta_amount: u128,
    timestamp: u64,
    meteora_dlmm_pool: &MeteoraDlmmPool
) -> Result<DynamicMeteoraResult, SoulManagerError> {
    let mut result = DynamicMeteoraResult {
        total_amount_in: 0,
        total_amount_out: 0,
        total_fee_amount: 0,
        touched_bins: HashMap::new(),
        new_bin_id: 0,
        crossed_bins: 0
    };

    let mut active_bin_id = meteora_dlmm_pool.lb_pair.active_id;
    let mut crossed_bins = meteora_dlmm_pool.lb_pair.v_parameters.crossed_bins;

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

        let (new_x_reserves, new_y_reserves) = if x_to_y {
            (amount_x + swap_within_active_bin.amount_in, amount_y - swap_within_active_bin.amount_out)
        } else {
            (amount_x - swap_within_active_bin.amount_out, amount_y + swap_within_active_bin.amount_in)
        };

        result.touched_bins
            .insert(active_bin_id,
                    Bin {
                        amount_x: new_x_reserves,
                        amount_y: new_y_reserves
                    }
        );

        if swap_within_active_bin.is_max {
            if x_to_y {
                active_bin_id -= 1;
            } else {
                active_bin_id += 1;
            }

            crossed_bins += 1;
        }
    }

    result.new_bin_id = active_bin_id;
    result.crossed_bins = crossed_bins;


    Ok(result)
}