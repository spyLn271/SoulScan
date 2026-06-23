use thiserror::Error;

#[derive(Debug, Error)]
pub enum SoulOsrError {
    #[error("This network is not supported")]
    NotSupportedNetwork,

    #[error("This token wasn't found in nodes")]
    ThisTokenWasNotFoundInNodes,

    #[error("This token wasn't found in tokens")]
    ThisTokenWasNotFoundInTokens,

    #[error("no metadata was found")]
    NoMetadataForPool,

    #[error("no state was found")]
    NoStateForPool,

    #[error("Pool mints dont match with processing mint")]
    NoMatchWithMint,

    #[error("Soul Manager error {0}")]
    SoulMathManagerError(#[from] rusted_soul_dex::smart_router::manager_errors::SoulManagerError),

    #[error("Failed to get fee rate")]
    FailedToGetFeeRate,

    #[error("Failed to get tick spacing")]
    FailedToGetTickSpacing,

    #[error("Time Error {0}")]
    TimeError(#[from] std::time::SystemTimeError),
}