/*
AMM - Automated Market Maker.

The main formula is
liquidity = x reserves * y reserves
price = y reserves / x reserves

Swap formula
x -> y
(x reserves + x in) * (y reserves - y out) = L
Amount is specified in
y out = y reserves - L / (x reserves + x in)

Amount is specified out
x in = L / (y reserves - y out) - x reserves

y -> x
(x reserves - x out) * (y reserves + y in) = L
Amount is specified in
x out = reserves x - L / (y reserves + y in)

Amount is specified out
y in = L / (x reserves - x out) - y reserves

*/
use crate::math::errors::SoulMathError;
use crate::math::u256::{mul_q64x64, U256};


pub const FEE_RATE_MUL_VALUE: u128 = 1_000_000;

#[derive(Copy, Clone, Debug)]
pub struct SwapStepResult {
    pub amount_in: u128,
    pub amount_out: u128,
    pub fee_amount: u128,
}

pub fn calculate_swap(
    x_reserves: u128,
    y_reserves: u128,
    delta_amount: u128,
    fee_rate: u32,
    x_to_y: bool,
    amount_specified_is_in: bool
) -> Result<SwapStepResult, SoulMathError> {
    let mut result = SwapStepResult{
        amount_in: 0,
        amount_out: 0,
        fee_amount: 0
    };

    let calculate_amount = if amount_specified_is_in {
        calculate_amount_with_fee(delta_amount, fee_rate, true)?
    } else {
        delta_amount
    };

    if x_to_y && amount_specified_is_in {
        let numerator = mul_q64x64(y_reserves, calculate_amount);
        let denominator = U256::new(0, x_reserves + calculate_amount);

        let (quotient, _remainder) = numerator.div(&denominator)?;
        result.amount_out = quotient.try_into_u128()?;
        result.amount_in = calculate_amount;
        result.fee_amount = delta_amount - calculate_amount;
    }
    else if x_to_y && !amount_specified_is_in {
        if calculate_amount >= y_reserves {
            return Err(SoulMathError::InsufficientLiquidity);
        }

        let numerator = mul_q64x64(x_reserves, calculate_amount);
        let denominator = U256::new(0, y_reserves - calculate_amount);

        let (quotient, remainder) = numerator.div(&denominator)?;

        result.amount_out = calculate_amount;
        result.amount_in = quotient.try_into_u128()?;
        if !remainder.is_zero() {
            result.amount_in += 1;
        }
        let total_amount_in = calculate_amount_with_fee(
            result.amount_in,
            fee_rate,
            false
        )?;
        result.fee_amount = total_amount_in - result.amount_in;
    }
    else if !x_to_y && amount_specified_is_in {
        let numerator = mul_q64x64(x_reserves, calculate_amount);
        let denominator = U256::new(0, y_reserves + calculate_amount);

        let (quotient, _remainder) = numerator.div(&denominator)?;
        result.amount_out = quotient.try_into_u128()?;
        result.amount_in = calculate_amount;
        result.fee_amount = delta_amount - calculate_amount;
    }
    else if !x_to_y && !amount_specified_is_in {
        if calculate_amount >= x_reserves {
            return Err(SoulMathError::InsufficientLiquidity);
        }

        let numerator = mul_q64x64(y_reserves, calculate_amount);
        let denominator = U256::new(0, x_reserves - calculate_amount);

        let (quotient, remainder) = numerator.div(&denominator)?;

        result.amount_out = calculate_amount;
        result.amount_in = quotient.try_into_u128()?;
        if !remainder.is_zero() {
            result.amount_in += 1;
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