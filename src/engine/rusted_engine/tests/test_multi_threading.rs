use std::collections::BTreeMap;
use std::sync::Arc;
use evmap;
use std::thread;
use r2d2::Pool;
use r2d2_redis::RedisConnectionManager;
use rusted_engine::api::dex::snapshot::{StateViewer, get_metadata, get_metadata_for_network};
use rusted_soul_dex::smart_router::v2::router::{SmartRouterV2, PoolStateV2};
use rusted_soul_dex::dex::uniswap::{UniswapClmmPools, UniswapAmm};
use rusted_soul_dex::dex::meteora::MeteoraDlmmPool;
use rusted_soul_dex::dex::raydium::{RayClmmPool, RayAmmPool};
use rusted_soul_dex::dex::orca::Whirlpool;
use rusted_soul_dex::dex::metadata::Metadata;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum DataV2 {
    PoolState(PoolStateV2),
    Metadata(BTreeMap<String, Metadata>)
}

#[test]
fn test_threading() {
    let client = RedisConnectionManager::new("redis://127.0.0.1:6379/0").unwrap();
    let redis_conn_pool = Pool::builder()
        .max_size(10)
        .build(client)
        .unwrap();

    let (mut write, reader) = unsafe {
        evmap::new_assert_stable::<&'static str, DataV2>()
    };

    let whirlpools = Whirlpool::get_state_snapshot(
        &redis_conn_pool,
        "solana",
        false
    );

    let meteora_dlmm = MeteoraDlmmPool::get_state_snapshot(
        &redis_conn_pool,
        "solana",
        false
    );

    let raydium_amm = RayAmmPool::get_state_snapshot(
        &redis_conn_pool,
        "solana",
        false
    );

    let raydium_clmm = RayClmmPool::get_state_snapshot(
        &redis_conn_pool,
        "solana",
        false
    );

    let uni_amm = UniswapAmm::get_state_snapshot(
        &redis_conn_pool,
        "eth",
        false
    );

    let uni_clmm = UniswapClmmPools::get_state_snapshot(
        &redis_conn_pool,
        "eth",
        false
    );

    let metadata = get_metadata_for_network(&redis_conn_pool, "solana").unwrap();

    write.insert(
        "state",
        DataV2::PoolState(
            PoolStateV2 {
                whirlpool: Arc::new(whirlpools.unwrap()),
                meteora_dlmm_pool: Arc::new(meteora_dlmm.unwrap()),
                ray_amm_pool: Arc::new(raydium_amm.unwrap()),
                ray_clmm_pool: Arc::new(raydium_clmm.unwrap()),
                uni_amm_pool: Arc::new(uni_amm.unwrap()),
                uni_clmm_pool: Arc::new(uni_clmm.unwrap()),
            }
        )
    );

    write.insert(
        "metadata",
        DataV2::Metadata(
            metadata
        )
    );

    write.publish();


    let handles: Vec<_> = (0..4).map(|_| {
        let reader_inner = reader.clone();

        thread::spawn(move || {
            let data=reader_inner.get("state").unwrap();
            let a = data.get_one().unwrap();
            println!("thread spawned");
            // println!("{:?}", a..get("Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE").unwrap().base_info);
            match a {
                DataV2::PoolState(pool_state) => {
                    println!("{:?}", pool_state.whirlpool.get("Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE").unwrap().base_info);
                },
                DataV2::Metadata(metadata) => {
                    println!("{:?}", metadata.get("3nMFwZXwY1s1M5s8vYAHqd4wGs4iSxXE4LRoUMMYqEgF"));
                }
            }

            let metadata = reader_inner.get("metadata").unwrap();
            let b = metadata.get_one().unwrap();
            match b {
                DataV2::PoolState(pool_state) => {
                    println!("{:?}", pool_state.whirlpool.get("Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE").unwrap().base_info);
                },
                DataV2::Metadata(metadata) => {
                    println!("{:?}", metadata.get("3nMFwZXwY1s1M5s8vYAHqd4wGs4iSxXE4LRoUMMYqEgF"));
                }
            }
            10
        })
    }).collect();

    for value in handles {
        value.join().unwrap();
    }
}