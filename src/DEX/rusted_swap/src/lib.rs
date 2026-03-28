use pyo3::prelude::*;
use serde;

pub mod manager;
pub mod math;


/// A Python module implemented in Rust.
#[pymodule]
mod rusted_swap {
    use pyo3::prelude::*;
    use pyo3::exceptions::PyValueError;
    use crate::manager::orca::clmm::swap_manager::{swap_manager, SwapResult, Whirlpool};
    use crate::manager::errors::SoulManagerError;

    #[pyfunction]
    fn orca_swap(
        x_to_y: bool,
        amount_specified_is_in: bool,
        delta_amount: u128,
        timestamp: u64,
        whirlpool: &str
    ) -> PyResult<SwapResult> {
        let whirlpool: Whirlpool = serde_json::from_str(whirlpool).unwrap();

        let swap_result = swap_manager (
            x_to_y,
            amount_specified_is_in,
            delta_amount,
            timestamp,
            &whirlpool
        );

        match swap_result {
            Ok(res) => Ok(res),
            Err(err) => {
                match err {
                    SoulManagerError::RunOutOfLiquidity => Err(PyValueError::new_err("RunOutOfLiquidity")),
                    SoulManagerError::MathError(math) => Err(PyValueError::new_err("MathError")),
                    SoulManagerError::LiquidityUnderflow => Err(PyValueError::new_err("LiquidityUnderflow")),
                    SoulManagerError::AmountOverflow => Err(PyValueError::new_err("AmountOverflow")),
                    SoulManagerError::LiquidityOverflow => Err(PyValueError::new_err("LiquidityOverflow")),
                }
            }
        }
    }
}
