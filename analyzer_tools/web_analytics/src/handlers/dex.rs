use crate::AppState;

use axum::{
    extract::{Json, Path as QPath, State},
    routing::{get, post},
    http::{StatusCode},
    response::{IntoResponse, Response},
    Router
};

use rusted_soul_dex::{
    dex::{
        uniswap::{ UniswapClmmPools, Slot0, TickData, UniswapAmm },
        raydium::{ RayAmmPool, RayClmmPool },
        orca::Whirlpool,
        meteora::MeteoraDlmmPool,
        metadata::{ Metadata, Path }
    },
    smart_router::v2::router::{ SmartRouterV2, PoolStateV2 },
};

use rusted_engine::{
    config::SUPPORTED_NETWORK_LIST,
    api::dex::snapshot::{ PoolSnapshot, TokenData }
};

use serde::{ Serialize, Deserialize };

use std::collections::BTreeMap;
use std::sync::Arc;
use std::time::{Duration, Instant};
use deadpool_redis::redis::AsyncTypedCommands;
use crate::errors::WebErrors;



pub fn routes(app_state: AppState) -> Router {
    Router::new()
        .route("/v1/sor", post(quote_sor))
        .route("/v1/metadata/{network}", get(metadata))
        .route("/v1/tokens/{network}", get(token_list))
        .with_state(app_state)
}


#[derive(Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Network {
    Solana,
    Eth,
    Base,
    Arbitrum,
    Bsc
}

// Post Quote Sor API

#[derive(Deserialize)]
pub struct GetQuoteSor {
    network: Network,
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

async fn quote_sor(
    State(state): State<AppState>,
    Json(payload): Json<GetQuoteSor>
) -> Result<SorQuoteResult, WebErrors> {
    let mut conn = state.redis_pool_conn
        .get()
        .await?;

    let mut pipe = deadpool_redis::redis::pipe();

    match payload.network {
        Network::Solana => {
            pipe.get("snapshot:state:solana:orca:clmm");
            pipe.get("snapshot:state:solana:raydium:clmm");
            pipe.get("snapshot:state:solana:raydium:amm");
            pipe.get("snapshot:state:solana:meteora:dlmm");

            pipe.get("snapshot:metadata:solana:orca:clmm");
            pipe.get("snapshot:metadata:solana:raydium:clmm");
            pipe.get("snapshot:metadata:solana:raydium:amm");
            pipe.get("snapshot:metadata:solana:meteora:dlmm");
        },
        Network::Eth | Network::Bsc | Network::Arbitrum | Network::Base => {
            pipe.get(format!("snapshot:state:{}:uniswap:v2", payload.network.as_str()));

            pipe.hget(
                format!("snapshot:state:{}:uniswap:v3", payload.network.as_str()),
                "slot"
            );
            pipe.hget(
                format!("snapshot:state:{}:uniswap:v3", payload.network.as_str()),
                "ticks"
            );
            pipe.hget(
                format!("snapshot:state:{}:uniswap:v4", payload.network.as_str()),
                "slot"
            );
            pipe.hget(
                format!("snapshot:state:{}:uniswap:v4", payload.network.as_str()),
                "ticks"
            );


            pipe.get(format!("snapshot:metadata:{}:uniswap:v2", payload.network.as_str()));
            pipe.get(format!("snapshot:metadata:{}:uniswap:v3", payload.network.as_str()));
            pipe.get(format!("snapshot:metadata:{}:uniswap:v4", payload.network.as_str()));
        },
    };

    let raw_data: Vec<String> = pipe.query_async(&mut conn).await?;

    let result = tokio::task::spawn_blocking(move || -> Result<SorQuoteResult, WebErrors> {
        let (pool_state, metadata) = match payload.network {
            Network::Solana => {
                let whirlpool: PoolSnapshot<String, Whirlpool> = serde_json::from_str(
                    raw_data
                        .get(0)
                        .ok_or_else(|| WebErrors::Error("whirlpool data wasn't found".to_string()))?
                )?;

                let ray_clmm: PoolSnapshot<String, RayClmmPool> = serde_json::from_str(
                    raw_data
                        .get(1)
                        .ok_or_else(|| WebErrors::Error("ray_clmm data wasn't found".to_string()))?
                )?;

                let ray_amm: PoolSnapshot<String, RayAmmPool> = serde_json::from_str(
                    raw_data
                        .get(2)
                        .ok_or_else(|| WebErrors::Error("ray_amm data wasn't found".to_string()))?
                )?;

                let meteora_dlmm: PoolSnapshot<String, MeteoraDlmmPool> = serde_json::from_str(
                    raw_data
                        .get(3)
                        .ok_or_else(|| WebErrors::Error("meteora_dlmm data wasn't found".to_string()))?
                )?;

                let pool_state = PoolStateV2{
                    whirlpool: Arc::new(whirlpool.pool_state),
                    ray_amm_pool: Arc::new(ray_amm.pool_state),
                    ray_clmm_pool: Arc::new(ray_clmm.pool_state),
                    meteora_dlmm_pool: Arc::new(meteora_dlmm.pool_state),
                    uni_amm_pool: Arc::new(BTreeMap::new()),
                    uni_clmm_pool: Arc::new(UniswapClmmPools{slot0s: BTreeMap::new(), ticks: BTreeMap::new()}),
                };

                let mut metadata: BTreeMap<String, Metadata> = BTreeMap::new();

                for idx in 4..8 {
                    let md: BTreeMap<String, Metadata> = serde_json::from_str(
                        raw_data
                            .get(idx)
                            .ok_or_else(|| WebErrors::Error("metadata data wasn't found".to_string()))?
                    )?;
                    metadata.extend(md);
                };

                (pool_state, metadata)
            },
            Network::Eth | Network::Bsc | Network::Arbitrum | Network::Base => {
                let uni_amm: PoolSnapshot<String, UniswapAmm> = serde_json::from_str(
                    raw_data
                        .get(0)
                        .ok_or_else(|| WebErrors::Error("uni_amm data wasn't found".to_string()))?
                )?;

                let uni_slot_v3: PoolSnapshot<String, Slot0> = serde_json::from_str(
                    raw_data
                        .get(1)
                        .ok_or_else(|| WebErrors::Error("uni_slot_v3 data wasn't found".to_string()))?
                )?;

                let uni_ticks_v3: PoolSnapshot<String, BTreeMap<i32, TickData>> = serde_json::from_str(
                    raw_data
                        .get(2)
                        .ok_or_else(|| WebErrors::Error("uni_ticks_v3 data wasn't found".to_string()))?
                )?;

                let uni_slot_v4: PoolSnapshot<String, Slot0> = serde_json::from_str(
                    raw_data
                        .get(3)
                        .ok_or_else(|| WebErrors::Error("uni_slot_v4 data wasn't found".to_string()))?
                )?;

                let uni_ticks_v4: PoolSnapshot<String, BTreeMap<i32, TickData>> = serde_json::from_str(
                    raw_data
                        .get(4)
                        .ok_or_else(|| WebErrors::Error("uni_ticks_v4 data wasn't found".to_string()))?
                )?;

                let mut slot0s: BTreeMap<String, Slot0> = uni_slot_v3.pool_state;
                slot0s.extend(uni_slot_v4.pool_state);

                let mut ticks: BTreeMap<String, BTreeMap<i32, TickData>> = uni_ticks_v3.pool_state;
                ticks.extend(uni_ticks_v4.pool_state);

                let uni_clmm = UniswapClmmPools {
                    slot0s,
                    ticks,
                };

                let pool_state = PoolStateV2 {
                    uni_amm_pool: Arc::new(uni_amm.pool_state),
                    uni_clmm_pool: Arc::new(uni_clmm),
                    meteora_dlmm_pool: Arc::new(BTreeMap::new()),
                    whirlpool: Arc::new(BTreeMap::new()),
                    ray_clmm_pool: Arc::new(BTreeMap::new()),
                    ray_amm_pool: Arc::new(BTreeMap::new()),
                };

                let mut metadata: BTreeMap<String, Metadata> = BTreeMap::new();

                for idx in 5..8 {
                    let md: BTreeMap<String, Metadata> = serde_json::from_str(
                        raw_data
                            .get(idx)
                            .ok_or_else(|| WebErrors::Error("metadata data wasn't found".to_string()))?
                    )?;
                    metadata.extend(md);
                }

                (pool_state, metadata)
            }
        };

        let mut sor_v2 = SmartRouterV2::new(
            &metadata,
            &pool_state,
            &state.blocking_redis_pool_conn
        );

        let result = sor_v2.smart_router(
            &payload.address0,
            &payload.address1,
            payload.amount,
            payload.a_to_b,
            payload.amount_specified_is_in,
        )?;

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
    })
        .await
        .map_err(|_| WebErrors::Error("Some Shit in result".to_string()))??;

    Ok(result)
}


// Get Metadata API

#[derive(Debug, Serialize)]
pub struct MetadataListResult {
    pub data: BTreeMap<String, Metadata>
}

pub async fn metadata(
    State(state): State<AppState>,
    QPath(network): QPath<Network>,
) -> Result<MetadataListResult, WebErrors> {
    let mut conn = state.redis_pool_conn
        .get()
        .await?;

    let mut pipe = deadpool_redis::redis::pipe();

    match network  {
        Network::Solana => {
            pipe.get("snapshot:metadata:solana:orca:clmm");
            pipe.get("snapshot:metadata:solana:raydium:clmm");
            pipe.get("snapshot:metadata:solana:raydium:amm");
            pipe.get("snapshot:metadata:solana:meteora:dlmm");
        },
        Network::Eth | Network::Bsc | Network::Arbitrum | Network::Base => {
            pipe.get(format!("snapshot:metadata:{}:uniswap:v2", network.as_str()));
            pipe.get(format!("snapshot:metadata:{}:uniswap:v3", network.as_str()));
            pipe.get(format!("snapshot:metadata:{}:uniswap:v4", network.as_str()));
        },
    };

    // println!("{:?}", conn.get("snapshot:metadata:solana:orca:clmm").await);

    let raw_data: Vec<String> = pipe.query_async(&mut conn)
        .await?;

    let mut metadata: BTreeMap<String, Metadata> = BTreeMap::new();

    for raw in raw_data.iter() {
        let md: BTreeMap<String, Metadata> = serde_json::from_str(raw)?;
        metadata.extend(md);
    };

    Ok(
        MetadataListResult {
            data: metadata
        }
    )
}

// Get TokenList API

#[derive(Debug, Serialize)]
pub struct TokenListResult {
    pub data: BTreeMap<String, TokenData>
}

pub async fn token_list (
    State(state): State<AppState>,
    QPath(network): QPath<Network>,
) -> Result<TokenListResult, WebErrors> {
    let mut conn = state.redis_pool_conn
        .get()
        .await?;

    let raw_data = conn
        .get(format!("snapshot:addresses:{}", network.as_str()))
        .await?
        .ok_or(WebErrors::Error("fuck token list".to_string()))?;

    let token_list: BTreeMap<String, TokenData> = serde_json::from_str(&raw_data)?;

    Ok(
        TokenListResult {
            data: token_list
        }
    )
}





impl IntoResponse for TokenListResult {
    fn into_response(self) -> Response {
        (StatusCode::OK, Json(self)).into_response()
    }
}

impl IntoResponse for MetadataListResult {
    fn into_response(self) -> Response {
        (StatusCode::OK, Json(self)).into_response()
    }
}

impl IntoResponse for SorQuoteResult {
    fn into_response(self) -> Response {
        (StatusCode::OK, Json(self)).into_response()
    }
}

impl Network {
    fn as_str(&self) -> &str {
        match self {
            Network::Solana => "solana",
            Network::Eth => "eth",
            Network::Arbitrum => "arbitrum",
            Network::Bsc => "bsc",
            Network::Base => "base",
        }
    }
}