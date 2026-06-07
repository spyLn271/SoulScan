use r2d2_redis::RedisConnectionManager;
use r2d2::Pool;
use rusted_soul_dex::dex::meteora::MeteoraDlmmPool;
use rusted_soul_dex::dex::orca::Whirlpool;
use rusted_soul_dex::dex::raydium::{RayAmmPool, RayClmmPool};
use rusted_soul_dex::dex::uniswap::{UniswapAmm, UniswapClmmPools};
use rusted_engine::api::dex::snapshot::*;

#[test]
fn test_metadata() {
    let client = RedisConnectionManager::new("redis://127.0.0.1:6379/0").unwrap();
    let redis_conn_pool = Pool::builder()
        .max_size(10)
        .build(client)
        .unwrap();


    let eth_uni_v3_metadata = get_metadata(
        &redis_conn_pool,
        "solana",
        "uniswap",
        "v4"
    );

    // println!("{:?}", eth_uni_v3_metadata);

    let eth_addresses = get_token_addresses(
        &redis_conn_pool,
        "eth"
    );

    // println!("{:?}", eth_addresses);

    // let meteora_pool_state = MeteoraDlmmPool::get_state_snapshot(
    //     &redis_conn_pool,
    //     "solana",
    //     false
    // );
    //
    // println!("{:?}", meteora_pool_state);

    // let ray_amm_pool_state = RayAmmPool::get_state_snapshot(
    //     &redis_conn_pool,
    //     "solana",
    //     true
    // );
    // println!("{:?}", ray_amm_pool_state);

    // let ray_clmm_pool_state = RayClmmPool::get_state_snapshot(
    //     &redis_conn_pool,
    //     "solana",
    //     true
    // );
    // println!("{:?}", ray_clmm_pool_state);

    // let orca_pool_state = Whirlpool::get_state_snapshot(
    //     &redis_conn_pool,
    //     "solana",
    //     true
    // );
    // println!("{:?}", orca_pool_state);

    // let uniswap_amm_pool_state = UniswapAmm::get_state_snapshot(
    //     &redis_conn_pool,
    //     "base",
    //     false
    // );
    // println!("{:?}", uniswap_amm_pool_state);

    let uniswap_clmm_pool_state = UniswapClmmPools::get_state_snapshot(
        &redis_conn_pool,
        "base",
        false
    ).unwrap();

    println!("{:?}", uniswap_clmm_pool_state.slot0s);

    // let network_metadata = get_metadata_for_network(
    //     &redis_conn_pool,
    //     "solana",
    // );
    //
    // println!("network_metadata: {:?}", network_metadata);
}
