use std::collections::HashMap;
use r2d2::Pool;
use r2d2_redis::RedisConnectionManager;
use r2d2_redis::redis::Commands;
use serde::Deserialize;
use rusted_soul_dex::dex::metadata::{ColdPath, Metadata};
use rusted_soul_dex::dex::meteora::MeteoraDlmmPool;
use rusted_soul_dex::dex::orca::Whirlpool;
use rusted_soul_dex::dex::raydium::{RayAmmPool, RayClmmPool};
use rusted_soul_dex::smart_router::v1::router::{PoolStateV1, SmartRouterV1};
use rusted_soul_dex::smart_router::v2::router;
use rusted_soul_dex::smart_router::v2::router::SmartRouterV2;

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

fn get_metadata(pool: &Pool<RedisConnectionManager>) -> HashMap<String, Metadata> {
    let mut conn = pool.get().unwrap();


    let market_metadata_keys = [
        "snapshot:metadata:meteora:dlmm",
        "snapshot:metadata:orca:clmm",
        "snapshot:metadata:raydium:clmm",
        "snapshot:metadata:raydium:amm"
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

    let whirlpool: HashMap<String, Whirlpool> = get_pool_state(&con_pool, "snapshot:state:orca:clmm");
    let ray_clmm: HashMap<String, RayClmmPool> = get_pool_state(&con_pool, "snapshot:state:raydium:clmm");
    let ray_amm: HashMap<String, RayAmmPool> = get_pool_state(&con_pool, "snapshot:state:raydium:amm");
    let met_dlmm: HashMap<String, MeteoraDlmmPool> = get_pool_state(&con_pool, "snapshot:state:meteora:dlmm");

    let pools_state = router::PoolStateV2 {
        whirlpool: &whirlpool,
        ray_amm_pool: &ray_amm,
        ray_clmm_pool: &ray_clmm,
        meteora_dlmm_pool: &met_dlmm
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