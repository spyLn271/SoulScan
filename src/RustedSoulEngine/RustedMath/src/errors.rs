use thiserror::Error;

use crate::math::errors::SoulMathError;
use crate::smart_router::manager_errors::SoulManagerError;
use crate::smart_router::smart_router_errors::SoulSmartRouterError;

#[derive(Debug, Error)]
pub enum Errors {
    #[error("Soul Math error {0}")]
    MathError(#[from] SoulMathError),

    #[error("Soul Manager error {0}")]
    ManagerError(#[from] SoulManagerError),

    #[error("Smart Router error {0}")]
    SmartRouterError(#[from] SoulSmartRouterError)
}