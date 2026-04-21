use std::convert::From;

use crate::math::errors::SoulMathError;
use crate::smart_router::manager_errors::SoulManagerError;
use crate::smart_router::smart_router_errors::SoulSmartRouterError;

#[derive(Debug)]
pub enum Errors {
    MathError(SoulMathError),
    ManagerError(SoulManagerError),
    SmartRouterError(SoulSmartRouterError)
}

impl From<SoulMathError> for Errors {
    fn from(error: SoulMathError) -> Self {
        Errors::MathError(error)
    }
}

impl From<SoulManagerError> for Errors {
    fn from(error: SoulManagerError) -> Self {
        Errors::ManagerError(error)
    }
}

impl From<SoulSmartRouterError> for Errors{
    fn from(error: SoulSmartRouterError) -> Self {
        Errors::SmartRouterError(error)
    }
}