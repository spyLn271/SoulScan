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

    #[error("Deadpool-redis error: {0}")]
    RedisPoolError(#[from] deadpool_redis::PoolError),

    #[error("redis error: {0}")]
    RedisError(#[from] deadpool_redis::redis::RedisError),

    #[error("json error: {0}")]
    JsonError(#[from] serde_json::Error),

    #[error("Error parsing float {0}")]
    ParseFloatError(#[from] std::num::ParseFloatError),

    #[error("Error parsing from redis value {0}")]
    ParseRedisValueError(#[from] deadpool_redis::redis::ParsingError),

    #[error("Database error: {0}")]
    DatabaseError(#[from] sqlx::Error),

    #[error("Unexpected move")]
    Error(String),

    #[error("Wrong Credentials")]
    WrongCredentials,
    #[error("Missing Credentials")]
    MissingCredentials,
    #[error("Token Creation")]
    TokenCreation,
    #[error("Invalid Token")]
    InvalidToken,
}

impl IntoResponse for WebErrors {
    fn into_response(self) -> Response {

        match &self {
            WebErrors::SoulEngineError(s) => (StatusCode::INTERNAL_SERVER_ERROR, format!("{}", s)),
            WebErrors::SoulMathError(s) => (StatusCode::INTERNAL_SERVER_ERROR, format!("{}", s)),
            WebErrors::SoulSmartRouterError(s) => (StatusCode::INTERNAL_SERVER_ERROR, format!("{}", s)),
            WebErrors::NotSupportedNetwork => (StatusCode::BAD_REQUEST, format!("{}", "Not supported Network")),
            WebErrors::RedisPoolError(s) => (StatusCode::INTERNAL_SERVER_ERROR, format!("{}", s)),
            WebErrors::RedisError(s) => (StatusCode::INTERNAL_SERVER_ERROR, format!("{}", s)),
            WebErrors::JsonError(s) => (StatusCode::INTERNAL_SERVER_ERROR, format!("{}", s)),
            WebErrors::ParseFloatError(s) => (StatusCode::INTERNAL_SERVER_ERROR, format!("{}", s)),
            WebErrors::ParseRedisValueError(s) => (StatusCode::INTERNAL_SERVER_ERROR, format!("{}", s)),
            WebErrors::Error(err) => (StatusCode::INTERNAL_SERVER_ERROR, format!("{}", err)),
            WebErrors::WrongCredentials => (StatusCode::UNAUTHORIZED, "Wrong credentials".to_string()),
            WebErrors::MissingCredentials => (StatusCode::BAD_REQUEST, "Missing credentials".to_string()),
            WebErrors::TokenCreation => (StatusCode::INTERNAL_SERVER_ERROR, "Token creation error".to_string()),
            WebErrors::InvalidToken => (StatusCode::BAD_REQUEST, "Invalid token".to_string()),
            WebErrors::DatabaseError(s) => (StatusCode::INTERNAL_SERVER_ERROR, format!("{}", s)),
        }.into_response()
    }
}