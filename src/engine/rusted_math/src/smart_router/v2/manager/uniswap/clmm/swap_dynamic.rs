use crate::math::uniswap::clmm::*;
use crate::math::u512::U512;
use crate::smart_router::manager_errors::SoulManagerError;
use crate::dex::uniswap::UniswapClmm;
use crate::dex::metadata::Metadata;

#[derive(Debug)]
pub struct DynamicUniClmmResult {
    pub total_amount_in: u128,
    pub total_amount_out: u128,
    pub total_fee_amount: u128,
    pub new_liquidity: U512,
    pub new_sqrt_price_x96: U512
}


pub fn swap_manager(
    x_to_y: bool,
    amount_specified_is_in: bool,
    delta_amount: u128,
    fee_rate: u32,
    tick_spacing: i32,
    uni_pool: &UniswapClmm,
) -> Result<DynamicUniClmmResult, SoulManagerError> {
    let mut result = DynamicUniClmmResult {
        total_amount_in: 0,
        total_amount_out: 0,
        total_fee_amount: 0,
        new_liquidity: U512::from_u128(0),
        new_sqrt_price_x96: U512::from_u128(0)
    };

    let slot0 = uni_pool.slot0;
    let mut liquidity = slot0.liquidity;
    let mut current_sqrt_price_x96 = slot0.sqrt_price_x96;
    let current_tick_index = slot0.tick_current;


    let mut boundary_tick = if x_to_y {
        get_lower_tick(current_tick_index, tick_spacing, &current_sqrt_price_x96)?
    } else {
        get_upper_tick(current_tick_index, tick_spacing)
    };

    let mut amount_remaining: i128 = delta_amount
        .try_into()
        .map_err(|_| SoulManagerError::AmountOverflow)?;


    while amount_remaining > 0 {
        let swap_within_tick_group = calculate_swap(
            current_sqrt_price_x96,
            boundary_tick,
            liquidity,
            amount_remaining as u128,
            fee_rate,
            x_to_y,
            amount_specified_is_in
        )?;

        current_sqrt_price_x96 = swap_within_tick_group.next_sqrt_price;
        result.total_fee_amount += swap_within_tick_group.fee_amount;
        result.total_amount_in += swap_within_tick_group.amount_in + swap_within_tick_group.fee_amount;
        result.total_amount_out += swap_within_tick_group.amount_out;

        if amount_specified_is_in {
            amount_remaining -= (swap_within_tick_group.amount_in + swap_within_tick_group.fee_amount) as i128;
        } else {
            amount_remaining -= swap_within_tick_group.amount_out as i128;
        }

        if swap_within_tick_group.is_max {
            let tick_data = uni_pool.tick.get(&boundary_tick);

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
        }
    }

    result.new_liquidity = liquidity;
    result.new_sqrt_price_x96= current_sqrt_price_x96;

    Ok(result)
}


fn add_delta_liquidity(liquidity: U512, delta_liquidity: i128) -> Result<U512, SoulManagerError> {
    if delta_liquidity == 0 {
        Ok(liquidity)
    } else if delta_liquidity > 0 {
        Ok(liquidity.add(&U512::from_u128(delta_liquidity as u128))?)
    } else {
        Ok(liquidity.sub(&U512::from_u128(delta_liquidity.unsigned_abs()))?)
    }
}