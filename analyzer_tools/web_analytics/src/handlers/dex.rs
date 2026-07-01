use std::collections::BTreeMap;
use std::time::{Duration, Instant};
use axum::{
    routing::{post, get},
    Router,
};
use axum::extract::{State, Json, Path as APath};
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};

use rusted_engine::api::dex::snapshot::{
    get_pool_state_for_network,
    get_metadata_for_network,
    get_token_addresses,
    TokenData
};

use rusted_soul_dex::dex::metadata::Path;
use rusted_soul_dex::smart_router::v2::router::SmartRouterV2;
use rusted_soul_dex::dex::metadata::Metadata;

use serde::{Deserialize, Serialize};
use crate::AppState;
use crate::errors::WebErrors;

#[derive(Deserialize)]
pub struct GetQuote {
    network: String,
    address0: String,
    address1: String,
    amount: u128,
    a_to_b: bool,
    amount_specified_is_in: bool
}
#[derive(Debug, Serialize)]
pub struct SorQuoteResult {
    pub paths: Vec<(Path, (u128, u128))>,
    pub total_amount_in: u128,
    pub total_amount_out: u128,
    pub execution_time: Option<Duration>
}

#[derive(Debug, Serialize)]
pub struct MetadataListResult {
    pub data: BTreeMap<String, Metadata>
}

#[derive(Debug, Serialize)]
pub struct TokenListResult {
    pub data: BTreeMap<usize, (String, TokenData)>
}


impl IntoResponse for SorQuoteResult {
    fn into_response(self) -> Response {
        (StatusCode::OK, Json(self)).into_response()
    }
}

impl IntoResponse for MetadataListResult {
    fn into_response(self) -> Response {
        (StatusCode::OK, Json(self)).into_response()
    }
}

impl IntoResponse for TokenListResult {
    fn into_response(self) -> Response {
        (StatusCode::OK, Json(self)).into_response()
    }
}

pub fn routes(app_state: AppState) -> Router {
    Router::new()
        .route("/v1/sor", post(quote_sor))
        .route("/v1/metadata/{network}", get(metadata))
        .route("/v1/tokens/{network}", get(token_list))
        .with_state(app_state)
}

pub async fn quote_sor(
    State(state): State<AppState>,
    Json(payload): Json<GetQuote>
) -> Result<SorQuoteResult, WebErrors> {
    let redis_pool_conn = state.redis_pool_conn.clone();

    let result = tokio::task::spawn_blocking(move || {
        let started = Instant::now();
        
        let pool_state = get_pool_state_for_network(
            &redis_pool_conn,
            payload.network.as_str(),
            false
        )?;
        println!("(pool_state) time elapsed: {:?}", started.elapsed());

        let metadata = get_metadata_for_network(
            &redis_pool_conn,
            payload.network.as_str(),
        )?;
        println!("(metadata) time elapsed: {:?}", started.elapsed());

        let mut sor_v2 = SmartRouterV2::new(
            &metadata,
            &pool_state,
            &redis_pool_conn,
        );
        println!("(sor_v2) time elapsed: {:?}", started.elapsed());

        let result = sor_v2.smart_router(
            &payload.address0,
            &payload.address1,
            payload.amount,
            payload.a_to_b,
            payload.amount_specified_is_in,
        )?;

        Ok::<_, WebErrors>(result)
    })
        .await
        .map_err(|_| { WebErrors::Error })??;

    let paths = {
        result.paths.into_iter()
            .map(|(path, (amount_in, amount_out))| {
                (path, (amount_in, amount_out))
            })
            .collect::<Vec<(Path, (u128, u128))>>()
    };

    Ok(
        SorQuoteResult {
            paths,
            total_amount_in: result.total_amount_in,
            total_amount_out: result.total_amount_out,
            execution_time: result.execution_time
        }
    )
}

pub async fn metadata(
    State(state): State<AppState>,
    APath(network): APath<String>,
) -> Result<MetadataListResult, WebErrors> {
    let started = Instant::now();
    let redis_pool_conn = state.redis_pool_conn.clone();
    println!("(redis_pool_conn) time elapsed: {:?}", started.elapsed());

    let metadata = get_metadata_for_network(
        &redis_pool_conn,
        network.as_str(),
    )?;
    println!("(metadata) time elapsed: {:?}", started.elapsed());

    Ok(
        MetadataListResult {
            data: metadata
        }
    )
}

pub async fn token_list (
    State(state): State<AppState>,
    APath(network): APath<String>,
) -> Result<TokenListResult, WebErrors> {
    let started = Instant::now();
    let redis_pool_conn = state.redis_pool_conn.clone();
    println!("(redis_pool_conn) time elapsed: {:?}", started.elapsed());

    let tokens = get_token_addresses(
        &redis_pool_conn,
        network.as_str(),
    )?;
    println!("(metadata) time elapsed: {:?}", started.elapsed());

    Ok(
        TokenListResult {
            data: tokens
        }
    )
}