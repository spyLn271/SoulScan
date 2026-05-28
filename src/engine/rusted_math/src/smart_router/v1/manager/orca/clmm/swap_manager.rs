use crate::math::orca::clmm::*;
use crate::smart_router::v1::manager::orca::clmm::fee_rate_manager::*;
use crate::smart_router::manager_errors::SoulManagerError;
use crate::smart_router::v1::manager::common_struct::SwapResult;
use crate::smart_router::common_functions::add_delta_liquidity;
use crate::dex::orca::Whirlpool;


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
        get_lower_tick(current_tick_index, tick_spacing, &current_sqrt_price)
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