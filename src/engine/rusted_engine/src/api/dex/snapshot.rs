use std::collections::BTreeMap;
use std::time;
use std::time::UNIX_EPOCH;
use std::sync::Arc;

use r2d2::Pool;
use r2d2_redis::redis::Commands;
use r2d2_redis::RedisConnectionManager;

use serde::Deserialize;

use rusted_soul_dex::dex::metadata::Metadata;
use rusted_soul_dex::dex::meteora::MeteoraDlmmPool;
use rusted_soul_dex::dex::orca::Whirlpool;
use rusted_soul_dex::dex::raydium::{RayAmmPool, RayClmmPool};
use rusted_soul_dex::dex::uniswap::{UniswapClmmPools, UniswapAmm, Slot0, TickData};
use rusted_soul_dex::smart_router::v2::router::PoolStateV2;
use crate::errors::SoulEngineErrors;
use crate::config::{
    SUPPORTED_NETWORK_LIST,
    MARKETS_SUPPORTED_IN_NETWORK,
    POOL_STATE_DECAY,
    POOL_TICK_DATA_DECAY,
    Market,
    Version
};

#[derive(Deserialize, Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct TokenData {
    pub decimals: u32
}

pub fn get_token_addresses(
    redis_conn_pool: &Pool<RedisConnectionManager>,
    network: &str,
) -> Result<BTreeMap<usize, (String, TokenData)>, SoulEngineErrors> {
    if !SUPPORTED_NETWORK_LIST.contains(&network) {
        return Err(SoulEngineErrors::NotSupportedNetwork);
    }

    let mut conn = redis_conn_pool.get()?;

    let key_to_tokens_list: String = format!("snapshot:addresses:{}", network);

    let raw_token_list: String = conn.get(&key_to_tokens_list)?;

    let tokens: BTreeMap<String, TokenData> = serde_json::from_str(&raw_token_list)?;
    
    let mut token_list: BTreeMap<usize, (String, TokenData)> = BTreeMap::new();
    
    for (idx, (address, token_data)) in tokens.into_iter().enumerate() {
        token_list.insert(idx, (address, token_data));
    }
    

    Ok(token_list)
}


pub fn get_metadata(
    redis_conn_pool: &Pool<RedisConnectionManager>,
    network: &str,
    market: &str,
    version: &str,
) -> Result<BTreeMap<String, Metadata>, SoulEngineErrors> {
    let markets_supported_in_network: &Vec<(&Market, &Version)> = MARKETS_SUPPORTED_IN_NETWORK
        .get(&network)
        .ok_or(SoulEngineErrors::NotSupportedNetwork)?;

    if !markets_supported_in_network.contains(&(market, version)) {
        return Err(SoulEngineErrors::NotSupportedMarket);
    }

    let mut conn = redis_conn_pool.get()?;

    let key_to_metadata: String = format!("snapshot:metadata:{}:{}:{}", network, market, version);

    let raw_metadata: String = conn.get(&key_to_metadata)?;

    let metadata: BTreeMap<String, Metadata> = serde_json::from_str(&raw_metadata)?;

    Ok(metadata)
}

pub fn get_metadata_for_network(
    redis_conn_pool: &Pool<RedisConnectionManager>,
    network: &str,
) -> Result<BTreeMap<String, Metadata>, SoulEngineErrors> {
    if !SUPPORTED_NETWORK_LIST.contains(&network) {
        return Err(SoulEngineErrors::NotSupportedNetwork);
    }

    let mut conn = redis_conn_pool.get()?;

    let mut pipe = r2d2_redis::redis::pipe();

    let markets = MARKETS_SUPPORTED_IN_NETWORK
        .get(&network)
        .ok_or(SoulEngineErrors::NotSupportedNetwork)?;

    for (market, version) in markets {
        let key_to_metadata: String = format!("snapshot:metadata:{}:{}:{}", network, market, version);
        pipe.get(&key_to_metadata);
    }

    let raw_metadata: Vec<String> = pipe.query(&mut *conn)?;

    let mut metadata: BTreeMap<String, Metadata> = BTreeMap::new();

    for raw_md in raw_metadata {
        let md: BTreeMap<String, Metadata> = serde_json::from_str(&raw_md)?;
        metadata.extend(md);
    }

    Ok(metadata)
}

pub trait StateViewer {
    type State;
    const REDIS_SNAPSHOT_KEY: &str = "snapshot:state:{network}:{market}:{version}";

    fn get_state_snapshot(
        redis_conn_pool: &Pool<RedisConnectionManager>,
        network: &str,
        check_for_freshness: bool
    ) -> Result<Self::State, SoulEngineErrors>;
}

#[derive(Deserialize, Debug)]
#[serde(bound(deserialize = "K: Deserialize<'de> + Eq + Ord, V: Deserialize<'de>"))]
pub struct PoolSnapshot<K, V> {
    pub pool_state: BTreeMap<K, V>,
    pub ts: u64,
}

impl StateViewer for MeteoraDlmmPool {
    type State = BTreeMap<String, MeteoraDlmmPool>;

    fn get_state_snapshot(
        redis_conn_pool: &Pool<RedisConnectionManager>,
        network: &str,
        check_for_freshness: bool
    ) -> Result<Self::State, SoulEngineErrors> {
        if !SUPPORTED_NETWORK_LIST.contains(&network) {
            return Err(SoulEngineErrors::NotSupportedNetwork);
        }

        let mut conn = redis_conn_pool.get()?;

        let key_to_snapshot: String = Self::REDIS_SNAPSHOT_KEY
            .replace("{network}", network)
            .replace("{market}", "meteora")
            .replace("{version}", "dlmm");

        let raw_snapshot: String = conn.get(&key_to_snapshot)?;

        let snapshot: PoolSnapshot<String, MeteoraDlmmPool> = serde_json::from_str(&raw_snapshot)?;

        if check_for_freshness {
            let current_ts: u64 = time::SystemTime::now()
                .duration_since(UNIX_EPOCH)?
                .as_secs();

            if current_ts - snapshot.ts > POOL_STATE_DECAY {
                return Err(SoulEngineErrors::StalePoolStateData)
            }
        }

        Ok(snapshot.pool_state)
    }
}

impl StateViewer for RayAmmPool {
    type State = BTreeMap<String, RayAmmPool>;

    fn get_state_snapshot(
        redis_conn_pool: &Pool<RedisConnectionManager>,
        network: &str,
        check_for_freshness: bool
    ) -> Result<Self::State, SoulEngineErrors> {
        if !SUPPORTED_NETWORK_LIST.contains(&network) {
            return Err(SoulEngineErrors::NotSupportedNetwork);
        }

        let mut conn = redis_conn_pool.get()?;

        let key_to_snapshot: String = Self::REDIS_SNAPSHOT_KEY
            .replace("{network}", network)
            .replace("{market}", "raydium")
            .replace("{version}", "amm");

        let raw_snapshot: String = conn.get(&key_to_snapshot)?;

        let snapshot: PoolSnapshot<String, RayAmmPool> = serde_json::from_str(&raw_snapshot)?;

        if check_for_freshness {
            let current_ts: u64 = time::SystemTime::now()
                .duration_since(UNIX_EPOCH)?
                .as_secs();

            if current_ts - snapshot.ts > POOL_STATE_DECAY {
                return Err(SoulEngineErrors::StalePoolStateData)
            }
        }

        Ok(snapshot.pool_state)
    }
}

impl StateViewer for RayClmmPool {
    type State = BTreeMap<String, RayClmmPool>;

    fn get_state_snapshot(
        redis_conn_pool: &Pool<RedisConnectionManager>,
        network: &str,
        check_for_freshness: bool
    ) -> Result<Self::State, SoulEngineErrors> {
        if !SUPPORTED_NETWORK_LIST.contains(&network) {
            return Err(SoulEngineErrors::NotSupportedNetwork);
        }

        let mut conn = redis_conn_pool.get()?;

        let key_to_snapshot: String = Self::REDIS_SNAPSHOT_KEY
            .replace("{network}", network)
            .replace("{market}", "raydium")
            .replace("{version}", "clmm");

        let raw_snapshot: String = conn.get(&key_to_snapshot)?;

        let snapshot: PoolSnapshot<String, RayClmmPool> = serde_json::from_str(&raw_snapshot)?;

        if check_for_freshness {
            let current_ts: u64 = time::SystemTime::now()
                .duration_since(UNIX_EPOCH)?
                .as_secs();

            if current_ts - snapshot.ts > POOL_STATE_DECAY {
                return Err(SoulEngineErrors::StalePoolStateData)
            }
        }

        Ok(snapshot.pool_state)
    }
}

impl StateViewer for Whirlpool {
    type State = BTreeMap<String, Whirlpool>;

    fn get_state_snapshot(
        redis_conn_pool: &Pool<RedisConnectionManager>,
        network: &str,
        check_for_freshness: bool
    ) -> Result<Self::State, SoulEngineErrors> {
        if !SUPPORTED_NETWORK_LIST.contains(&network) {
            return Err(SoulEngineErrors::NotSupportedNetwork);
        }

        let mut conn = redis_conn_pool.get()?;

        let key_to_snapshot: String = Self::REDIS_SNAPSHOT_KEY
            .replace("{network}", network)
            .replace("{market}", "orca")
            .replace("{version}", "clmm");

        let raw_snapshot: String = conn.get(&key_to_snapshot)?;

        let snapshot: PoolSnapshot<String, Whirlpool> = serde_json::from_str(&raw_snapshot)?;

        if check_for_freshness {
            let current_ts: u64 = time::SystemTime::now()
                .duration_since(UNIX_EPOCH)?
                .as_secs();

            if current_ts - snapshot.ts > POOL_STATE_DECAY {
                return Err(SoulEngineErrors::StalePoolStateData)
            }
        }

        Ok(snapshot.pool_state)
    }
}

impl StateViewer for UniswapAmm {
    type State = BTreeMap<String, UniswapAmm>;

    fn get_state_snapshot(
        redis_conn_pool: &Pool<RedisConnectionManager>,
        network: &str,
        check_for_freshness: bool
    ) -> Result<Self::State, SoulEngineErrors> {
        if !SUPPORTED_NETWORK_LIST.contains(&network) {
            return Err(SoulEngineErrors::NotSupportedNetwork);
        }

        let mut conn = redis_conn_pool.get()?;

        let key_to_snapshot: String = Self::REDIS_SNAPSHOT_KEY
            .replace("{network}", network)
            .replace("{market}", "uniswap")
            .replace("{version}", "v2");

        let raw_snapshot: String = conn.get(&key_to_snapshot)?;

        let snapshot: PoolSnapshot<String, UniswapAmm> = serde_json::from_str(&raw_snapshot)?;

        if check_for_freshness {
            let current_ts: u64 = time::SystemTime::now()
                .duration_since(UNIX_EPOCH)?
                .as_secs();

            if current_ts - snapshot.ts > POOL_STATE_DECAY {
                return Err(SoulEngineErrors::StalePoolStateData)
            }
        }

        Ok(snapshot.pool_state)
    }
}

impl StateViewer for UniswapClmmPools {
    type State = UniswapClmmPools;

    fn get_state_snapshot(
        redis_conn_pool: &Pool<RedisConnectionManager>,
        network: &str,
        check_for_freshness: bool
    ) -> Result<Self::State, SoulEngineErrors> {
        if !SUPPORTED_NETWORK_LIST.contains(&network) {
            return Err(SoulEngineErrors::NotSupportedNetwork);
        }

        let mut conn = redis_conn_pool.get()?;

        let key = |version: &str| {
            Self::REDIS_SNAPSHOT_KEY
                .replace("{network}", network)
                .replace("{market}", "uniswap")
                .replace("{version}", version)
        };

        let key_to_snap_hash_v3: String = key("v3");
        let key_to_snap_hash_v4: String = key("v4");

        let (raw_slot_v3, raw_ticks_v3, raw_slot_v4, raw_ticks_v4): (String, String, String, String) =
            r2d2_redis::redis::pipe()
                .hget(&key_to_snap_hash_v3, "slot")
                .hget(&key_to_snap_hash_v3, "ticks")
                .hget(&key_to_snap_hash_v4, "slot")
                .hget(&key_to_snap_hash_v4, "ticks")
                .query(&mut *conn)?;

        let slot_v3: PoolSnapshot<String, Slot0> = serde_json::from_str(&raw_slot_v3)?;
        let ticks_v3: PoolSnapshot<String, BTreeMap<i32, TickData>> = serde_json::from_str(&raw_ticks_v3)?;

        let slot_v4: PoolSnapshot<String, Slot0> = serde_json::from_str(&raw_slot_v4)?;
        let ticks_v4: PoolSnapshot<String, BTreeMap<i32, TickData>> = serde_json::from_str(&raw_ticks_v4)?;

        if check_for_freshness {
            let current_ts = time::SystemTime::now()
                .duration_since(UNIX_EPOCH)?
                .as_secs();

            let slot_age  = current_ts.saturating_sub(slot_v3.ts.min(slot_v4.ts));
            let ticks_age = current_ts.saturating_sub(ticks_v3.ts.min(ticks_v4.ts));

            if slot_age > POOL_STATE_DECAY || ticks_age > POOL_TICK_DATA_DECAY {
                return Err(SoulEngineErrors::StalePoolStateData);
            }
        }

        let mut slot0s: BTreeMap<String, Slot0> = slot_v3.pool_state;
        slot0s.extend(slot_v4.pool_state);

        let mut ticks: BTreeMap<String, BTreeMap<i32, TickData>> = ticks_v3.pool_state;
        ticks.extend(ticks_v4.pool_state);

        Ok(
            UniswapClmmPools {
                slot0s,
                ticks,
            }
        )
    }
}


pub fn get_pool_state_for_network(
    redis_conn_pool: &Pool<RedisConnectionManager>,
    network: &str,
    check_for_freshness: bool
) -> Result<PoolStateV2, SoulEngineErrors> {
    let pool_state = if network == "solana" {
        PoolStateV2 {
            meteora_dlmm_pool: Arc::new(
                MeteoraDlmmPool::get_state_snapshot(
                    redis_conn_pool,
                    network,
                    check_for_freshness
                )?
            ),
            whirlpool: Arc::new(
                Whirlpool::get_state_snapshot(
                    redis_conn_pool,
                    network,
                    check_for_freshness
                )?
            ),
            ray_clmm_pool: Arc::new(
                RayClmmPool::get_state_snapshot(
                    redis_conn_pool,
                    network,
                    check_for_freshness
                )?
            ),
            ray_amm_pool: Arc::new(
                RayAmmPool::get_state_snapshot(
                    redis_conn_pool,
                    network,
                    check_for_freshness
                )?
            ),
            uni_amm_pool: Arc::new(BTreeMap::new()),
            uni_clmm_pool: Arc::new(UniswapClmmPools{slot0s: BTreeMap::new(), ticks: BTreeMap::new()}),
        }
    } else {
        PoolStateV2 {
            uni_amm_pool: Arc::new(
                UniswapAmm::get_state_snapshot(
                    redis_conn_pool,
                    network,
                    check_for_freshness
                )?
            ),
            uni_clmm_pool: Arc::new(
                UniswapClmmPools::get_state_snapshot(
                    redis_conn_pool,
                    network,
                    check_for_freshness
                )?
            ),
            meteora_dlmm_pool: Arc::new(BTreeMap::new()),
            whirlpool: Arc::new(BTreeMap::new()),
            ray_clmm_pool: Arc::new(BTreeMap::new()),
            ray_amm_pool: Arc::new(BTreeMap::new()),
        }
    };

    Ok(pool_state)
}