use crate::smart_router::manager_errors::SoulManagerError;
use crate::math::errors::SoulMathError;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum SoulSmartRouterError {
    #[error("error in Manager {0}")]
    ManagerError(#[from] SoulManagerError),

    #[error("error in Math {0}")]
    MathError(#[from] SoulMathError),

    #[error("no metadata was found")]
    NoMetadataForPool,

    #[error("no metadata was found")]
    NoStateForPool,

    #[error("error in redis {0}")]
    RedisError(#[from] r2d2_redis::redis::RedisError),

    #[error("error in pool connection {0}")]
    PoolConnectionError(#[from] r2d2::Error),

    #[error("error in json {0}")]
    JsonError(#[from] serde_json::Error),

    #[error("Pool mints dont match with processing mint")]
    NoMatchWithMint,

    #[error("Didnt find such a pool {0} in Pool State")]
    NoPoolInPoolState(String),

    #[error("Unsupported Market")]
    UnsupportedMarket,

    #[error("Time Error {0}")]
    TimeError(#[from] std::time::SystemTimeError),

    #[error("Int Parse error {0}")]
    ParseIntError(#[from] std::num::ParseIntError),

    #[error("Cold Path Expired")]
    ColdPathExpired,

    #[error("Failed to find Max / Min")]
    FailedToFindBestResult,

    #[error("Failed to get fee rate")]
    FailedToGetFeeRate,

    #[error("Failed to get fee rate")]
    FailedToGetTickSpacing,

    #[error("While iterating through IA5, one chunk couldnt be processed and find the best result")]
    CouldntFindTheBestResultForChunkAmount,

    #[error("There is no routes for chosen pair")]
    NoRoutes,

    #[error("Unexpected Update Error")]
    UnexpectedUpdateError,

    #[error("error")]
    Error,
}