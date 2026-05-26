// Incremental Allocation 5% (or IA5)

use std::collections::HashMap;
use std::time;
use std::time::{Duration, UNIX_EPOCH};
use r2d2_redis::redis::Commands;
use r2d2_redis::RedisConnectionManager;
use crate::config::{COLD_PATH_KEY, DECAY_PERIOD_COLD_PATH};
use crate::smart_router::v2::manager::meteora::dlmm::swap_dynamic::DynamicMeteoraResult;
use crate::smart_router::v2::manager::orca::clmm::swap_dynamic::DynamicOrcaResult;
use crate::smart_router::v2::manager::raydium::clmm::swap_dynamic::DynamicRayClmmResult;
use crate::smart_router::v2::manager::raydium::amm::swap_dynamic::DynamicRayAmmResult;
use crate::smart_router::v2::manager::uniswap::amm::swap_dynamic::DynamicUniAmmResult;
use crate::smart_router::v2::manager::uniswap::clmm::swap_dynamic::DynamicUniClmmResult;
use crate::smart_router::v2::manager::dynamic_results::DynamicResult;

use crate::smart_router::smart_router_errors::SoulSmartRouterError;

use crate::dex::orca::Whirlpool;
use crate::dex::raydium::{RayClmmPool, RayAmmPool};
use crate::dex::meteora::MeteoraDlmmPool;
use crate::dex::uniswap::{UniswapAmm, UniswapClmm, UniswapClmmPools};
use crate::dex::pools::Pool;

use crate::dex::metadata::{ColdPath, Path, Metadata};

use crate::math::orca::clmm::tick_index_from_sqrt_price;
use crate::math::uniswap::clmm::tick_index_from_sqrt_price as uni_tick_index_from_sqrt_price;

use crate::smart_router::v2::manager::orca::clmm::swap_dynamic::swap_manager as orca_swap_manager;
use crate::smart_router::v2::manager::raydium::amm::swap_dynamic::swap_manager as raydium_amm_swap_manager;
use crate::smart_router::v2::manager::raydium::clmm::swap_dynamic::swap_manager as raydium_clmm_swap_manager;
use crate::smart_router::v2::manager::meteora::dlmm::swap_dynamic::swap_manager as meteora_swap_manager;
use crate::smart_router::v2::manager::uniswap::clmm::swap_dynamic::swap_manager as uni_clmm_swap_manager;
use crate::smart_router::v2::manager::uniswap::amm::swap_dynamic::swap_manager as uni_amm_swap_manager;

pub trait UpdatePool {
    type DynamicSwapResult;

    fn update(&mut self, swap_res: Self::DynamicSwapResult) -> Result<(), SoulSmartRouterError>;
}

type AmountIn = u128;
type AmountOut = u128;
type DynamicSwapResults = HashMap<String, DynamicResult>;

impl UpdatePool for Whirlpool {
    type DynamicSwapResult = DynamicOrcaResult;

    fn update(&mut self, swap_res: DynamicOrcaResult) -> Result<(), SoulSmartRouterError> {
        self.base_info.liquidity = swap_res.new_liquidity;
        self.base_info.crossed_tick_groups = swap_res.crossed_tick_groups;
        self.base_info.sqrt_price = swap_res.new_sqrt_price;
        self.base_info.tick_current_index = tick_index_from_sqrt_price(&swap_res.new_sqrt_price);

        Ok(())
    }
}

impl UpdatePool for RayClmmPool {
    type DynamicSwapResult = DynamicRayClmmResult;

    fn update(&mut self, swap_res: DynamicRayClmmResult) -> Result<(), SoulSmartRouterError> {
        self.pool_state.liquidity = swap_res.new_liquidity;
        self.pool_state.sqrt_price_x64 = swap_res.new_sqrt_price;
        self.pool_state.tick_current = tick_index_from_sqrt_price(&swap_res.new_sqrt_price);

        Ok(())
    }
}

impl UpdatePool for RayAmmPool {
    type DynamicSwapResult = DynamicRayAmmResult;

    fn update(&mut self, swap_res: DynamicRayAmmResult) -> Result<(), SoulSmartRouterError> {
        self.base_vault.amount = swap_res.new_x_reserves;
        self.quote_vault.amount = swap_res.new_y_reserves;

        Ok(())
    }
}

impl UpdatePool for MeteoraDlmmPool {
    type DynamicSwapResult = DynamicMeteoraResult;

    fn update(&mut self, swap_res: DynamicMeteoraResult) -> Result<(), SoulSmartRouterError> {
        self.lb_pair.active_id = swap_res.new_bin_id;
        self.lb_pair.v_parameters.crossed_bins = swap_res.crossed_bins;
        self.bins.extend(swap_res.touched_bins);

        Ok(())
    }
}

impl UpdatePool for UniswapClmm {
    type DynamicSwapResult = DynamicUniClmmResult;

    fn update(&mut self, swap_res: Self::DynamicSwapResult) -> Result<(), SoulSmartRouterError> {
        self.slot0.sqrt_price_x96 = swap_res.new_sqrt_price_x96;
        self.slot0.liquidity = swap_res.new_liquidity;
        self.slot0.tick_current = uni_tick_index_from_sqrt_price(&swap_res.new_sqrt_price_x96)?;

        Ok(())
    }
}

impl UpdatePool for UniswapAmm {
    type DynamicSwapResult = DynamicUniAmmResult;

    fn update(&mut self, swap_res: Self::DynamicSwapResult) -> Result<(), SoulSmartRouterError> {
        self.reserve0 = swap_res.new_x_reserves;
        self.reserve1 = swap_res.new_y_reserves;

        Ok(())
    }
}


#[derive(Debug)]
pub struct PoolStateV2<'a> {
    pub whirlpool: &'a HashMap<String, Whirlpool>,
    pub meteora_dlmm_pool: &'a HashMap<String, MeteoraDlmmPool>,
    pub ray_amm_pool: &'a HashMap<String, RayAmmPool>,
    pub ray_clmm_pool: &'a HashMap<String, RayClmmPool>,
    pub uni_clmm_pool: &'a UniswapClmmPools,
    pub uni_amm_pool: &'a HashMap<String, UniswapAmm>
}

impl<'a> PoolStateV2<'a> {
    pub fn get_unique_pools_from(
        &self,
        cold_paths: &ColdPath,
        metadata: &HashMap<String, Metadata>
    ) -> HashMap<String, Pool> {
        let mut unique_pools: HashMap<String, Pool> = HashMap::new();

        for path in &cold_paths.routes {
            for pool in path {
                if unique_pools.contains_key(pool) {
                    continue
                }

                if let Some(pool_metadata) = metadata.get(pool) {
                    let (dex, version) = (pool_metadata.dex.as_str(), pool_metadata.version.as_str());

                    match (dex, version) {
                        ("orca", "clmm") => {
                            if let Some(state) = self.whirlpool.get(pool) {
                                unique_pools.insert(pool.clone(), Pool::Whirlpool(state.clone()));
                            }
                        }
                        ("raydium", "clmm") => {
                            if let Some(state) = self.ray_clmm_pool.get(pool) {
                                unique_pools.insert(pool.clone(), Pool::RayClmmPool(state.clone()));
                            }
                        }
                        ("raydium", "amm") => {
                            if let Some(state) = self.ray_amm_pool.get(pool) {
                                unique_pools.insert(pool.clone(), Pool::RayAmmPool(state.clone()));
                            }
                        }
                        ("meteora", "dlmm") => {
                            if let Some(state) = self.meteora_dlmm_pool.get(pool) {
                                unique_pools.insert(pool.clone(), Pool::MeteoraDlmmPool(state.clone()));
                            }
                        }
                        ("uniswap", "v3") | ("uniswap", "v4") => {
                            if let Some(slot0) = self.uni_clmm_pool.slot0s.get(pool) {
                                if let Some(tick) = self.uni_clmm_pool.ticks.get(pool) {
                                    unique_pools.insert(
                                        pool.clone(),
                                        Pool::UniswapClmmPool(
                                            UniswapClmm {
                                                slot0: slot0.clone(),
                                                tick: tick.clone(),
                                            }
                                        )
                                    );
                                }
                            }
                        }
                        ("uniswap", "v2") => {
                            if let Some(state) = self.uni_amm_pool.get(pool) {
                                unique_pools.insert(pool.clone(), Pool::UniswapAmmPool(state.clone()));
                            }
                        }
                        _ => continue
                    }
                }
            }
        }

        unique_pools
    }
}


#[derive(Debug)]
struct ChunkSwapResult {
    pub touched_pools: DynamicSwapResults,
    pub amount_in: u128,
    pub amount_out: u128
}

#[derive(Debug)]
pub struct SmartResultV2 {
    pub paths: HashMap<Path, (AmountIn, AmountOut)>,
    pub total_amount_in: u128,
    pub total_amount_out: u128,
    pub execution_time: Option<Duration>
}


#[derive(Debug)]
pub struct SmartRouterV2<'a> {
    pub metadata: &'a HashMap<String, Metadata>,
    pub pool_state: &'a PoolStateV2<'a>,
    pub redis_pool_connection: &'a r2d2::Pool<RedisConnectionManager>
}


impl<'a> SmartRouterV2<'a> {
    pub fn new(
        metadata: &'a HashMap<String, Metadata>,
        pool_state: &'a PoolStateV2<'a>,
        redis_pool_connection: &'a r2d2::Pool<RedisConnectionManager>
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
    ) -> Result<SmartResultV2, SoulSmartRouterError> {
        let mut result = SmartResultV2 {
            paths: HashMap::new(),
            total_amount_in: 0,
            total_amount_out: 0,
            execution_time: None
        };

        let mut delta_amount = delta_amount;

        let timestamp = time::SystemTime::now()
            .duration_since(UNIX_EPOCH)?
            .as_secs();

        let cold_paths = self.get_cold_path(
            &format!("{}/{}", base_mint, quote_mint),
            timestamp
        )?;

        let mut unique_pools = self.pool_state.get_unique_pools_from(
            &cold_paths,
            self.metadata
        );

        let chunk_amount = delta_amount / 20;

        let start_time = time::Instant::now();

        let mut chunk: u16 = 0;
        while delta_amount > 0 && chunk < 20 {
            let chunk_delta_amount = if chunk == 19 {
                delta_amount
            } else {
                chunk_amount
            };

            let mut is_best_found = false;
            let mut best_touched_pools: DynamicSwapResults = HashMap::new();
            let mut best_path: &Path = &Vec::new();
            let mut best_result: u128 = if amount_specified_is_in {
                0
            } else {
                u128::MAX
            };

            for path in &cold_paths.routes {
                let swap_path_result = self.swap_path_loop(
                    base_mint,
                    quote_mint,
                    chunk_delta_amount,
                    a_to_b,
                    amount_specified_is_in,
                    timestamp,
                    &unique_pools,
                    path
                );

                let Ok(chunk_result) = swap_path_result else { continue };

                (best_result, best_touched_pools, best_path) = Self::find_the_best(
                    best_result,
                    best_touched_pools,
                    &best_path,
                    chunk_result,
                    path,
                    amount_specified_is_in,
                    &mut is_best_found
                );
            }

            if !is_best_found {
                return Err(SoulSmartRouterError::CouldntFindTheBestResultForChunkAmount);
            }

            Self::update_pool_data(
                &mut unique_pools,
                best_touched_pools
            )?;

            let (chunk_amount_in, chunk_amount_out) = if amount_specified_is_in {
                (chunk_delta_amount, best_result)
            } else {
                (best_result, chunk_delta_amount)
            };

            if let Some(entry) = result.paths.get_mut(best_path) {
                entry.0 += chunk_amount_in;
                entry.1 += chunk_amount_out;
            } else {
                result.paths.insert(
                    best_path.clone(),
                    (chunk_amount_in, chunk_amount_out)
                );
            }

            result.total_amount_in += chunk_amount_in;
            result.total_amount_out += chunk_amount_out;


            chunk += 1;
            delta_amount -= chunk_delta_amount;
        }

        result.execution_time = Some(start_time.elapsed());
        Ok(result)
    }

    fn swap_path_loop(
        &self,
        base_mint: &str,
        quote_mint: &str,
        delta_amount: u128,
        a_to_b: bool,
        amount_specified_is_in: bool,
        timestamp: u64,
        pools: &HashMap<String, Pool>,
        path: &Path
    ) -> Result<ChunkSwapResult, SoulSmartRouterError> {
        let mut result = ChunkSwapResult {
            touched_pools: HashMap::new(),
            amount_in: 0,
            amount_out: 0
        };

        let mut processing_amount: u128 = delta_amount;
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

            let pool_state = pools
                .get(pool)
                .ok_or(SoulSmartRouterError::NoStateForPool)?;

            let (x_to_y, next_mint) = if processing_mint == pool_metadata.mint0 {
                (amount_specified_is_in, pool_metadata.mint1.as_str())
            } else if processing_mint == pool_metadata.mint1 {
                (!amount_specified_is_in, pool_metadata.mint0.as_str())
            } else {
                return Err(SoulSmartRouterError::NoMatchWithMint);
            };

            match pool_state {
                Pool::Whirlpool(whirlpool) => {
                    let swap_result = orca_swap_manager(
                        x_to_y, amount_specified_is_in, processing_amount, timestamp, whirlpool
                    )?;

                    processing_amount = if amount_specified_is_in {
                        swap_result.total_amount_out
                    } else {
                        swap_result.total_amount_in
                    };

                    result.touched_pools.insert(
                        pool.clone(),
                        DynamicResult::DynamicOrcaResult(swap_result)
                    );
                },
                Pool::RayAmmPool(ray_amm_pool) => {
                    let fee_rate = (pool_metadata.fee_rate
                        .ok_or(SoulSmartRouterError::FailedToGetFeeRate)? * 1_000_000f64) as u32;

                    let swap_result = raydium_amm_swap_manager(
                        x_to_y, amount_specified_is_in, processing_amount, fee_rate, ray_amm_pool
                    )?;

                    processing_amount = if amount_specified_is_in {
                        swap_result.total_amount_out
                    } else {
                        swap_result.total_amount_in
                    };

                    result.touched_pools.insert(
                        pool.clone(),
                        DynamicResult::DynamicRayAmmResult(swap_result)
                    );
                },
                Pool::RayClmmPool(ray_clmm_pool) => {
                    let fee_rate = (pool_metadata.fee_rate
                        .ok_or(SoulSmartRouterError::FailedToGetFeeRate)? * 1_000_000f64) as u32;

                    let swap_result = raydium_clmm_swap_manager(
                        x_to_y, amount_specified_is_in, processing_amount, fee_rate, ray_clmm_pool
                    )?;

                    processing_amount = if amount_specified_is_in {
                        swap_result.total_amount_out
                    } else {
                        swap_result.total_amount_in
                    };

                    result.touched_pools.insert(
                        pool.clone(),
                        DynamicResult::DynamicRayClmmResult(swap_result)
                    );
                },
                Pool::MeteoraDlmmPool(met_dlmm_pool) => {
                    let swap_result = meteora_swap_manager(
                        x_to_y, amount_specified_is_in, processing_amount, timestamp, met_dlmm_pool
                    )?;

                    processing_amount = if amount_specified_is_in {
                        swap_result.total_amount_out
                    } else {
                        swap_result.total_amount_in
                    };

                    result.touched_pools.insert(
                        pool.clone(),
                        DynamicResult::DynamicMeteoraResult(swap_result)
                    );
                },
                Pool::UniswapClmmPool(uni_clmm_pool) => {
                    // Uniswap fee is already in needed format 400, 500, etc.
                    let fee_rate = pool_metadata.fee_rate
                        .ok_or(SoulSmartRouterError::FailedToGetFeeRate)? as u32;
                    let tick_spacing = pool_metadata.tick_spacing
                        .ok_or(SoulSmartRouterError::FailedToGetTickSpacing)?;

                    let swap_result = uni_clmm_swap_manager(
                        x_to_y,
                        amount_specified_is_in,
                        processing_amount,
                        fee_rate,
                        tick_spacing as i32,
                        &uni_clmm_pool
                    )?;

                    processing_amount = if amount_specified_is_in {
                        swap_result.total_amount_out
                    } else {
                        swap_result.total_amount_in
                    };

                    result.touched_pools.insert(
                        pool.clone(),
                        DynamicResult::DynamicUniClmmResult(swap_result)
                    );
                },
                Pool::UniswapAmmPool(uni_amm_pool) => {
                    // Uniswap fee is already in needed format 400, 500, etc.
                    let fee_rate = pool_metadata.fee_rate
                        .ok_or(SoulSmartRouterError::FailedToGetFeeRate)? as u32;

                    let swap_result = uni_amm_swap_manager(
                        x_to_y,
                        amount_specified_is_in,
                        processing_amount,
                        fee_rate,
                        &uni_amm_pool
                    )?;

                    processing_amount = if amount_specified_is_in {
                        swap_result.total_amount_out
                    } else {
                        swap_result.total_amount_in
                    };

                    result.touched_pools.insert(
                        pool.clone(),
                        DynamicResult::DynamicUniAmmResult(swap_result)
                    );
                }
            };

            processing_mint = next_mint;
        }

        (result.amount_in, result.amount_out) = if amount_specified_is_in {
            (delta_amount, processing_amount)
        } else {
            (processing_amount, delta_amount)
        };

        Ok(result)
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

        if paths.routes.is_empty() {
            return Err(SoulSmartRouterError::NoRoutes);
        }

        Ok(paths)
    }

    fn find_the_best<'b>(
        old: u128,
        old_touched_pools: DynamicSwapResults,
        old_path: &'b Path,
        new: ChunkSwapResult,
        new_path: &'b Path,
        amount_specified_is_in: bool,
        is_best_found: &mut bool
    ) -> (u128, DynamicSwapResults, &'b Path) {
        // println!("old: {old}");
        // println!("old_touched_pools: {old_touched_pools:?}");
        // println!("old_path: {old_path:?}");
        // println!("new: {new:?}");
        // println!("new_path: {new_path:?}");
        // println!("________________________________________");

        if amount_specified_is_in {
            if old >= new.amount_out {
                (old, old_touched_pools, old_path)
            } else {
                *is_best_found = true;
                (new.amount_out, new.touched_pools, new_path)
            }
        } else {
            if old > new.amount_in {
                *is_best_found = true;
                (new.amount_in, new.touched_pools, new_path)
            } else {
                (old, old_touched_pools, old_path)
            }
        }
    }

    fn update_pool_data(
        unique_pools: &mut HashMap<String, Pool>,
        best_touched_pools: DynamicSwapResults
    ) -> Result<(), SoulSmartRouterError> {
        for (pool_key, dynamic_result) in best_touched_pools {
            if let Some(pool) = unique_pools.get_mut(&pool_key) {
                match (pool, dynamic_result) {
                    (Pool::Whirlpool(wp), DynamicResult::DynamicOrcaResult(res)) => wp.update(res)?,
                    (Pool::RayClmmPool(rp), DynamicResult::DynamicRayClmmResult(res)) => rp.update(res)?,
                    (Pool::RayAmmPool(rp), DynamicResult::DynamicRayAmmResult(res)) => rp.update(res)?,
                    (Pool::MeteoraDlmmPool(mp), DynamicResult::DynamicMeteoraResult(res)) => mp.update(res)?,
                    (Pool::UniswapClmmPool(uni), DynamicResult::DynamicUniClmmResult(res)) => uni.update(res)?,
                    (Pool::UniswapAmmPool(uni), DynamicResult::DynamicUniAmmResult(res)) => uni.update(res)?,
                    _ => return Err(SoulSmartRouterError::UnexpectedUpdateError)
                }
            }
        }

        Ok(())
    }
}