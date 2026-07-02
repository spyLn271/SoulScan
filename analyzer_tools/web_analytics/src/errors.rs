use axum::http::StatusCode;
use thiserror::Error;
use axum::response::{IntoResponse, Response};

#[derive(Error, Debug)]
pub enum  WebErrors {
    #[error("Something went wrong in SoulEngine {0}")]
    SoulEngineError(#[from] rusted_engine::errors::SoulEngineErrors),

    #[error("Something went wrong in SoulMAth {0}")]
    SoulMathError(#[from] rusted_soul_dex::errors::Errors),

    #[error("Something went wrong in SOR {0}")]
    SoulSmartRouterError(#[from] rusted_soul_dex::smart_router::smart_router_errors::SoulSmartRouterError),


    #[error("Unexpected move")]
    NotSupportedNetwork,
    
    #[error("Unexpected move")]
    Error(String),
}

impl IntoResponse for WebErrors {
    fn into_response(self) -> Response {

        match &self {
            WebErrors::SoulEngineError(s) => (StatusCode::INTERNAL_SERVER_ERROR, format!("{}", s)),
            WebErrors::SoulMathError(s) => (StatusCode::INTERNAL_SERVER_ERROR, format!("{}", s)),
            WebErrors::SoulSmartRouterError(s) => (StatusCode::INTERNAL_SERVER_ERROR, format!("{}", s)),
            WebErrors::NotSupportedNetwork => (StatusCode::BAD_REQUEST, format!("{}", "Not supported Network")),
            WebErrors::Error(err) => (StatusCode::INTERNAL_SERVER_ERROR, format!("{}", err)),
        }.into_response()
    }
}