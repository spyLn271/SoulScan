/*
REDIS_METADATA_KEY = 'snapshot:metadata:%s:%s:%s'  # network, market and version
POOLS_STATE_DICT_REDIS_KEY = 'snapshot:state:%s:%s:%s'  # network, market and version
REDIS_KEY_COLD_PATH = "snapshot:cold_path"
REDIS_DEX_MINTS = "snapshot:addresses:%s" # network
*/
use r2d2_redis::RedisConnectionManager;
use r2d2::Pool;
use r2d2_redis::redis::Commands;

use std::collections::HashMap;
use std::hash::Hash;
use std::ops::Shr;
use rusted_soul_dex::dex::metadata::Metadata;
use rusted_soul_dex::dex::uniswap::{Slot0, TickData, UniswapAmm, UniswapClmm};
use rusted_soul_dex::math::uniswap::clmm;

use serde::Deserialize;
use rusted_soul_dex::math::i256::I256;
use rusted_soul_dex::math::u256::U256;
use rusted_soul_dex::math::u512::U512;

use rusted_soul_dex::smart_router::v2::manager::uniswap::clmm::swap_dynamic;

#[derive(Deserialize, Debug)]
#[serde(bound(deserialize = "K: Deserialize<'de> + Eq + Hash, V: Deserialize<'de>"))]
struct PoolFormat<K, V> {
    pub pool_state: HashMap<K, V>,
    pub ts: u64,
}

fn get_metadata(
    redis_pool_con: &Pool<RedisConnectionManager>,
    network: &String,
    market: &String,
    version: &String
) -> HashMap<String, Metadata>{
    let mut redis_con = redis_pool_con.get().unwrap();

    let raw_json: String = redis_con.get(
        format!("snapshot:metadata:{}:{}:{}", network, market, version)
    ).unwrap();

    let metadata: HashMap<String, Metadata> = serde_json::from_str(&raw_json).unwrap();

    metadata
}

fn get_state_amm(
    redis_pool_con: &Pool<RedisConnectionManager>,
    network: &String,
    market: &String,
) -> HashMap<String, UniswapAmm> {
    let mut redis_con = redis_pool_con.get().unwrap();

    let raw_json: String = redis_con.get(
        format!("snapshot:state:{}:{}:v2", network, market)
    ).unwrap();

    let pool_form: PoolFormat<String, UniswapAmm> = serde_json::from_str(&raw_json).unwrap();

    let state_amm: HashMap<String, UniswapAmm> = pool_form.pool_state;

    state_amm
}

fn get_state_slot0s(
    redis_pool_con: &Pool<RedisConnectionManager>,
    network: &String,
    market: &String,
    version: &String
) -> HashMap<String, Slot0> {
    let mut redis_con = redis_pool_con.get().unwrap();

    let raw_json: String = redis_con.hget(
        format!("snapshot:state:{}:{}:{}", network, market, version),
        "slot"
    ).unwrap();

    let pool_form: PoolFormat<String, Slot0> = serde_json::from_str(&raw_json)
        .unwrap();

    let slot0s = pool_form.pool_state;

    slot0s
}

fn get_ticks(
    redis_pool_con: &Pool<RedisConnectionManager>,
    network: &String,
    market: &String,
    version: &String
) -> HashMap<String, HashMap<i32, TickData>> {

    let mut redis_con = redis_pool_con.get().unwrap();

    let raw_json: String = redis_con.hget(
        format!("snapshot:state:{}:{}:{}", network, market, version),
        "ticks"
    ).unwrap();

    let pool_form: PoolFormat<String, HashMap<i32, TickData>> = serde_json::from_str(&raw_json).unwrap();

    let ticks = pool_form.pool_state;

    ticks
}


fn test_data() {
    let redis_client = RedisConnectionManager::new("redis://127.0.0.1:6379/0")
        .unwrap();

    let redis_pool_con = Pool::builder()
        .max_size(10)
        .build(redis_client)
        .unwrap();

    let network = "eth".to_string();
    let market = "uniswap".to_string();
    let version = "v3".to_string();

    let metadata = get_metadata(
        &redis_pool_con,
        &network,
        &market,
        &version
    );

    println!("{:?}", metadata.get("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"));

    let slot0s = get_state_slot0s(
        &redis_pool_con,
        &network,
        &market,
        &version
    );

    let ticks = get_ticks(
        &redis_pool_con,
        &network,
        &market,
        &version
    );

    //tick_current: 199461

    let pool1_slot0 = slot0s.get("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640").unwrap();
    let pool1_tick = ticks.get("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640").unwrap();


    println!("{:?}", slot0s.get("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"));
    println!("{:?}", ticks.get("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"));

    let sqrt_price_0 = pool1_slot0.sqrt_price_x96;
    let sqrt_price_1 = clmm::sqrt_price_from_tick_index(199464).unwrap();
    let liquidity = pool1_slot0.liquidity;

    let delta_x = clmm::get_amount_x(&sqrt_price_0, &sqrt_price_1, &liquidity, false)
        .unwrap();
    let delta_y = clmm::get_amount_y(&sqrt_price_0, &sqrt_price_1, &liquidity, false)
        .unwrap();

    println!("{:?}", delta_x);
    println!("{:?}", delta_y);

    let sqrt_end_with_x = clmm::get_sqrt_price_from_x(
        &sqrt_price_0, &liquidity, delta_x, true, false
    ).unwrap();

    let sqrt_end_with_y = clmm::get_sqrt_price_from_y(
        &sqrt_price_0, &liquidity, delta_y, true, false
    ).unwrap();

    println!("{:?}", sqrt_price_1);

    println!("{:?}", sqrt_end_with_x);
    println!("{:?}", sqrt_end_with_y);

    let delta_x = clmm::get_amount_x(&sqrt_price_0, &sqrt_end_with_x, &liquidity, false)
        .unwrap();
    let delta_y = clmm::get_amount_y(&sqrt_price_0, &sqrt_end_with_y, &liquidity, false)
        .unwrap();

    println!("{:?}", delta_x);
    println!("{:?}", delta_y);

    let res = clmm::calculate_swap(
        sqrt_price_0,
        199456,
        liquidity,
        5000000000,
        400,
        true,
        true
    );

    println!("{:?}", res);

}

fn test_manager() {
    let redis_client = RedisConnectionManager::new("redis://127.0.0.1:6379/0")
        .unwrap();

    let redis_pool_con = Pool::builder()
        .max_size(10)
        .build(redis_client)
        .unwrap();

    let network = "eth".to_string();
    let market = "uniswap".to_string();
    let version = "v3".to_string();

    let metadata = get_metadata(
        &redis_pool_con,
        &network,
        &market,
        &version
    );

    let slot0s = get_state_slot0s(
        &redis_pool_con,
        &network,
        &market,
        &version
    );

    let ticks = get_ticks(
        &redis_pool_con,
        &network,
        &market,
        &version
    );

    let pool1_slot0 = slot0s.get("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640").unwrap();
    let pool1_tick = ticks.get("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640").unwrap();

    let res_1 = swap_dynamic::swap_manager(
        true,
        false,
        2044382913026368485478,
        500,
        10,
        &UniswapClmm {
            slot0: pool1_slot0.clone(),
            tick: pool1_tick.clone()
        }
    );

    println!("{res_1:?}");
}

fn test_sqrt_price_from_tick_index(tick: i32) {
    let sqrt_price = clmm::sqrt_price_from_tick_index(tick).unwrap();

    println!("{sqrt_price:?}");
}


#[test]
fn main_test() {
    test_manager()
}