use crate::smart_router::manager_errors::SoulManagerError;

pub fn add_delta_liquidity(liquidity: u128, delta_liquidity: i128) -> Result<u128, SoulManagerError> {
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