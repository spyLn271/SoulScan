use std::collections::HashMap;
use r2d2::Pool;
use r2d2_redis::redis::Commands;
use rusted_soul_dex::smart_router::v1::router::*;
use redis;
use redis::TypedCommands;
use r2d2_redis::RedisConnectionManager;
use serde::Deserialize;
use rusted_soul_dex::dex::metadata::{Metadata, ColdPath};

#[derive(Deserialize, Debug)]
struct PoolStateFor<T> {
    pool_state: HashMap<String, T>,
    ts: u64
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

fn get_cold_path(pair: &str, pool: &Pool<RedisConnectionManager>) -> ColdPath {
    let mut conn = pool.get().unwrap();

    let raw_json: String = conn
        .hget("snapshot:cold_path", pair)
        .unwrap();

    let paths: ColdPath = serde_json::from_str(&raw_json).unwrap();

    paths
}

fn get_metadata() -> HashMap<String, Metadata> {
    let client = redis::Client::open("redis://127.0.0.1:6379/0").unwrap();
    let mut conn = client.get_connection().unwrap();


    let market_metadata_keys = [
        "snapshot:metadata:solana:meteora:dlmm",
        "snapshot:metadata:solana:orca:clmm",
        "snapshot:metadata:solana:raydium:clmm",
        "snapshot:metadata:solana:raydium:amm"
    ];

    let mut metadata: HashMap<String, Metadata> = HashMap::new();

    for key in market_metadata_keys {
        let raw_json = conn.get(key).unwrap().unwrap();
        let market_metadata: HashMap<String, Metadata> = serde_json::from_str(&raw_json).unwrap();
        metadata.extend(market_metadata);
    }


    metadata
}


#[test]
fn test_smart_router() {
    let client = RedisConnectionManager::new("redis://127.0.0.1:6379/0").unwrap();
    let pool = Pool::builder()
        .max_size(20)
        .build(client)
        .unwrap();

    let whirlpool = get_pool_state(&pool, "snapshot:state:orca:clmm");
    let ray_clmm = get_pool_state(&pool, "snapshot:state:raydium:clmm");
    let ray_amm = get_pool_state(&pool, "snapshot:state:raydium:amm");
    let met_dlmm = get_pool_state(&pool, "snapshot:state:meteora:dlmm");

    let pool_state = PoolStateV1 {
        whirlpool: &whirlpool,
        meteora_dlmm_pool: &met_dlmm,
        ray_amm_pool: &ray_amm,
        ray_clmm_pool: &ray_clmm
    };

    let metadata = get_metadata();

    let smart_router_v1 = SmartRouterV1 {
        pool_state: &pool_state,
        metadata: &metadata,
        redis_pool_connection: &pool
    };

    let res = smart_router_v1.smart_router(
        "So11111111111111111111111111111111111111112",
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        1000_000_000_000,
        true,
        true
    );

    println!("{res:?}");

    let res_1 = smart_router_v1.smart_router(
        "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN",
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        1000_000_000_000,
        true,
        true
    );

    println!("{res_1:?}");
}
