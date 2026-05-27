// V1 Smart Router doesn't support Uniswap

use crate::smart_router::v1::manager::orca::clmm::swap_manager::swap_manager as orca_clmm_swap;
use crate::smart_router::v1::manager::meteora::dlmm::swap_manager::swap_manager as meteora_dlmm_swap;
use crate::smart_router::v1::manager::raydium::clmm::swap_manager::swap_manager as raydium_clmm_swap;
use crate::smart_router::v1::manager::raydium::amm::swap_manager::swap_manager as raydium_amm_swap;
use crate::smart_router::smart_router_errors::SoulSmartRouterError;
use crate::config::{DECAY_PERIOD_COLD_PATH, COLD_PATH_KEY};
use crate::dex::metadata::{Metadata, ColdPath, Path, MarketKind};
use crate::dex::orca::Whirlpool;
use crate::dex::raydium::{RayClmmPool, RayAmmPool};
use crate::dex::meteora::MeteoraDlmmPool;

use std::collections::HashMap;

use r2d2::Pool;
use r2d2_redis::redis::Commands;
use r2d2_redis::RedisConnectionManager;

use std::time;
use std::time::{Duration, UNIX_EPOCH};

#[derive(Debug)]
pub struct PoolStateV1<'a> {
    pub whirlpool: &'a HashMap<String, Whirlpool>,
    pub meteora_dlmm_pool: &'a HashMap<String, MeteoraDlmmPool>,
    pub ray_amm_pool: &'a HashMap<String, RayAmmPool>,
    pub ray_clmm_pool: &'a HashMap<String, RayClmmPool>,
}

#[derive(Debug)]
pub struct SmartResultV1 {
    pub amount_in: u128,
    pub amount_out: u128,
    pub best_path: Path,
    pub execution_time: Duration
}

#[derive(Debug)]
pub struct SmartRouterV1<'a> {
    pub metadata: &'a HashMap<String, Metadata>,
    pub pool_state: &'a PoolStateV1<'a>,
    pub redis_pool_connection: &'a Pool<RedisConnectionManager>
}

impl<'a> SmartRouterV1<'a> {
    pub fn new(
        metadata: &'a HashMap<String, Metadata>,
        pool_state: &'a PoolStateV1<'a>,
        redis_pool_connection: &'a Pool<RedisConnectionManager>
    ) -> Self {
        Self {
            metadata,
            pool_state,
            redis_pool_connection
        }
    }

    pub fn smart_router(
        &self,
        base_mint: &str,
        quote_mint: &str,
        delta_amount: u128,
        a_to_b: bool,
        amount_specified_is_in: bool,
    ) -> Result<SmartResultV1, SoulSmartRouterError> {
        let timestamp = time::SystemTime::now()
            .duration_since(UNIX_EPOCH)?
            .as_secs();

        let cold_paths = self.get_cold_path(
            &format!("{}/{}", base_mint, quote_mint),
            timestamp
        )?;

        let mut map_results: HashMap<&Path, u128> = HashMap::new();

        let start_time = time::Instant::now();

        for path in &cold_paths.routes {
            let smart_swap_res = self.smart_swap(
                base_mint,
                quote_mint,
                delta_amount,
                a_to_b,
                amount_specified_is_in,
                timestamp,
                path
            );

            match smart_swap_res {
                Ok(res) => { map_results.insert(path, res); },
                Err(_) => {}
            };
        }

        let (best_path, best_result) = if amount_specified_is_in {
            map_results
                .into_iter()
                .max_by_key(|entity| entity.1)
                .ok_or(SoulSmartRouterError::FailedToFindBestResult)?
        } else {
            map_results
                .into_iter()
                .min_by_key(|entity| entity.1)
                .ok_or(SoulSmartRouterError::FailedToFindBestResult)?
        };

        Ok(SmartResultV1 {
            amount_in: if amount_specified_is_in {delta_amount} else {best_result},
            amount_out: if amount_specified_is_in {best_result} else {delta_amount},
            best_path: best_path.clone(),
            execution_time: start_time.elapsed()
        })
    }

    fn smart_swap(
        &self,
        base_mint: &str,
        quote_mint: &str,
        delta_amount: u128,
        a_to_b: bool,
        amount_specified_is_in: bool,
        timestamp: u64,
        path: &Path
    ) -> Result<u128, SoulSmartRouterError> {
        // P.S a_to_b means only swaping base_mint to quote_mint or vice versa.
        // for determining a swap direction within a pool is used x_to_y.

        let mut processing_amount = delta_amount;
        let mut processing_mint = base_mint;
        let mut path = path.clone();

        if (!a_to_b && amount_specified_is_in) || (a_to_b && !amount_specified_is_in) {
            path.reverse();
            processing_mint = quote_mint;
        }

        for pool in &path {
            let pool_metadata = self.metadata
                .get(pool)
                .ok_or(SoulSmartRouterError::NoMetadataForPool)?;

            let (x_to_y, next_mint) = if processing_mint == pool_metadata.mint0 {
                (amount_specified_is_in, pool_metadata.mint1.as_str())
            } else if processing_mint == pool_metadata.mint1 {
                (!amount_specified_is_in, pool_metadata.mint0.as_str())
            } else {
                return Err(SoulSmartRouterError::NoMatchWithMint);
            };

            let kind = pool_metadata.kind;

            // All these markets are in config::SWAP_SUPPORTED_MARKETS
            let pool_swap_result = match kind {
                MarketKind::OrcaClmm => {
                    let pool_data = self.pool_state.whirlpool
                        .get(pool)
                        .ok_or(SoulSmartRouterError::NoPoolInPoolState(pool.clone()))?;

                    orca_clmm_swap( x_to_y, amount_specified_is_in, processing_amount, timestamp, pool_data)

                },
                MarketKind::RaydiumClmm | MarketKind::RaydiumAmm => {
                    let fee_rate = (pool_metadata.fee_rate
                        .ok_or(SoulSmartRouterError::FailedToGetFeeRate)? * 1_000_000f64) as u32;

                    match kind {
                        MarketKind::RaydiumClmm => {
                            let pool_data = self.pool_state.ray_clmm_pool
                                .get(pool)
                                .ok_or(SoulSmartRouterError::NoPoolInPoolState(pool.clone()))?;
                            raydium_clmm_swap(x_to_y, amount_specified_is_in, processing_amount, fee_rate, pool_data)
                        },
                        MarketKind::RaydiumAmm => {
                            let pool_data = self.pool_state.ray_amm_pool
                                .get(pool)
                                .ok_or(SoulSmartRouterError::NoPoolInPoolState(pool.clone()))?;
                            raydium_amm_swap(x_to_y, amount_specified_is_in, processing_amount, fee_rate, pool_data)
                        },
                        _ => unreachable!(),
                    }
                },
                MarketKind::MeteoraDlmm => {
                    let pool_data = self.pool_state.meteora_dlmm_pool
                        .get(pool)
                        .ok_or(SoulSmartRouterError::NoPoolInPoolState(pool.clone()))?;

                    meteora_dlmm_swap(x_to_y, amount_specified_is_in, processing_amount, timestamp, pool_data)
                },
                _ => return Err(SoulSmartRouterError::UnsupportedMarket),
            }?;

            processing_amount = if amount_specified_is_in {
                pool_swap_result.total_amount_out
            } else {
                pool_swap_result.total_amount_in
            };

            processing_mint = next_mint;
        }

        Ok(processing_amount)
    }

    fn get_cold_path(
        &self,
        pair: &str,
        timestamp: u64
    ) -> Result<ColdPath, SoulSmartRouterError> {
        let mut conn = self.redis_pool_connection.get()?;

        let raw_json: String = conn.hget(COLD_PATH_KEY, pair)?;

        let paths: ColdPath = serde_json::from_str(&raw_json)?;

        let ts: u64 = paths.ts.parse()?;

        if timestamp.saturating_sub(ts) > DECAY_PERIOD_COLD_PATH {
            return Err(SoulSmartRouterError::ColdPathExpired);
        }

        Ok(paths)
    }
}