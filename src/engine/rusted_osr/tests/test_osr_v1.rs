use std::collections::BTreeMap;
use std::sync::Arc;
use std::time::Instant;

use std::path::Path;

use r2d2::Pool;
use r2d2_redis::RedisConnectionManager;

use rusted_engine::api::dex::snapshot::{get_metadata_for_network, StateViewer};
use rusted_soul_dex::dex::meteora::MeteoraDlmmPool;
use rusted_soul_dex::dex::orca::Whirlpool;
use rusted_soul_dex::dex::raydium::{RayAmmPool, RayClmmPool};
use rusted_soul_dex::dex::uniswap::UniswapClmmPools;
use rusted_soul_dex::smart_router::v2::router::PoolStateV2;
use rusted_osr::osr::engine::v1::OsrEngine;
use rusted_osr::logging;

#[test]
fn test_osr_engine() {

    let _guard = logging::init(&Path::new("foo/"))
        .expect("failed to initialize logging");

    logging::install_panic_hook();

    let client = RedisConnectionManager::new(
        String::from("redis://localhost:6379")
    ).unwrap();
    let redis_conn_pool= Pool::builder()
        .max_size(15)
        .build(client)
        .unwrap();

    let network = "solana".to_string();


    let metadata = Arc::new(
        get_metadata_for_network(
            &redis_conn_pool,
            network.as_str()
        ).unwrap()
    );


    let pool_state_v2 = Arc::new(
        PoolStateV2 {
            meteora_dlmm_pool: Arc::new(
                MeteoraDlmmPool::get_state_snapshot(
                    &redis_conn_pool,
                    network.as_str(),
                    false
                ).unwrap()
            ),
            whirlpool: Arc::new(
                Whirlpool::get_state_snapshot(
                    &redis_conn_pool,
                    network.as_str(),
                    false
                ).unwrap()
            ),
            ray_clmm_pool: Arc::new(
                RayClmmPool::get_state_snapshot(
                    &redis_conn_pool,
                    network.as_str(),
                    false
                ).unwrap()
            ),
            ray_amm_pool: Arc::new(
                RayAmmPool::get_state_snapshot(
                    &redis_conn_pool,
                    network.as_str(),
                    false
                ).unwrap()
            ),
            uni_amm_pool: Arc::new(BTreeMap::new()),
            uni_clmm_pool: Arc::new(UniswapClmmPools{slot0s: BTreeMap::new(), ticks: BTreeMap::new()}),
        }
    );

    let osr_engine = OsrEngine::new(
        network.clone(),
        metadata.clone(),
        pool_state_v2.clone(),
    ).unwrap();

    let quote_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v".to_string();
    // for base_mint in osr_engine.tokens_graph.tokens.iter() {
    //     let cold_path_t_1 = osr_engine.find_the_best_cold_path(
    //         base_mint.0.clone(),
    //         quote_mint.clone(),
    //         5
    //     ).unwrap();
    // }

    osr_engine.find_the_best_cold_path(
        "GozPNCAseytzxCR3d2k8hTsTYkr4SDpuXy2RQAZFVx2g".to_string(),
        quote_mint.clone(),
        5
    );
}