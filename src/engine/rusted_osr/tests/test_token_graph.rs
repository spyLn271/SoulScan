use std::collections::BTreeMap;
use std::sync::Arc;
use std::time::Instant;

use r2d2::Pool;
use r2d2_redis::RedisConnectionManager;

use rusted_engine::api::dex::snapshot::{get_metadata_for_network, StateViewer};
use rusted_soul_dex::dex::meteora::MeteoraDlmmPool;
use rusted_soul_dex::dex::orca::Whirlpool;
use rusted_soul_dex::dex::raydium::{RayAmmPool, RayClmmPool};
use rusted_soul_dex::dex::uniswap::UniswapClmmPools;
use rusted_soul_dex::smart_router::v2::router::PoolStateV2;
use rusted_osr::osr::token_graph::TokensGraph;

#[test]
fn test_token_graph() {
    let client = RedisConnectionManager::new(
        String::from("redis://localhost:6379")
    ).unwrap();
    let redis_conn_pool= Pool::builder()
        .max_size(15)
        .build(client)
        .unwrap();

    let network = "solana".to_string();


    let metadata = get_metadata_for_network(
        &redis_conn_pool,
        network.as_str()
    ).unwrap();


    let pool_state_v2 = PoolStateV2 {
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
    };

    let token_graph = TokensGraph::new(&metadata, network.clone()).unwrap();

    let mint1 = "GozPNCAseytzxCR3d2k8hTsTYkr4SDpuXy2RQAZFVx2g".to_string();
    let usd = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v".to_string();

    println!("metadata len: {}", metadata.len());
    println!("nodes: {}", token_graph.graph.node_count());
    println!("edges: {}", token_graph.graph.edge_count());

    let start = Instant::now();

    let paths = token_graph.get_filtered_paths(&mint1, &usd).unwrap();

    println!("Total time: {:?}", start.elapsed());

    println!("all paths: {:?}", paths);

}