use crate::math::orca::clmm::*;
use crate::manager::orca::clmm::fee_rate_manager::*;
use crate::manager::errors::SoulManagerError;

use serde::Deserialize;
use std::collections::HashMap;
use pyo3::prelude::*;

#[derive(Deserialize, Debug, Copy, Clone)]
#[serde(rename_all = "camelCase")]
pub struct BaseInfo {
    pub tick_spacing: u16,
    pub fee_rate: u16,
    pub liquidity: u128,
    pub sqrt_price: u128,
    pub tick_current_index: i32,
    pub reward_last_updated_timestamp: u64,
}

#[derive(Deserialize, Debug, Copy, Clone)]
#[serde(rename_all = "camelCase")]
pub struct TickData {
    pub liquidity_net: i128,
    pub liquidity_gross: u128,
}

#[derive(Deserialize, Debug)]
pub struct Whirlpool {
    pub base_info: BaseInfo,
    pub ticks: HashMap<i32, TickData>,
    pub oracle: Option<Oracle>,
}


#[pyclass]
#[derive(Copy, Clone, Debug)]
pub struct SwapResult {
    #[pyo3(get)]
    pub total_amount_in: u128,

    #[pyo3(get)]
    pub total_amount_out: u128,

    #[pyo3(get)]
    pub total_fee_amount: u128
}

pub fn swap_manager(
    x_to_y: bool,
    amount_specified_is_in: bool,
    delta_amount: u128,
    timestamp: u64,
    whirlpool: &Whirlpool
) -> Result<SwapResult, SoulManagerError> {
    let mut result = SwapResult {
        total_amount_in: 0,
        total_amount_out: 0,
        total_fee_amount: 0
    };
    if amount_specified_is_in {
        result.total_amount_in = delta_amount;
    } else {
        result.total_amount_out = delta_amount;
    }

    let base_info = whirlpool.base_info;
    let mut liquidity = base_info.liquidity;
    let current_tick_index = base_info.tick_current_index;
    let tick_spacing = base_info.tick_spacing as i32;
    let mut current_sqrt_price = base_info.sqrt_price;
    let mut boundary_tick = if x_to_y {
        get_lower_tick(current_tick_index, tick_spacing)
    } else {
        get_upper_tick(current_tick_index, tick_spacing)
    };

    let fee_rate_manager = FeeRateManager::new(
      x_to_y, current_tick_index, timestamp, base_info.fee_rate, &whirlpool.oracle
    )?;
    let mut crossed_tick_groups: u16 = 0;

    let mut amount_remaining: i128 = delta_amount
        .try_into()
        .map_err(|_| SoulManagerError::AmountOverflow)?;


    while amount_remaining > 0 {
        let fee_rate = fee_rate_manager.get_fee_rate(crossed_tick_groups);

        let swap_within_tick_group = calculate_swap(
            current_sqrt_price, boundary_tick, liquidity, amount_remaining as u128,
            fee_rate, x_to_y, amount_specified_is_in
        )?;

        current_sqrt_price = swap_within_tick_group.next_sqrt_price;
        result.total_fee_amount += swap_within_tick_group.fee_amount;
        if amount_specified_is_in {
            amount_remaining -= (swap_within_tick_group.amount_in + swap_within_tick_group.fee_amount) as i128;
            result.total_amount_out += swap_within_tick_group.amount_out;
        } else {
            amount_remaining -= swap_within_tick_group.amount_out as i128;
            result.total_amount_in += swap_within_tick_group.amount_in + swap_within_tick_group.fee_amount;
        }

        if swap_within_tick_group.is_max {
            let tick_data = whirlpool.ticks.get(&boundary_tick);

            match tick_data {
                None => return Err(SoulManagerError::RunOutOfLiquidity),
                Some(tick_data) => {
                    let liquidity_net = tick_data.liquidity_net;

                    if x_to_y {
                        boundary_tick -= tick_spacing;
                        liquidity = add_delta_liquidity(liquidity, -liquidity_net)?;
                    } else {
                        boundary_tick += tick_spacing;
                        liquidity = add_delta_liquidity(liquidity, liquidity_net)?;
                    }

                }
            }


            crossed_tick_groups += 1;
        }

    }

    Ok(result)
}

fn add_delta_liquidity(liquidity: u128, delta_liquidity: i128) -> Result<u128, SoulManagerError> {
    if delta_liquidity == 0 {
        Ok(liquidity)
    } else if delta_liquidity > 0 {
        liquidity
            .checked_add(delta_liquidity as u128)
            .ok_or(SoulManagerError::LiquidityOverflow)
    } else {
        liquidity
            .checked_sub(delta_liquidity.unsigned_abs())
            .ok_or(SoulManagerError::LiquidityUnderflow)
    }
}