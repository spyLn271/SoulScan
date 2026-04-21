/*
CLMM - Concentrated Liquidity Market Maker
Orca's CLMM is actually Uniswap V3, but with small changes.
Orca has Static and Adaptive fee, static fee fully behaves like Uniswap V3, while Adaptive Fee is
Swap Math of Uniswap and Fee Managing is Trader Joe V2.

sqrt_price = sqrt(y / x)
1 / sqrt_price = sqrt(x / y)
L = sqrt(xy)

delta_y = (sqrt_price_end - sqrt_price_start) * L
delta_x = (1 / sqrt_price_end - 1 / sqrt_price_start) * L

if delta_token < 0, then that amount of token is being removed from a pool.
if delta_token > 0, then that amount of token is being added to a pool.
(P.S but functions will always return a positive value)

(P.S this class is pure for math within one single tick range and handle fee itself)

(P.S Orca uses Q64.64 precision)

  Rounding rules

  ┌──────────────────────────────┬──────────────┬─────────────────────────────────┐
  │          Operation           │   Rounding   │              Why                │
  ├──────────────────────────────┼──────────────┼─────────────────────────────────┤
  │ Δtoken_a (exact input)       │ round up     │ take more from user (safe)      │
  ├──────────────────────────────┼──────────────┼─────────────────────────────────┤
  │ Δtoken_a (exact output)      │ round down   │ give less to user (safe)        │
  ├──────────────────────────────┼──────────────┼─────────────────────────────────┤
  │ Δtoken_b (exact input)       │ round up     │ take more from user (safe)      │
  ├──────────────────────────────┼──────────────┼─────────────────────────────────┤
  │ Δtoken_b (exact output)      │ round down   │ give less to user (safe)        │
  ├──────────────────────────────┼──────────────┼─────────────────────────────────┤
  │ next √P from token_a         │ round up     │ don't undershoot the price move │
  ├──────────────────────────────┼──────────────┼─────────────────────────────────┤
  │ next √P from token_b         │ round down   │ don't overshoot the price move  │
  └──────────────────────────────┴──────────────┴─────────────────────────────────┘

*/
use crate::math::u256::{U256, mul_q64x64, hi_lo};
use crate::math::errors::SoulMathError;

pub const MAX_SQRT_PRICE_X64: u128 = 79226673515401279992447579055;
pub const MIN_SQRT_PRICE_X64: u128 = 4295048016;
const LOG_B_2_X32: i128 = 59543866431248i128;
const BIT_PRECISION: u32 = 14;
const LOG_B_P_ERR_MARGIN_LOWER_X64: i128 = 184467440737095516i128;
const LOG_B_P_ERR_MARGIN_UPPER_X64: i128 = 15793534762490258745i128;
pub const FULL_RANGE_ONLY_TICK_SPACING_THRESHOLD: u16 = 32768;
pub const FEE_RATE_MUL_VALUE: u128 = 1_000_000;


pub fn sqrt_price_from_tick_index(tick: i32) -> u128 {
    // this function is from Orca::math::tick_math.rs
    if tick >= 0 {
        let mut ratio: u128 = if tick & 1 != 0 {
            79232123823359799118286999567
        } else {
            79228162514264337593543950336
        };

        if tick & 2 != 0 {
            ratio = mul_shift_96(ratio, 79236085330515764027303304731);
        }
        if tick & 4 != 0 {
            ratio = mul_shift_96(ratio, 79244008939048815603706035061);
        }
        if tick & 8 != 0 {
            ratio = mul_shift_96(ratio, 79259858533276714757314932305);
        }
        if tick & 16 != 0 {
            ratio = mul_shift_96(ratio, 79291567232598584799939703904);
        }
        if tick & 32 != 0 {
            ratio = mul_shift_96(ratio, 79355022692464371645785046466);
        }
        if tick & 64 != 0 {
            ratio = mul_shift_96(ratio, 79482085999252804386437311141);
        }
        if tick & 128 != 0 {
            ratio = mul_shift_96(ratio, 79736823300114093921829183326);
        }
        if tick & 256 != 0 {
            ratio = mul_shift_96(ratio, 80248749790819932309965073892);
        }
        if tick & 512 != 0 {
            ratio = mul_shift_96(ratio, 81282483887344747381513967011);
        }
        if tick & 1024 != 0 {
            ratio = mul_shift_96(ratio, 83390072131320151908154831281);
        }
        if tick & 2048 != 0 {
            ratio = mul_shift_96(ratio, 87770609709833776024991924138);
        }
        if tick & 4096 != 0 {
            ratio = mul_shift_96(ratio, 97234110755111693312479820773);
        }
        if tick & 8192 != 0 {
            ratio = mul_shift_96(ratio, 119332217159966728226237229890);
        }
        if tick & 16384 != 0 {
            ratio = mul_shift_96(ratio, 179736315981702064433883588727);
        }
        if tick & 32768 != 0 {
            ratio = mul_shift_96(ratio, 407748233172238350107850275304);
        }
        if tick & 65536 != 0 {
            ratio = mul_shift_96(ratio, 2098478828474011932436660412517);
        }
        if tick & 131072 != 0 {
            ratio = mul_shift_96(ratio, 55581415166113811149459800483533);
        }
        if tick & 262144 != 0 {
            ratio = mul_shift_96(ratio, 38992368544603139932233054999993551);
        }

        ratio >> 32
    }
    else {
        let abs_tick = tick.abs();

        let mut ratio: u128 = if abs_tick & 1 != 0 {
            18445821805675392311
        } else {
            18446744073709551616
        };

        if abs_tick & 2 != 0 {
            ratio = (ratio * 18444899583751176498) >> 64
        }
        if abs_tick & 4 != 0 {
            ratio = (ratio * 18443055278223354162) >> 64
        }
        if abs_tick & 8 != 0 {
            ratio = (ratio * 18439367220385604838) >> 64
        }
        if abs_tick & 16 != 0 {
            ratio = (ratio * 18431993317065449817) >> 64
        }
        if abs_tick & 32 != 0 {
            ratio = (ratio * 18417254355718160513) >> 64
        }
        if abs_tick & 64 != 0 {
            ratio = (ratio * 18387811781193591352) >> 64
        }
        if abs_tick & 128 != 0 {
            ratio = (ratio * 18329067761203520168) >> 64
        }
        if abs_tick & 256 != 0 {
            ratio = (ratio * 18212142134806087854) >> 64
        }
        if abs_tick & 512 != 0 {
            ratio = (ratio * 17980523815641551639) >> 64
        }
        if abs_tick & 1024 != 0 {
            ratio = (ratio * 17526086738831147013) >> 64
        }
        if abs_tick & 2048 != 0 {
            ratio = (ratio * 16651378430235024244) >> 64
        }
        if abs_tick & 4096 != 0 {
            ratio = (ratio * 15030750278693429944) >> 64
        }
        if abs_tick & 8192 != 0 {
            ratio = (ratio * 12247334978882834399) >> 64
        }
        if abs_tick & 16384 != 0 {
            ratio = (ratio * 8131365268884726200) >> 64
        }
        if abs_tick & 32768 != 0 {
            ratio = (ratio * 3584323654723342297) >> 64
        }
        if abs_tick & 65536 != 0 {
            ratio = (ratio * 696457651847595233) >> 64
        }
        if abs_tick & 131072 != 0 {
            ratio = (ratio * 26294789957452057) >> 64
        }
        if abs_tick & 262144 != 0 {
            ratio = (ratio * 37481735321082) >> 64
        }

        ratio
    }
}

pub fn tick_index_from_sqrt_price(sqrt_price_x64: &u128) -> i32 {
    // this function is from Orca::math::tick_math.rs
    let msb: u32 = 128 - sqrt_price_x64.leading_zeros() - 1;
    let log2p_integer_x32 = (msb as i128 - 64) << 32;

    let mut bit: i128 = 0x8000_0000_0000_0000i128;
    let mut precision = 0;
    let mut log2p_fraction_x64 = 0;

    let mut r = if msb >= 64 {
        sqrt_price_x64 >> (msb - 63)
    } else {
        sqrt_price_x64 << (63 - msb)
    };

    while bit > 0 && precision < BIT_PRECISION {
        r *= r;
        let is_r_more_than_two = r >> 127_u32;
        r >>= 63 + is_r_more_than_two;
        log2p_fraction_x64 += bit * is_r_more_than_two as i128;
        bit >>= 1;
        precision += 1;
    }

    let log2p_fraction_x32 = log2p_fraction_x64 >> 32;
    let log2p_x32 = log2p_integer_x32 + log2p_fraction_x32;

    let logbp_x64 = log2p_x32 * LOG_B_2_X32;

    let tick_low: i32 = ((logbp_x64 - LOG_B_P_ERR_MARGIN_LOWER_X64) >> 64)
        .try_into()
        .unwrap();
    let tick_high: i32 = ((logbp_x64 + LOG_B_P_ERR_MARGIN_UPPER_X64) >> 64)
        .try_into()
        .unwrap();

    if tick_low == tick_high {
        tick_low
    } else {
        let actual_tick_high_sqrt_price_x64: u128 = sqrt_price_from_tick_index(tick_high);
        if actual_tick_high_sqrt_price_x64 <= *sqrt_price_x64 {
            tick_high
        } else {
            tick_low
        }
    }
}

pub fn get_upper_tick(current_tick: i32, tick_spacing: i32) -> i32 {
    let quotient = current_tick / tick_spacing;
    let remainder = current_tick % tick_spacing;

    if current_tick < 0 && remainder != 0 {
        quotient * tick_spacing
    } else {
        (quotient + 1) * tick_spacing
    }

}

pub fn get_lower_tick(current_tick: i32, tick_spacing: i32) -> i32 {
    let quotient = current_tick / tick_spacing;
    let remainder = current_tick % tick_spacing;

    if current_tick < 0 && remainder != 0 {
        (quotient - 1) * tick_spacing
    } else {
        quotient * tick_spacing
    }
}

pub fn find_tick_group_index(current_tick_index: i32, tick_group_size: u16) -> Result<i32, SoulMathError> {
    if tick_group_size == 0 {
        return Err(SoulMathError::CantBeDividedByZero)
    }

    if current_tick_index % tick_group_size as i32 == 0 || current_tick_index >= 0 {
        Ok(current_tick_index / tick_group_size as i32)
    } else {
        Ok(current_tick_index / tick_group_size as i32 - 1)
    }
}

pub fn get_amount_x(sqrt_price0: u128, sqrt_price1: u128, liquidity: u128, round_up: bool) -> u128 {
    let (sqrt_price0, sqrt_price1) = increase_order(sqrt_price0, sqrt_price1);
    let delta_sqrt_price = sqrt_price1 - sqrt_price0;

    let numerator = mul_q64x64(delta_sqrt_price, liquidity).shift_left(64);
    let denominator = mul_q64x64(sqrt_price0, sqrt_price1);
    let (quotient, remainder) = numerator.div(&denominator).unwrap();

    let mut amount_x = quotient.try_into_u128().unwrap();

    if round_up && !remainder.is_zero() {
        amount_x += 1;
    }

    amount_x
}

pub fn get_amount_y(sqrt_price0: u128, sqrt_price1: u128, liquidity: u128, round_up: bool) -> u128 {
    let (sqrt_price0, sqrt_price1) = increase_order(sqrt_price0, sqrt_price1);
    let delta_sqrt_price = sqrt_price1 - sqrt_price0;

    let product = mul_q64x64(delta_sqrt_price, liquidity);
    let mut amount_y = hi_lo(product.items[2], product.items[1]);
    let remainder = product.items[0];

    if round_up && remainder != 0 {
        amount_y += 1
    }

    amount_y
}

pub fn get_sqrt_price_from_x(sqrt_price_start: u128, liquidity: u128, delta_x: u128,
                             amount_specified_is_in: bool,
                             round_up: bool) -> Result<u128, SoulMathError> {
    let scaled_liquidity = U256::new(0, liquidity).shift_left(64);
    let x_part_of_denominator = mul_q64x64(delta_x, sqrt_price_start);

    if !amount_specified_is_in && scaled_liquidity.lte(&x_part_of_denominator) {
        return Err(SoulMathError::InsufficientLiquidity);
    }

    let denominator = if amount_specified_is_in {
        scaled_liquidity.add(&x_part_of_denominator)?
    } else {
        scaled_liquidity.sub(&x_part_of_denominator)?
    };
    let numerator = mul_q64x64(liquidity, sqrt_price_start).shift_left(64);

    let (quotient, remainder) = numerator.div(&denominator)?;
    let mut sqrt_price = quotient.try_into_u128()?;

    if round_up && !remainder.is_zero() {
        sqrt_price += 1
    }

    Ok(sqrt_price)
}

pub fn get_sqrt_price_from_y(sqrt_price_start: u128, liquidity: u128, delta_y: u128,
                             amount_specified_is_in: bool,
                             round_up: bool) -> Result<u128, SoulMathError> {
    let scaled_delta_y = U256::new(0, delta_y).shift_left(64);
    let liquidity_part_numerator = mul_q64x64(liquidity, sqrt_price_start);

    if !amount_specified_is_in && liquidity_part_numerator.lte(&scaled_delta_y) {
        return Err(SoulMathError::InsufficientLiquidity);
    }

    let denominator = U256::new(0, liquidity);
    let numerator = if amount_specified_is_in {
        liquidity_part_numerator.add(&scaled_delta_y)?
    } else {
        liquidity_part_numerator.sub(&scaled_delta_y)?
    };

    let (quotient, remainder) = numerator.div(&denominator)?;
    let mut sqrt_price = quotient.try_into_u128()?;

    if round_up && !remainder.is_zero() {
        sqrt_price += 1
    }

    Ok(sqrt_price)
}


#[derive(Copy, Clone, Debug)]
pub struct SwapStepResult {
    pub is_max: bool,      // by is_max is meant that all liquidity from the current price range is used
    pub amount_in: u128,   // pure amount in without any fee regulation
    pub amount_out: u128,
    pub fee_amount: u128,
    pub next_sqrt_price: u128,
}

pub fn calculate_swap(sqrt_price: u128, boundary_tick: i32, liquidity: u128,
                      delta_amount: u128, fee_rate: u32, x_to_y: bool,
                      amount_specified_is_in: bool) -> Result<SwapStepResult, SoulMathError> {
    let mut result = SwapStepResult {
        is_max: false,
        amount_in: 0,
        amount_out: 0,
        fee_amount: 0,
        next_sqrt_price: sqrt_price,
    };

    let calculate_amount = if amount_specified_is_in {
        calculate_amount_with_fee(delta_amount, fee_rate, true)?
    } else {
        delta_amount
    };
    let boundary_sqrt_price= sqrt_price_from_tick_index(boundary_tick);


    if x_to_y && amount_specified_is_in {
        let target_sqrt_price = get_sqrt_price_from_x(sqrt_price,
                                                      liquidity,
                                                      calculate_amount,
                                                      amount_specified_is_in,
                                                      true)?;

        if target_sqrt_price > boundary_sqrt_price {
            result.next_sqrt_price = target_sqrt_price;
            result.amount_out = get_amount_y(sqrt_price, target_sqrt_price, liquidity, false);
            result.amount_in = calculate_amount;
            result.fee_amount = delta_amount - calculate_amount;

        } else {
            result.is_max = true;
            result.next_sqrt_price = boundary_sqrt_price;
            result.amount_out = get_amount_y(sqrt_price, boundary_sqrt_price, liquidity, false);
            result.amount_in = get_amount_x(sqrt_price, boundary_sqrt_price, liquidity, true);

            let amount_in_without_fee = calculate_amount_with_fee(
                result.amount_in,
                fee_rate,
                false
            )?;
            result.fee_amount = amount_in_without_fee - result.amount_in;
        };

    }
    else if x_to_y && !amount_specified_is_in {
        let target_sqrt_price = get_sqrt_price_from_y(sqrt_price,
                                                      liquidity,
                                                      calculate_amount,
                                                      amount_specified_is_in,
                                                      false)?;

        if target_sqrt_price > boundary_sqrt_price {
            result.next_sqrt_price = target_sqrt_price;
            result.amount_out = calculate_amount;
            result.amount_in = get_amount_x(sqrt_price, target_sqrt_price, liquidity, true);
        } else {
            result.is_max = true;
            result.next_sqrt_price = boundary_sqrt_price;
            result.amount_out = get_amount_y(sqrt_price, boundary_sqrt_price, liquidity, false);
            result.amount_in = get_amount_x(sqrt_price, boundary_sqrt_price, liquidity, true);
        }

        let amount_in_without_fee = calculate_amount_with_fee(
            result.amount_in,
            fee_rate,
            false
        )?;
        result.fee_amount = amount_in_without_fee - result.amount_in;

    }
    else if !x_to_y && amount_specified_is_in {
        let target_sqrt_price = get_sqrt_price_from_y(sqrt_price,
                                                      liquidity,
                                                      calculate_amount,
                                                      amount_specified_is_in,
                                                      false)?;

        if target_sqrt_price < boundary_sqrt_price {
            result.next_sqrt_price = target_sqrt_price;
            result.amount_out = get_amount_x(sqrt_price, target_sqrt_price, liquidity, false);
            result.amount_in = calculate_amount;
            result.fee_amount = delta_amount - calculate_amount;

        } else {
            result.is_max = true;
            result.next_sqrt_price = boundary_sqrt_price;
            result.amount_out = get_amount_x(sqrt_price, boundary_sqrt_price, liquidity, false);
            result.amount_in = get_amount_y(sqrt_price, boundary_sqrt_price, liquidity, true);

            let amount_in_without_fee = calculate_amount_with_fee(
                result.amount_in,
                fee_rate,
                false
            )?;
            result.fee_amount = amount_in_without_fee - result.amount_in;
        }
    }
    else if !x_to_y && !amount_specified_is_in {
        let target_sqrt_price = get_sqrt_price_from_x(sqrt_price,
                                                      liquidity,
                                                      calculate_amount,
                                                      amount_specified_is_in,
                                                      true)?;

        if target_sqrt_price < boundary_sqrt_price {
            result.next_sqrt_price = target_sqrt_price;
            result.amount_out = calculate_amount;
            result.amount_in = get_amount_y(sqrt_price, target_sqrt_price, liquidity, true);
        } else {
            result.is_max = true;
            result.next_sqrt_price = boundary_sqrt_price;
            result.amount_out = get_amount_x(sqrt_price, boundary_sqrt_price, liquidity, false);
            result.amount_in = get_amount_y(sqrt_price, boundary_sqrt_price, liquidity,true);
        }

        let amount_in_without_fee = calculate_amount_with_fee(
            result.amount_in,
            fee_rate,
            false
        )?;
        result.fee_amount = amount_in_without_fee - result.amount_in;
    }


    Ok(result)
}






fn mul_shift_96(n0: u128, n1: u128) -> u128 {
    mul_q64x64(n0, n1).shift_right(96).try_into_u128().unwrap()
}

fn increase_order(a: u128, b: u128) -> (u128, u128) {
    if a < b {
        (a, b)
    } else {
        (b, a)
    }
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