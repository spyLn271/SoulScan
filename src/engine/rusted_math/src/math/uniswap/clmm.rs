/*
CLMM - Concentrated Liquidity Market Maker

sqrt_price = sqrt(y / x)
1 / sqrt_price = sqrt(x / y)
L = sqrt(xy)

delta_y = (sqrt_price_end - sqrt_price_start) * L
delta_x = (1 / sqrt_price_end - 1 / sqrt_price_start) * L

if delta_token < 0, then that amount of token is being removed from a pool.
if delta_token > 0, then that amount of token is being added to a pool.
(P.S but functions will always return a positive value)

(P.S this class is pure for math within one single tick range and handle fee itself)

(P.S Uniswap uses Q64.96 precision we use Q128.96 internally and it doesnt affect calculations)

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

use crate::math::u512::U512;
use crate::math::errors::SoulMathError;
use crate::math::i256::I256;
use crate::math::u256::U256;

const MAX_U256: U512 = U512 { items: [u64::MAX, u64::MAX, u64::MAX, u64::MAX, 0, 0, 0, 0] };

const MIN_TICK: i32 = -887272;
const MAX_TICK: i32 = 887272;

const MIN_SQRT_RATIO: U512 = U512 { items: [4295128739, 0, 0, 0, 0, 0, 0, 0] };
const MAX_SQRT_RATIO: U512 = U512 { items: [6743328256752651558, 17280870778742802505, 4294805859, 0, 0, 0, 0, 0] };

const BIT_PRECISION: u32 = 14;

pub const FEE_RATE_MUL_VALUE: u128 = 1_000_000;


fn mul_shift_128(a: &U512, b: u128) -> Result<U512, SoulMathError> {
    Ok(
        a.mul(&U512::new(0, 0, 0, b))?
            .shift_right(128)
    )
}

pub fn sqrt_price_from_tick_index(tick: i32) -> Result<U512, SoulMathError> {
    if tick > MAX_TICK || tick < MIN_TICK {
        return Err(SoulMathError::TickIsNotInRange)
    }

    let abs_tick: u32 = tick.unsigned_abs();

    let mut ratio: U512 = if abs_tick & 1 != 0 {
        U512::new(
            0, 0, 0, 340265354078544963557816517032075149313
        )
    } else {
        U512::new(
            0, 0, 1, 0
        )
    };

    if abs_tick & 2 != 0 {
        ratio = mul_shift_128(&ratio, 340248342086729790484326174814286782778)?;
    }
    if abs_tick & 4 != 0 {
        ratio = mul_shift_128(&ratio, 340214320654664324051920982716015181260)?;
    }
    if abs_tick & 8 != 0 {
        ratio = mul_shift_128(&ratio, 340146287995602323631171512101879684304)?;
    }
    if abs_tick & 16 != 0 {
        ratio = mul_shift_128(&ratio, 340010263488231146823593991679159461444)?;
    }
    if abs_tick & 32 != 0 {
        ratio = mul_shift_128(&ratio, 339738377640345403697157401104375502016)?;
    }
    if abs_tick & 64 != 0 {
        ratio = mul_shift_128(&ratio, 339195258003219555707034227454543997025)?;
    }
    if abs_tick & 128 != 0 {
        ratio = mul_shift_128(&ratio, 338111622100601834656805679988414885971)?;
    }
    if abs_tick & 256 != 0 {
        ratio = mul_shift_128(&ratio, 335954724994790223023589805789778977700)?;
    }
    if abs_tick & 512 != 0 {
        ratio = mul_shift_128(&ratio, 331682121138379247127172139078559817300)?;
    }
    if abs_tick & 1024 != 0 {
        ratio = mul_shift_128(&ratio, 323299236684853023288211250268160618739)?;
    }
    if abs_tick & 2048 != 0 {
        ratio = mul_shift_128(&ratio, 307163716377032989948697243942600083929)?;
    }
    if abs_tick & 4096 != 0 {
        ratio = mul_shift_128(&ratio, 277268403626896220162999269216087595045)?;
    }
    if abs_tick & 8192 != 0 {
        ratio = mul_shift_128(&ratio, 225923453940442621947126027127485391333)?;
    }
    if abs_tick & 16384 != 0 {
        ratio = mul_shift_128(&ratio, 149997214084966997727330242082538205943)?;
    }
    if abs_tick & 32768 != 0 {
        ratio = mul_shift_128(&ratio, 66119101136024775622716233608466517926)?;
    }
    if abs_tick & 65536 != 0 {
        ratio = mul_shift_128(&ratio, 12847376061809297530290974190478138313)?;
    }
    if abs_tick & 131072 != 0 {
        ratio = mul_shift_128(&ratio, 485053260817066172746253684029974020)?;
    }
    if abs_tick & 262144 != 0 {
        ratio = mul_shift_128(&ratio, 691415978906521570653435304214168)?;
    }
    if abs_tick & 524288 != 0 {
        ratio = mul_shift_128(&ratio, 1404880482679654955896180642)?;
    }

    if tick > 0 {
        ratio = MAX_U256.div(&ratio)?.0
    }


    // this divides by 1<<32 rounding up to go from a Q128.128 to a Q128.96.
    let bottom_32 = ratio.items[0] & 0xFFFF_FFFF;
    let round_up = if bottom_32 == 0 { 0u128 } else { 1u128 };
    let result = ratio
        .shift_right(32)
        .add(&U512::new(0, 0, 0, round_up))?;

    Ok(result)
}

pub fn tick_index_from_sqrt_price(sqrt_price_x96: &U512) -> Result<i32, SoulMathError> {
    if sqrt_price_x96.lt(&MIN_SQRT_RATIO) || sqrt_price_x96.gte(&MAX_SQRT_RATIO) {
        return Err(SoulMathError::PriceIsNotInRange)
    }

    let ratio = sqrt_price_x96.shift_left(32);
    let msb = 512 - ratio.leading_zeros() - 1;

    let mut r = if msb >= 128 {
        ratio.shift_right(msb - 127)
    } else {
        ratio.shift_left(127 - msb)
    };

    let mut log_2: I256 = I256::from_i64((msb as i64) - 128i64).shl(64);

    for i in 0..BIT_PRECISION {
        r = r.mul(&r)?.shift_right(127);
        let f = r.shift_right(128).try_into_u128()?;
        log_2 = log_2.checked_add(&I256::from_i32(f as i32).shl(63 - i))?;
        r = r.shift_right(f as u32);
    }

    let log_sqrt10001 = log_2.checked_mul(&I256::from_i128(255738958999603826347141))?;

    let tick_low: i32 = log_sqrt10001
        .checked_sub(&I256::from_i128(3402992956809132418596140100660247210))?
        .shr(128)
        .try_to_i32()?;


    let tick_hi: i32 = log_sqrt10001
        .checked_add(&I256::from_raw(U256::new(0, 291339464771989622907027621153398088495)))?
        .shr(128)
        .try_to_i32()?;


    let tick = if tick_low == tick_hi {
        tick_low
    } else if sqrt_price_from_tick_index(tick_hi)?.lte(sqrt_price_x96) {
        tick_hi
    } else {
        tick_low
    };

    Ok(tick)
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

pub fn get_amount_x(
    sqrt_price0: &U512,
    sqrt_price1: &U512,
    liquidity: &U512,
    round_up: bool
) -> Result<u128, SoulMathError> {
    let (sqrt_price0, sqrt_price1) = increase_order(sqrt_price0, sqrt_price1);
    let delta_sqrt_price = sqrt_price1.sub(sqrt_price0)?;

    let numerator = delta_sqrt_price
        .mul(liquidity)?
        .shift_left(96);
    let denominator = sqrt_price0.mul(sqrt_price1)?;
    let (quotient, remainder) = numerator.div(&denominator)?;

    let mut amount_x = quotient.try_into_u128()?;

    if round_up && !remainder.is_zero() {
        amount_x += 1;
    }

    Ok(amount_x)
}

pub fn get_amount_y(
    sqrt_price0: &U512,
    sqrt_price1: &U512,
    liquidity: &U512,
    round_up: bool
) -> Result<u128, SoulMathError> {
    let (sqrt_price0, sqrt_price1) = increase_order(sqrt_price0, sqrt_price1);
    let delta_sqrt_price = sqrt_price1.sub(sqrt_price0)?;

    let product = delta_sqrt_price.mul(liquidity)?;

    let mut amount_y = product.shift_right(96).try_into_u128()?;
    let fraction = product
        .shift_left(416)
        .shift_right(416)
        .try_into_u128()?;

    if round_up && fraction != 0 {
        amount_y += 1;
    }

    Ok(amount_y)
}

pub fn get_sqrt_price_from_x(
    sqrt_price_start: &U512,
    liquidity: &U512,
    delta_x: u128,
    amount_specified_is_in: bool,
    round_up: bool
) -> Result<U512, SoulMathError> {
    let scaled_liquidity = liquidity.shift_left(96);
    let x_part_of_denominator = U512::from_u128(delta_x).mul(sqrt_price_start)?;

    if !amount_specified_is_in && scaled_liquidity.lte(&x_part_of_denominator) {
        return Err(SoulMathError::InsufficientLiquidity);
    }

    let denominator = if amount_specified_is_in {
        scaled_liquidity.add(&x_part_of_denominator)?
    } else {
        scaled_liquidity.sub(&x_part_of_denominator)?
    };

    let numerator = liquidity
        .mul(sqrt_price_start)?
        .shift_left(96);

    let (mut quotient, remainder) = numerator.div(&denominator)?;

    if round_up && !remainder.is_zero() {
        quotient = quotient.add(&U512::ONE)?;
    }

    Ok(quotient)
}

pub fn get_sqrt_price_from_y(
    sqrt_price_start: &U512,
    liquidity: &U512,
    delta_y: u128,
    amount_specified_is_in: bool,
    round_up: bool
) -> Result<U512, SoulMathError> {
    let scaled_delta_y = U512::from_u128(delta_y).shift_left(96);
    let liquidity_part_numerator = liquidity.mul(sqrt_price_start)?;

    if !amount_specified_is_in && liquidity_part_numerator.lte(&scaled_delta_y) {
        return Err(SoulMathError::InsufficientLiquidity);
    }

    let numerator = if amount_specified_is_in {
        liquidity_part_numerator.add(&scaled_delta_y)?
    } else {
        liquidity_part_numerator.sub(&scaled_delta_y)?
    };

    let (mut quotient, remainder) = numerator.div(liquidity)?;

    if round_up && !remainder.is_zero() {
        quotient = quotient.add(&U512::ONE)?;
    }

    Ok(quotient)
}

fn increase_order<'a>(a: &'a U512, b: &'a U512) -> (&'a U512, &'a U512) {
    if a.lt(&b) {
        (a, b)
    } else {
        (b, a)
    }
}



#[derive(Copy, Clone, Debug)]
pub struct SwapStepResult {
    pub is_max: bool,      // by is_max is meant that all liquidity from the current price range is used
    pub amount_in: u128,   // pure amount in without any fee regulation
    pub amount_out: u128,
    pub fee_amount: u128,
    pub next_sqrt_price: U512,
}

pub fn calculate_swap(
    sqrt_price: U512,
    boundary_tick: i32,
    liquidity: U512,
    delta_amount: u128,
    fee_rate: u32,
    x_to_y: bool,
    amount_specified_is_in: bool
) -> Result<SwapStepResult, SoulMathError> {
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
    let boundary_sqrt_price= sqrt_price_from_tick_index(boundary_tick)?;


    if x_to_y && amount_specified_is_in {
        let target_sqrt_price = get_sqrt_price_from_x(
            &sqrt_price,
            &liquidity,
            calculate_amount,
            amount_specified_is_in,
            true
        )?;

        if target_sqrt_price.gt(&boundary_sqrt_price) {
            result.next_sqrt_price = target_sqrt_price;
            result.amount_out = get_amount_y(&sqrt_price, &target_sqrt_price, &liquidity, false)?;
            result.amount_in = calculate_amount;
            result.fee_amount = delta_amount - calculate_amount;

        } else {
            result.is_max = true;
            result.next_sqrt_price = boundary_sqrt_price;
            result.amount_out = get_amount_y(&sqrt_price, &boundary_sqrt_price, &liquidity, false)?;
            result.amount_in = get_amount_x(&sqrt_price, &boundary_sqrt_price, &liquidity, true)?;

            let total_amount_in = calculate_amount_with_fee(
                result.amount_in,
                fee_rate,
                false
            )?;
            result.fee_amount = total_amount_in - result.amount_in;
        };

    }
    else if x_to_y && !amount_specified_is_in {
        let target_sqrt_price = get_sqrt_price_from_y(
            &sqrt_price,
            &liquidity,
            calculate_amount,
            amount_specified_is_in,
            false
        )?;

        if target_sqrt_price.gt(&boundary_sqrt_price) {
            result.next_sqrt_price = target_sqrt_price;
            result.amount_out = calculate_amount;
            result.amount_in = get_amount_x(&sqrt_price, &target_sqrt_price, &liquidity, true)?;
        } else {
            result.is_max = true;
            result.next_sqrt_price = boundary_sqrt_price;
            result.amount_out = get_amount_y(&sqrt_price, &boundary_sqrt_price, &liquidity, false)?;
            result.amount_in = get_amount_x(&sqrt_price, &boundary_sqrt_price, &liquidity, true)?;
        }

        let total_amount_in = calculate_amount_with_fee(
            result.amount_in,
            fee_rate,
            false
        )?;
        result.fee_amount = total_amount_in - result.amount_in;

    }
    else if !x_to_y && amount_specified_is_in {
        let target_sqrt_price = get_sqrt_price_from_y(
            &sqrt_price,
            &liquidity,
            calculate_amount,
            amount_specified_is_in,
            false
        )?;

        if target_sqrt_price.lt(&boundary_sqrt_price) {
            result.next_sqrt_price = target_sqrt_price;
            result.amount_out = get_amount_x(&sqrt_price, &target_sqrt_price, &liquidity, false)?;
            result.amount_in = calculate_amount;
            result.fee_amount = delta_amount - calculate_amount;

        } else {
            result.is_max = true;
            result.next_sqrt_price = boundary_sqrt_price;
            result.amount_out = get_amount_x(&sqrt_price, &boundary_sqrt_price, &liquidity, false)?;
            result.amount_in = get_amount_y(&sqrt_price, &boundary_sqrt_price, &liquidity, true)?;

            let total_amount_in = calculate_amount_with_fee(
                result.amount_in,
                fee_rate,
                false
            )?;
            result.fee_amount = total_amount_in - result.amount_in;
        }
    }
    else if !x_to_y && !amount_specified_is_in {
        let target_sqrt_price = get_sqrt_price_from_x(
            &sqrt_price,
            &liquidity,
            calculate_amount,
            amount_specified_is_in,
            true
        )?;

        if target_sqrt_price.lt(&boundary_sqrt_price) {
            result.next_sqrt_price = target_sqrt_price;
            result.amount_out = calculate_amount;
            result.amount_in = get_amount_y(&sqrt_price, &target_sqrt_price, &liquidity, true)?;
        } else {
            result.is_max = true;
            result.next_sqrt_price = boundary_sqrt_price;
            result.amount_out = get_amount_x(&sqrt_price, &boundary_sqrt_price, &liquidity, false)?;
            result.amount_in = get_amount_y(&sqrt_price, &boundary_sqrt_price, &liquidity, true)?;
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



fn calculate_amount_with_fee(delta_amount: u128, fee_rate: u32, strip_fee: bool) -> Result<u128, SoulMathError> {
    let fee_rate_u256 = {
        let fee_rate_scaled = FEE_RATE_MUL_VALUE - fee_rate as u128;
        U256::new(0, fee_rate_scaled)
    };

    if strip_fee {
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