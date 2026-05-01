/*
DLMM - Dynamic Liquidity Market Maker

Meteora's DLMM is actually Trader Joe V2.2 with Adaptive Fee Rate.
Price is determined by bin step and active id
    (1 + bin_step / 10_000) ^ active_id

and instead of a curve like in CLMM or AMM, in DLMM swap is executed with a liner function and
price slipage occurs when the price jumps to the next active id.

Main formulas for swaping
price * amount while its product is less than or equal to reserves corresponding token.
Because price is in x term for x->y:

y out =  price * x amount in
( next active id = active id - 1 )
( next bin is full of y token and zero x token )

and for y->x

x out = y amount in / price
( next active id = active id + 1 )
( next bin is full of x token and zero y token )

*/

use crate::math::errors::SoulMathError;
use crate::math::raydium::clmm::FEE_RATE_MUL_VALUE;
use crate::math::u256::*;


pub fn get_price_from_active_id(active_id: i32, bin_step: u32) -> Result<u128, SoulMathError> {
    let mut result: u128 = 1 << 64;
    let ratio = (((10_000 + bin_step) as u128) << 64) / 10_000;
    let mut accumulator: u128 = ratio;
    let mut exp_idx = active_id.abs();
    let mut counter = 1;


    while exp_idx > 0 {
        if exp_idx - counter >= 0 {
            exp_idx -= counter;

            result = {
                let product = mul_q64x64(result, accumulator);
                let integer_part = hi_lo(product.items[3], product.items[2]);
                let fraction_part = hi_lo(product.items[1], product.items[0]);

                let integer_part_u64 = integer_part as u64;
                let fraction_part_u64 = (fraction_part >> 64) as u64;

                hi_lo(integer_part_u64, fraction_part_u64)
            };


            accumulator = {
                let product = mul_q64x64(accumulator, accumulator);
                let integer_part = hi_lo(product.items[3], product.items[2]);
                let fraction_part = hi_lo(product.items[1], product.items[0]);

                let integer_part_u64 = integer_part as u64;
                let fraction_part_u64 = (fraction_part >> 64) as u64;

                hi_lo(integer_part_u64, fraction_part_u64)
            };



            counter *= 2;
        } else {
            counter = 1;
            accumulator = ratio;
        }
    }

    if active_id < 0 {
        let numerator = U256::new(1, 0);
        let denominator = U256::new(0, result);

        let (quotient, _remainder) = numerator.div(&denominator)?;

        result = quotient.try_into_u128()?;
    }

    Ok(result)
}

pub fn get_amount_x(active_price: u128, delta_amount: u128,
                    round_up: bool) -> Result<u128, SoulMathError> {
    let scaled_delta_amount = U256::new(0, delta_amount).shift_left(64);
    let active_price_u256 = U256::new(0, active_price);

    let (quotient, remainder) = scaled_delta_amount.div(&active_price_u256)?;

    let mut amount_x = quotient.try_into_u128()?;

    if round_up && !remainder.is_zero() {
        amount_x += 1;
    }

    Ok(amount_x)
}

pub fn get_amount_y(active_price: u128, delta_amount: u128, round_up: bool) -> u128 {
    let product = mul_q64x64(delta_amount, active_price);

    let mut amount_y = hi_lo(product.items[2], product.items[1]);
    let fraction = product.items[0];

    if round_up && fraction > 0 {
        amount_y += 1
    }

    amount_y
}

#[derive(Copy, Clone, Debug)]
pub struct SwapStepResult {
    pub is_max: bool,      // by is_max is meant that all liquidity from the current price range is used
    pub amount_in: u128,   // pure amount in without any fee regulation
    pub amount_out: u128,
    pub fee_amount: u128,
}

pub fn calculate_swap(x_reserves: u128, y_reserves: u128, active_id: i32, bin_step: u32,
                      delta_amount: u128, fee_rate: u32, x_to_y: bool,
                      amount_specified_is_in: bool) -> Result<SwapStepResult, SoulMathError> {
    let mut result = SwapStepResult {
        is_max: false,
        amount_in: 0,
        amount_out: 0,
        fee_amount: 0
    };

    let active_price = get_price_from_active_id(active_id, bin_step)?;
    let calculate_amount = if amount_specified_is_in {
        calculate_amount_with_fee(delta_amount, fee_rate, true)?
    } else {
        delta_amount
    };

    if (x_to_y && y_reserves == 0) || (!x_to_y && x_reserves == 0) {
        result.is_max = true;
        return Ok(result);
    }

    if x_to_y && amount_specified_is_in {
        let target_amount_y = get_amount_y(active_price, calculate_amount, false);

        if target_amount_y > y_reserves {
            result.is_max = true;
            result.amount_out = y_reserves;
            result.amount_in = get_amount_x(active_price, y_reserves, true)?;

            let total_amount_in = calculate_amount_with_fee(
                result.amount_in,
                fee_rate,
                false
            )?;
            result.fee_amount = total_amount_in - result.amount_in;
        } else {
            result.amount_out = target_amount_y;
            result.amount_in = calculate_amount;
            result.fee_amount = delta_amount - calculate_amount;
        }

    }
    else if x_to_y && !amount_specified_is_in {
        if calculate_amount > y_reserves {
            result.is_max = true;
            result.amount_out = y_reserves;
            result.amount_in = get_amount_x(active_price, y_reserves, true)?;
        } else {
            result.amount_out = calculate_amount;
            result.amount_in = get_amount_x(active_price, calculate_amount, true)?;
        }

        let total_amount_in = calculate_amount_with_fee(
            result.amount_in,
            fee_rate,
            false
        )?;
        result.fee_amount = total_amount_in - result.amount_in;
    }
    else if !x_to_y && amount_specified_is_in {
        let target_amount_x = get_amount_x(active_price, calculate_amount, false)?;

        if target_amount_x > x_reserves {
            result.is_max = true;
            result.amount_out = x_reserves;
            result.amount_in = get_amount_y(active_price, x_reserves, true);

            let total_amount_in = calculate_amount_with_fee(
                result.amount_in,
                fee_rate,
                false
            )?;
            result.fee_amount = total_amount_in - result.amount_in;
        } else {
            result.amount_out = target_amount_x;
            result.amount_in = calculate_amount;
            result.fee_amount = delta_amount - calculate_amount;
        }
    }
    else if !x_to_y && !amount_specified_is_in {
        if calculate_amount > x_reserves {
            result.is_max = true;
            result.amount_out = x_reserves;
            result.amount_in = get_amount_y(active_price, x_reserves, true);
        } else {
            result.amount_out = calculate_amount;
            result.amount_in = get_amount_y(active_price, calculate_amount, true);
        }

        let total_amount_in = calculate_amount_with_fee(
            result.amount_in,
            fee_rate,
            false
        )?;
        result.fee_amount = total_amount_in - result.amount_in;
    }


    Ok(result)
}


fn calculate_amount_with_fee(delta_amount: u128, fee_rate: u32, with_fee: bool) -> Result<u128, SoulMathError> {
    let fee_rate_u256 = {
        let fee_rate_scaled = FEE_RATE_MUL_VALUE - fee_rate as u128;
        U256::new(0, fee_rate_scaled)
    };

    if with_fee {
        let numerator = U256::new(0, delta_amount).mul(&fee_rate_u256)?;
        let denominator = U256::new(0, FEE_RATE_MUL_VALUE);
        let normalized_amount = numerator.div(&denominator)?.0.try_into_u128()?;

        Ok(normalized_amount)
    } else {
        let numerator = U256::new(0, delta_amount)
            .mul(&U256::new(0, FEE_RATE_MUL_VALUE))?;
        let (quotient, remainder) = numerator.div(&fee_rate_u256)?;
        let mut normalized_amount = quotient.try_into_u128()?;

        if !remainder.is_zero() {
            normalized_amount += 1;
        }
        Ok(normalized_amount)
    }
}
