use std::collections::BTreeMap;
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
use std::sync::Arc;

#[derive(Deserialize, Debug)]
struct PoolStateFor<T> {
    pool_state: BTreeMap<String, T>,
    ts: u64
}

#[derive(Deserialize, Debug)]
#[serde(bound(deserialize = "K: Deserialize<'de> + Eq + Ord, V: Deserialize<'de>"))]
struct PoolFormat<K, V> {
    pub pool_state: BTreeMap<K, V>,
    pub ts: u64,
}

fn get_pool_state<T>(
    pool: &Pool<RedisConnectionManager>,
    key: &str
) -> BTreeMap<String, T>
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
) -> BTreeMap<String, UniswapAmm> {
    let mut redis_con = redis_pool_con.get().unwrap();

    let raw_json: String = redis_con.get(
        format!("snapshot:state:{}:{}:v2", network, market)
    ).unwrap();

    let pool_form: PoolFormat<String, UniswapAmm> = serde_json::from_str(&raw_json).unwrap();

    let state_amm: BTreeMap<String, UniswapAmm> = pool_form.pool_state;

    state_amm
}

fn get_state_slot0s(
    redis_pool_con: &Pool<RedisConnectionManager>,
    network: &String,
    market: &String,
    version: &String
) -> BTreeMap<String, Slot0> {
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
) -> BTreeMap<String, BTreeMap<i32, TickData>> {

    let mut redis_con = redis_pool_con.get().unwrap();

    let raw_json: String = redis_con.hget(
        format!("snapshot:state:{}:{}:{}", network, market, version),
        "ticks"
    ).unwrap();

    let pool_form: PoolFormat<String, BTreeMap<i32, TickData>> = serde_json::from_str(&raw_json).unwrap();

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

fn get_metadata(pool: &Pool<RedisConnectionManager>) -> BTreeMap<String, Metadata> {
    let mut conn = pool.get().unwrap();


    let market_metadata_keys = [
        "snapshot:metadata:solana:meteora:dlmm",
        "snapshot:metadata:solana:orca:clmm",
        "snapshot:metadata:solana:raydium:clmm",
        "snapshot:metadata:solana:raydium:amm",
        "snapshot:metadata:eth:uniswap:v3",
        "snapshot:metadata:eth:uniswap:v4",
        "snapshot:metadata:eth:uniswap:v2",
    ];

    let mut metadata: BTreeMap<String, Metadata> = BTreeMap::new();

    for key in market_metadata_keys {
        let raw_json: String = conn.get(key).unwrap();
        let market_metadata: BTreeMap<String, Metadata> = serde_json::from_str(&raw_json).unwrap();
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

    let whirlpool: BTreeMap<String, Whirlpool> = get_pool_state(&con_pool, "snapshot:state:solana:orca:clmm");
    let ray_clmm: BTreeMap<String, RayClmmPool> = get_pool_state(&con_pool, "snapshot:state:solana:raydium:clmm");
    let ray_amm: BTreeMap<String, RayAmmPool> = get_pool_state(&con_pool, "snapshot:state:solana:raydium:amm");
    let met_dlmm: BTreeMap<String, MeteoraDlmmPool> = get_pool_state(&con_pool, "snapshot:state:solana:meteora:dlmm");
    let uni_amm: BTreeMap<String, UniswapAmm> = get_pool_state(&con_pool, "snapshot:state:eth:uniswap:v2");

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



    let pools_state_v2 = router::PoolStateV2 {
        whirlpool: Arc::new(whirlpool),
        ray_amm_pool: Arc::new(ray_amm),
        ray_clmm_pool: Arc::new(ray_clmm),
        meteora_dlmm_pool: Arc::new(met_dlmm),
        uni_clmm_pool: Arc::new(uni_clmm),
        uni_amm_pool: Arc::new(uni_amm),
    };

    let pool_state_v1 = PoolStateV1 {
        whirlpool: Arc::clone(&pools_state_v2.whirlpool),
        meteora_dlmm_pool: Arc::clone(&pools_state_v2.meteora_dlmm_pool),
        ray_amm_pool: Arc::clone(&pools_state_v2.ray_amm_pool),
        ray_clmm_pool: Arc::clone(&pools_state_v2.ray_clmm_pool),
    };

    let metadata = get_metadata(&con_pool);

    let mut smart_router_v2 = SmartRouterV2::new(
        &metadata,
        &pools_state_v2,
        &con_pool
    );

    let smart_router_v1 = SmartRouterV1 {
        pool_state: &pool_state_v1,
        metadata: &metadata,
        redis_pool_connection: &con_pool
    };

    let res_v2 = smart_router_v2.smart_router(
        "So11111111111111111111111111111111111111112",
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        10000000000000,
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

    let res_v2_clone = smart_router_v2.smart_router(
        "So11111111111111111111111111111111111111112",
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        10000000000000,
        true,
        true
    );

    println!("{res_v2_clone:?}");

    println!("{res_1_v2:?}");

    let res_2_v2 = smart_router_v2.smart_router(
        "So11111111111111111111111111111111111111112",
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        8052_261_348,
        false,
        true
    );

    println!("{res_2_v2:?}");

    let res_eth_v2 = smart_router_v2.smart_router(
        "0xf19304e6bfe0a18d2a0171758aa433921f192897",
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        1000000000000000000,
        true,
        true
    );

    println!("{res_eth_v2:?}");
    println!("{:?}", smart_router_v2.metadata.get("0xab905aba2cf13128f1233f68800d85a275eddbcf"));
    println!("{:?}", smart_router_v2.metadata.get("3nMFwZXwY1s1M5s8vYAHqd4wGs4iSxXE4LRoUMMYqEgF"));
}

#[test]
fn test_cold_path() {
    let client = RedisConnectionManager::new("redis://127.0.0.1:6379/0").unwrap();
    let con_pool = Pool::builder()
        .max_size(20)
        .build(client)
        .unwrap();


    let cold_path = get_cold_path(
        "0xf19304e6bfe0a18d2a0171758aa433921f192897/0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        &con_pool
    );

    println!("{:?}", cold_path);
}