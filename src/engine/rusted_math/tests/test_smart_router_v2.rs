use std::collections::HashMap;
use r2d2::Pool;
use r2d2_redis::RedisConnectionManager;
use r2d2_redis::redis::Commands;
use serde::Deserialize;
use rusted_soul_dex::dex::metadata::{ColdPath, Metadata};
use rusted_soul_dex::dex::meteora::MeteoraDlmmPool;
use rusted_soul_dex::dex::orca::Whirlpool;
use rusted_soul_dex::dex::raydium::{RayAmmPool, RayClmmPool};
use rusted_soul_dex::dex::uniswap::{Slot0, TickData, UniswapAmm, UniswapClmmPools};
use rusted_soul_dex::smart_router::v1::router::{PoolStateV1, SmartRouterV1};
use rusted_soul_dex::smart_router::v2::router;
use rusted_soul_dex::smart_router::v2::router::SmartRouterV2;
use std::hash::Hash;

#[derive(Deserialize, Debug)]
struct PoolStateFor<T> {
    pool_state: HashMap<String, T>,
    ts: u64
}

#[derive(Deserialize, Debug)]
#[serde(bound(deserialize = "K: Deserialize<'de> + Eq + Hash, V: Deserialize<'de>"))]
struct PoolFormat<K, V> {
    pub pool_state: HashMap<K, V>,
    pub ts: u64,
}

fn get_pool_state<T>(
    pool: &Pool<RedisConnectionManager>,
    key: &str
) -> HashMap<String, T>
where
    T: serde::de::DeserializeOwned
{
    let mut con = pool.get().unwrap();

    let raw_data: String = con.get(key).unwrap();
    let pool_state: PoolStateFor<T> = serde_json::from_str(&raw_data).unwrap();

    pool_state.pool_state
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

fn get_cold_path(pair: &str, pool: &Pool<RedisConnectionManager>) -> ColdPath {
    let mut conn = pool.get().unwrap();

    let raw_json: String = conn
        .hget("snapshot:cold_path", pair)
        .unwrap();

    let paths: ColdPath = serde_json::from_str(&raw_json).unwrap();

    paths
}

fn get_metadata(pool: &Pool<RedisConnectionManager>) -> HashMap<String, Metadata> {
    let mut conn = pool.get().unwrap();


    let market_metadata_keys = [
        "snapshot:metadata:solana:meteora:dlmm",
        "snapshot:metadata:solana:orca:clmm",
        "snapshot:metadata:solana:raydium:clmm",
        "snapshot:metadata:solana:raydium:amm",
        "snapshot:metadata:eth:uniswap:v3",
        "snapshot:metadata:eth:uniswap:v4",
    ];

    let mut metadata: HashMap<String, Metadata> = HashMap::new();

    for key in market_metadata_keys {
        let raw_json: String = conn.get(key).unwrap();
        let market_metadata: HashMap<String, Metadata> = serde_json::from_str(&raw_json).unwrap();
        metadata.extend(market_metadata);
    }


    metadata
}


#[test]
fn test_smart_router() {
    /*
    Bases to test:
        SOL(So11111111111111111111111111111111111111112)


    Quotes to test:
        USDC(EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v)
    */


    let client = RedisConnectionManager::new("redis://127.0.0.1:6379/0").unwrap();
    let con_pool = Pool::builder()
        .max_size(20)
        .build(client)
        .unwrap();

    let whirlpool: HashMap<String, Whirlpool> = get_pool_state(&con_pool, "snapshot:state:solana:orca:clmm");
    let ray_clmm: HashMap<String, RayClmmPool> = get_pool_state(&con_pool, "snapshot:state:solana:raydium:clmm");
    let ray_amm: HashMap<String, RayAmmPool> = get_pool_state(&con_pool, "snapshot:state:solana:raydium:amm");
    let met_dlmm: HashMap<String, MeteoraDlmmPool> = get_pool_state(&con_pool, "snapshot:state:solana:meteora:dlmm");
    let uni_amm: HashMap<String, UniswapAmm> = get_pool_state(&con_pool, "snapshot:state:eth:uniswap:v2");

    let uni_clmm_slot_v3 = get_state_slot0s(
        &con_pool,
        &"eth".to_string(),
        &"uniswap".to_string(),
        &"v3".to_string()
    );
    let uni_clmm_slot_v4 = get_state_slot0s(
        &con_pool,
        &"eth".to_string(),
        &"uniswap".to_string(),
        &"v4".to_string()
    );

    let uni_clmm_tick_v3 = get_ticks(
        &con_pool,
        &"eth".to_string(),
        &"uniswap".to_string(),
        &"v3".to_string()
    );

    let uni_clmm_tick_v4 = get_ticks(
        &con_pool,
        &"eth".to_string(),
        &"uniswap".to_string(),
        &"v4".to_string()
    );

    let mut slot0s = uni_clmm_slot_v3;
    slot0s.extend(uni_clmm_slot_v4);

    let mut ticks = uni_clmm_tick_v3;
    ticks.extend(uni_clmm_tick_v4);


    let uni_clmm = UniswapClmmPools {
        slot0s,
        ticks
    };



    let pools_state = router::PoolStateV2 {
        whirlpool: &whirlpool,
        ray_amm_pool: &ray_amm,
        ray_clmm_pool: &ray_clmm,
        meteora_dlmm_pool: &met_dlmm,
        uni_clmm_pool: &uni_clmm,
        uni_amm_pool: &uni_amm
    };

    let pool_state = PoolStateV1 {
        whirlpool: &whirlpool,
        meteora_dlmm_pool: &met_dlmm,
        ray_amm_pool: &ray_amm,
        ray_clmm_pool: &ray_clmm
    };

    let metadata = get_metadata(&con_pool);

    let smart_router_v2 = SmartRouterV2::new(
        &metadata,
        &pools_state,
        &con_pool
    );

    let smart_router_v1 = SmartRouterV1 {
        pool_state: &pool_state,
        metadata: &metadata,
        redis_pool_connection: &con_pool
    };

    let res_v2 = smart_router_v2.smart_router(
        "So11111111111111111111111111111111111111112",
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        124_186_887_459,
        true,
        true
    );

    println!("{res_v2:?}");

    let res_v1 = smart_router_v1.smart_router(
        "So11111111111111111111111111111111111111112",
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        99_980_000_000_000,
        true,
        true
    );
    println!("{res_v1:?}");

    let res_1_v2 = smart_router_v2.smart_router(
        "So11111111111111111111111111111111111111112",
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        100_000_000_000,
        false,
        false
    );

    println!("{res_1_v2:?}");

    let res_2_v2 = smart_router_v2.smart_router(
        "So11111111111111111111111111111111111111112",
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        8052_261_348,
        false,
        true
    );

    println!("{res_2_v2:?}");
}