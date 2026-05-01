use rusted_soul_dex::smart_router::v1::manager::orca::clmm::{fee_rate_manager, swap_manager};
use rusted_soul_dex::math::orca::clmm::calculate_swap as calculate_swap_orca_clmm;
use rusted_soul_dex::smart_router::v1::manager::orca::clmm::swap_manager::swap_manager;
use redis;
use serde::Deserialize;
use std::collections::HashMap;
use redis::TypedCommands;
use rusted_soul_dex::dex::orca::Whirlpool;
use std::time::Instant;
use rusted_soul_dex::math::orca::clmm::{get_lower_tick, get_upper_tick};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Deserialize, Debug)]
struct PoolState {
    pool_state: HashMap<String, Whirlpool>,
    ts: u64
}

fn get_orca_pool_state() -> PoolState {
    let client = redis::Client::open("redis://127.0.0.1:6379/0").unwrap();
    let mut con = client.get_connection().unwrap();

    let raw_json: String = con.get("snapshot:state:orca:clmm").unwrap().unwrap();

    let start_time = Instant::now();

    let pool_state: PoolState = serde_json::from_str(&raw_json).unwrap();

    let elapsed = start_time.elapsed();

    // println!("Total CPU Execution Time: {:?}", elapsed);

    pool_state
}

#[test]
fn test_swap() {
    // let sqrt_price: u128 = 257165948088673153491;
    // let current_tick: i32 = 52699;
    // let boundary_tick_lower = get_lower_tick(current_tick, 4);
    // let liquidity: u128 = 534144246188;
    // let fee_rate: u32 = 400;
    // let delta_amount = 2998979;

    // let x_to_y_asii = calculate_swap_orca_clmm(
    //     sqrt_price, boundary_tick_lower, liquidity, delta_amount,
    //     fee_rate, true, true
    // ).unwrap();
    //
    // println!("{x_to_y_asii:?}");

    let current_time = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
    let pool_state = get_orca_pool_state();

    let start_time = Instant::now();

    let res_total_swap = swap_manager(
        true,
        true,
        2000_000_000_000,
        current_time,
        &pool_state.pool_state.get("Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE").unwrap()
    );
    let elapsed = start_time.elapsed();

    println!("{res_total_swap:?}");
    println!("Total CPU Execution Time: {:?}", elapsed);
    println!("{:?}", &pool_state.pool_state.get("7XFiNgEcwiUUKw4GadjHv87kGSef3RKqh4TYmnkErtmB").unwrap())


    // let delta_y_amount_out = 1_000_000_000;
    //
    // let x_to_y_not_asii = calculate_swap_orca_clmm(
    //     sqrt_price, boundary_tick_lower, liquidity, delta_y_amount_out,
    //     fee_rate, true, false
    // ).unwrap();
    //
    // println!("{x_to_y_not_asii:?}");

    //
    // let res_total_swap = swap_manager(
    //     true,
    //     true,
    //     1_000_000_000,
    //     current_time,
    //     &pool_state.pool_state.get("7XFiNgEcwiUUKw4GadjHv87kGSef3RKqh4TYmnkErtmB").unwrap()
    // );
    //
    // let elapsed = start_time.elapsed();
    //
    // println!("{res_total_swap:?}");
    // println!("Total CPU Execution Time: {:?}", elapsed);


    //
    // let boundary_tick_upper = get_upper_tick(current_tick, 4);
    //
    // let y_to_x_asii = calculate_swap_orca_clmm(
    //     sqrt_price, boundary_tick_upper, liquidity, 30_000_000_000,
    //     fee_rate, false, true
    // ).unwrap();
    //
    // println!("{y_to_x_asii:?}");
    //
    // let y_to_x_not_asii = calculate_swap_orca_clmm(
    //     sqrt_price, boundary_tick_upper, liquidity, y_to_x_asii.amount_out,
    //     fee_rate, false, false
    // ).unwrap();
    //
    // println!("{y_to_x_not_asii:?}");
}