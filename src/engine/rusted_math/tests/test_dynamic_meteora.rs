use rusted_soul_dex::smart_router::v2::manager::meteora::dlmm::swap_dynamic::*;
use rusted_soul_dex::dex::meteora::*;

use r2d2::Pool;
use r2d2_redis::RedisConnectionManager;

use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};
use r2d2_redis::redis::Commands;
use serde::Deserialize;

#[derive(Deserialize, Debug)]
struct PoolStateFor<T> {
    pool_state: HashMap<String, T>,
    ts: u64
}

fn get_dlmm_pools(con_pool: &Pool<RedisConnectionManager>) -> HashMap<String, MeteoraDlmmPool> {
    let mut con = con_pool
        .get()
        .unwrap();


    let raw_json: String = con
        .get("snapshot:state:meteora:dlmm")
        .unwrap();

    let pool_state: PoolStateFor<MeteoraDlmmPool> = serde_json::from_str(&raw_json)
        .unwrap();

    pool_state.pool_state
}

#[test]
fn test_dynamic_meteora() {
    let client = RedisConnectionManager::new("redis://127.0.0.1:6379/0").unwrap();
    let con_pool = Pool::builder()
        .max_size(20)
        .build(client)
        .unwrap();

    let dlmm_pools = get_dlmm_pools(&con_pool);

    let timestamp = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();

    // x_to_y: bool,
    // amount_specified_is_in: bool,
    // delta_amount: u128,
    // timestamp: u64,
    // meteora_dlmm_pool: &MeteoraDlmmPool

    let test_pool_1 = dlmm_pools
        .get("81GpCm4d13y8TozYtThabuSCLQN2o3bbrvDogXFPn8sA")
        .unwrap();

    let test_res_1 = swap_manager(
        true,
        true,
        30_000_000_000_000,
        timestamp,
        &test_pool_1
    );

    println!("Before: {test_pool_1:?}");
    println!("{test_res_1:?}");

    let test_pool_2 = dlmm_pools
        .get("71QNAbzXJL3tupEL3vyUKzcGLvCcAHsbYWGbK1otBe7P")
        .unwrap();

    let test_res_2 = swap_manager(
        false,
        true,
        10_000_000_000,
        timestamp,
        &test_pool_2
    );

    println!("Before: {test_pool_2:?}");
    println!("{test_res_2:?}");
}