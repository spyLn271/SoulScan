use rusted_soul_dex::smart_router::v2::manager::orca::clmm::swap_dynamic::*;
use rusted_soul_dex::dex::orca::*;

use r2d2_redis::RedisConnectionManager;
use r2d2::Pool;
use r2d2_redis::redis::Commands;

use std::collections::HashMap;
use serde::Deserialize;

use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Deserialize, Debug)]
struct PoolStateFor<T> {
    pool_state: HashMap<String, T>,
    ts: u64
}

fn get_whirlpool(con_pool: &Pool<RedisConnectionManager>) -> HashMap<String, Whirlpool> {
    let mut con = con_pool.get().unwrap();

    let raw_json: String = con
        .get("snapshot:state:orca:clmm")
        .unwrap();

    let pool_state: PoolStateFor<Whirlpool> = serde_json::from_str(&raw_json)
        .unwrap();

    pool_state.pool_state
}


#[test]
fn test_dynamic_orca_manager() {
    let client = RedisConnectionManager::new("redis://127.0.0.1:6379/0").unwrap();
    let con_pool = Pool::builder()
        .max_size(20)
        .build(client)
        .unwrap();

    let whirlpool = get_whirlpool(&con_pool);

    // x_to_y: bool,
    // amount_specified_is_in: bool,
    // delta_amount: u128,
    // timestamp: u64,
    // whirlpool: &Whirlpool

    let timestamp = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();

    // WSOL / USDC ( 9 / 6 decimals)
    let pool_test_1 = whirlpool
        .get("Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE")
        .unwrap();

    let res_test_1 = swap_manager(
        true,
        true,
        100_000_000_000,
        timestamp,
        &pool_test_1
    );

    println!("before {:?}", pool_test_1.base_info);
    println!("{res_test_1:?}");

    // cbBTC / JLP (8 / 6 decimals)
    let pool_test_2 = whirlpool
        .get("7XFiNgEcwiUUKw4GadjHv87kGSef3RKqh4TYmnkErtmB")
        .unwrap();

    let res_test_2 = swap_manager(
        false,
        true,
        100_000_000_000,
        timestamp,
        &pool_test_2
    );

    println!("before {:?}", pool_test_2.base_info);
    println!("{res_test_2:?}");

    //OOB / USDC (6 / 6 decimals)
    let pool_test_3 = whirlpool
        .get("DehSVMLfV4fjyn9JAfgvDbT9kE2t97WnGJTXFnk7EkQx")
        .unwrap();

    let res_test_3 = swap_manager(
        false,
        false,
        100_000_000_000,
        timestamp,
        &pool_test_3
    );

    println!("before {:?}", pool_test_3.base_info);
    println!("{res_test_3:?}");
}