use thiserror::Error;
use crate::math::errors::SoulMathError;

#[derive(Debug, Error)]
pub enum SoulManagerError {
    #[error("Error in Math u256 {0}")]
    MathError(#[from] SoulMathError),

    #[error("Run out of Liquidity")]
    RunOutOfLiquidity,

    #[error("Liquidity overflow (more that u128 can handle)")]
    LiquidityOverflow,

    #[error("Unsufficient Liquidity")]
    LiquidityUnderflow,

    #[error("Amount overflow")]
    AmountOverflow
}