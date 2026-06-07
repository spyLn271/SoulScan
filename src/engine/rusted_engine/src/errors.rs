use thiserror::Error;

#[derive(Debug, Error)]
pub enum SoulEngineErrors {
    #[error("error in Rusted Soul Dex Errors {0}")]
    RustedSoulDexErrors(#[from] rusted_soul_dex::errors::Errors),

    #[error("error in json {0}")]
    JsonError(#[from] serde_json::Error),

    #[error("error in pool connection {0}")]
    PoolConnectionError(#[from] r2d2::Error),

    #[error("error in redis {0}")]
    RedisError(#[from] r2d2_redis::redis::RedisError),

    #[error("Time Error {0}")]
    TimeError(#[from] std::time::SystemTimeError),

    #[error("Error parsing float {0}")]
    ParseFloatError(#[from] std::num::ParseFloatError),

    #[error("not bids and not asks")]
    NotSupportedOrderSide,

    #[error("Not Supported Exchange")]
    NotSupportedExchange,

    #[error("No Stream")]
    StreamWasNotFound,

    #[error("No Entry")]
    NoEntry,

    #[error("order book data wasn't found")]
    OrderBookDataNotFound,

    #[error("This network is not supported")]
    NotSupportedNetwork,
    
    #[error("This (market, version) combination is not supported in this network")]
    NotSupportedMarket,

    #[error("Data is stale")]
    StalePoolStateData,

    #[error("This symbol is not inactive")]
    InactiveSymbol,

    #[error("Error")]
    Error,
}

