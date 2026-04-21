#[derive(Debug)]
pub enum SoulMathError {
    AddOverflow,
    SubUnderflow,
    MulOverflow,
    CantBeDividedByZero,
    NumberDownCastError,
    InsufficientLiquidity
}