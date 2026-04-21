use std::convert::From;
use crate::math::errors::SoulMathError;

#[derive(Debug)]
pub enum SoulManagerError {
    MathError(SoulMathError),
    RunOutOfLiquidity,
    LiquidityOverflow,
    LiquidityUnderflow,
    AmountOverflow
}

impl From<SoulMathError> for SoulManagerError {
    fn from(error: SoulMathError) -> Self {
        SoulManagerError::MathError(error)
    }
}