use thiserror::Error;

#[derive(Debug, Error)]
pub enum SoulMathError {
    #[error("Overflow adding")]
    AddOverflow,
    
    #[error("Subtraction underflow")]
    SubUnderflow,

    #[error("Multiplication overflow")]
    MulOverflow,

    #[error("Division Overflow in singed integer")]
    DivisionOverflow,

    #[error("Cant be divided by zero")]
    CantBeDividedByZero,

    #[error("number down cast")]
    NumberDownCastError,

    #[error("Insufficient Liquidity")]
    InsufficientLiquidity,

    #[error("tick is more than or less than required amount")]
    TickIsNotInRange,

    #[error("Price is more than or less than required amount")]
    PriceIsNotInRange,
}