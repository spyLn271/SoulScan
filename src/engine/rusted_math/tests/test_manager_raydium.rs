use rusted_soul_dex::smart_router::v1::manager::raydium::clmm::swap_manager::*;
use rusted_soul_dex::smart_router::v1::manager::raydium::amm::swap_manager::swap_manager as amm_swap_manager;
use rusted_soul_dex::dex::raydium::{RayAmmPool, RayClmmPool};
use rusted_soul_dex::math::raydium::clmm::calculate_swap;
use redis;
use serde::Deserialize;
use std::collections::HashMap;
use std::time::Instant;
use redis::TypedCommands;
use rusted_soul_dex::math::orca::clmm::get_lower_tick;

#[derive(Deserialize, Debug)]
struct PoolState {
    pool_state: HashMap<String, RayClmmPool>,
    ts: u64
}

#[derive(Deserialize, Debug)]
struct AmmPoolState {
    pool_state: HashMap<String, RayAmmPool>,
    ts: u64
}

fn get_ray_pool() -> PoolState {
    let client = redis::Client::open("redis://127.0.0.1:6379/0").unwrap();
    let mut conn = client.get_connection().unwrap();

    let raw_json: String = conn.get("snapshot:state:raydium:clmm").unwrap().unwrap();

    let start_time = Instant::now();

    let pool_state: PoolState = serde_json::from_str(&raw_json).unwrap();

    let elapsed = start_time.elapsed();

    println!("Total CPU Execution Time: {:?}", elapsed);

    pool_state
}

fn get_raydium_amm_pool() -> AmmPoolState {
    let client = redis::Client::open("redis://127.0.0.1:6379/0").unwrap();

    let mut con = client.get_connection().unwrap();

    let raw_json: String = con.get("snapshot:state:raydium:amm").unwrap().unwrap();

    let pool_state: AmmPoolState = serde_json::from_str(&raw_json).unwrap();

    pool_state
}

#[test]
fn test_raydium_manager() {
    let pool_state = get_ray_pool();

    let wsol_usdt_pool = pool_state.pool_state
        .get("3nMFwZXwY1s1M5s8vYAHqd4wGs4iSxXE4LRoUMMYqEgF")
        .unwrap();

    let liquidity: u128 = 72164963466389;
    let sqrt_price: u128 = 5665152880145517355;
    let current_tick = -23613;
    let boundary_tick_lower = get_lower_tick(current_tick, 1, &sqrt_price);
    let delta_amount= 10_000_000_000;
    let fee_rate = 100;

    let x_to_y_asii = calculate_swap(
        sqrt_price, boundary_tick_lower, liquidity, delta_amount,
        fee_rate, true, true
    ).unwrap();

    println!("{x_to_y_asii:?}");

    let res_total_swap = swap_manager(
        true,
        true,
        delta_amount,
        fee_rate,
        wsol_usdt_pool
    );
    println!("{res_total_swap:?}");

}


#[test]
fn test_raydium_amm_manager() {
    let pool_state = get_raydium_amm_pool();

    let pool = pool_state.pool_state
        .get("8kKGS3mBhhGMJVQfaUENRL1LMoExXF86kJZFzyNxG5Go")
        .unwrap();

    let swap_res = amm_swap_manager(
        true,
        true,
        10_000_000_000,
        400,
        pool
    );

    println!("{swap_res:?}");
}