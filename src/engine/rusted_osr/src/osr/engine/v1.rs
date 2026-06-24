use std::collections::{BTreeMap, HashMap};
use std::sync::Arc;
use std::time;
use std::time::{Instant, UNIX_EPOCH};

use rusted_soul_dex::dex::metadata::{MarketKind, Metadata, Path};
use rusted_soul_dex::dex::uniswap::UniswapClmm;
use rusted_soul_dex::smart_router::v2::router::PoolStateV2;

use rusted_soul_dex::smart_router::v2::manager::orca::clmm::swap_dynamic::swap_manager as orca_swap_manager;
use rusted_soul_dex::smart_router::v2::manager::raydium::amm::swap_dynamic::swap_manager as raydium_amm_swap_manager;
use rusted_soul_dex::smart_router::v2::manager::raydium::clmm::swap_dynamic::swap_manager as raydium_clmm_swap_manager;
use rusted_soul_dex::smart_router::v2::manager::meteora::dlmm::swap_dynamic::swap_manager as meteora_swap_manager;
use rusted_soul_dex::smart_router::v2::manager::uniswap::clmm::swap_dynamic::swap_manager as uni_clmm_swap_manager;
use rusted_soul_dex::smart_router::v2::manager::uniswap::amm::swap_dynamic::swap_manager as uni_amm_swap_manager;

use crate::osr::token_graph::TokensGraph;
use crate::config::SUPPORTED_NETWORK_LIST;
use crate::errors::SoulOsrError;

use tracing::{info_span, trace, debug, info};

const PROBE_AMOUNT: [f64; 20] = [
    0.1,
    1.0,
    100.0,
    500.0,
    1000.0,
    7812.5,
    15_625.0,
    31_250.0,
    62_500.0,
    125_000.0,
    250_000.0,
    500_000.0,
    1_000_000.0,
    2_500_000.0,
    5_000_000.0,
    10_000_000.0,
    25_000_000.0,
    50_000_000.0,
    75_000_000.0,
    100_000_000.0
];

const MIN_CANDIDATES_LENGTH_REQUIREMENTS: usize = 10;

pub struct OsrEngine {
    pub network: String,
    pub tokens_graph: TokensGraph,
    metadata: Arc<BTreeMap<String, Metadata>>,
    pool_state_v2: Arc<PoolStateV2>,
}

impl OsrEngine {
    pub fn new(
        network: String,
        metadata: Arc<BTreeMap<String, Metadata>>,
        pool_state_v2: Arc<PoolStateV2>,
    ) -> Result<Self, SoulOsrError> {
        if !SUPPORTED_NETWORK_LIST.contains(&network.as_str()) {
            return Err(SoulOsrError::NotSupportedNetwork);
        };

        let tokens_graph = TokensGraph::new(
            &metadata,
            network.clone(),
        )?;


        Ok(
            Self {
                network,
                tokens_graph,
                metadata,
                pool_state_v2,
            }
        )
    }

    fn path_swap_loop(
        &self,
        base_mint: &str,
        quote_mint: &str,
        delta_amount: u128,
        timestamp: u64,
        path: &Path, // it is supposed that path lead from base mint to quote mint, amount_specified_is_in automatically True
    ) -> Result<u128, SoulOsrError> {
        let mut processing_amount: u128 = delta_amount;
        let mut processing_mint = base_mint;


        for pool in path {
            let pool_metadata = self.metadata
                .get(pool)
                .ok_or(SoulOsrError::NoMetadataForPool)?;

            let (x_to_y, next_mint) = if processing_mint == pool_metadata.mint0 {
                (true, pool_metadata.mint1.as_str())
            } else if processing_mint == pool_metadata.mint1 {
                (false, pool_metadata.mint0.as_str())
            } else {
                return Err(SoulOsrError::NoMatchWithMint);
            };

            processing_amount = match pool_metadata.kind {
                MarketKind::OrcaClmm => {
                    let whirlpool = self.pool_state_v2.whirlpool
                        .get(pool)
                        .ok_or(SoulOsrError::NoStateForPool)?;

                    let swap_result = orca_swap_manager(
                        x_to_y,
                        true,
                        processing_amount,
                        timestamp,
                        whirlpool
                    )?;

                    swap_result.total_amount_out
                }
                MarketKind::RaydiumClmm => {
                    let clmm = self.pool_state_v2.ray_clmm_pool
                        .get(pool)
                        .ok_or(SoulOsrError::NoStateForPool)?;

                    let fee_rate = pool_metadata.fee_rate
                        .ok_or(SoulOsrError::FailedToGetFeeRate)?;

                    let swap_result = raydium_clmm_swap_manager(
                        x_to_y,
                        true,
                        processing_amount,
                        fee_rate,
                        clmm
                    )?;

                    swap_result.total_amount_out
                }
                MarketKind::RaydiumAmm => {
                    let amm = self.pool_state_v2.ray_amm_pool
                        .get(pool)
                        .ok_or(SoulOsrError::NoStateForPool)?;

                    let fee_rate = pool_metadata.fee_rate
                        .ok_or(SoulOsrError::FailedToGetFeeRate)?;

                    let swap_result = raydium_amm_swap_manager(
                        x_to_y,
                        true,
                        processing_amount,
                        fee_rate,
                        amm
                    )?;

                    swap_result.total_amount_out
                }
                MarketKind::MeteoraDlmm => {
                    let dlmm = self.pool_state_v2.meteora_dlmm_pool
                        .get(pool)
                        .ok_or(SoulOsrError::NoStateForPool)?;

                    let swap_result = meteora_swap_manager(
                        x_to_y,
                        true,
                        processing_amount,
                        timestamp,
                        dlmm
                    )?;

                    swap_result.total_amount_out
                }
                MarketKind::UniswapV3 | MarketKind::UniswapV4 => {
                    let uni_clmm = UniswapClmm {
                        slot0: self.pool_state_v2.uni_clmm_pool.slot0s
                            .get(pool)
                            .ok_or(SoulOsrError::NoStateForPool)?.clone(),
                        tick: self.pool_state_v2.uni_clmm_pool.ticks
                            .get(pool)
                            .ok_or(SoulOsrError::NoStateForPool)?.clone(),
                    };

                    let fee_rate = pool_metadata.fee_rate
                        .ok_or(SoulOsrError::FailedToGetFeeRate)?;
                    let tick_spacing = pool_metadata.tick_spacing
                        .ok_or(SoulOsrError::FailedToGetTickSpacing)?;

                    let swap_result = uni_clmm_swap_manager(
                        x_to_y,
                        true,
                        processing_amount,
                        fee_rate,
                        tick_spacing as i32,
                        &uni_clmm
                    )?;

                    swap_result.total_amount_out
                }
                MarketKind::UniswapV2 => {
                    let amm = self.pool_state_v2.uni_amm_pool
                        .get(pool)
                        .ok_or(SoulOsrError::NoStateForPool)?;

                    let fee_rate = pool_metadata.fee_rate
                        .ok_or(SoulOsrError::FailedToGetFeeRate)?;

                    let swap_resul = uni_amm_swap_manager(
                        x_to_y, true, processing_amount, fee_rate, &amm
                    )?;

                    swap_resul.total_amount_out
                }
            };

            processing_mint = next_mint;
        }

        Ok(processing_amount)
    }

    pub fn find_the_best_cold_path(
        &self,
        base_mint: String,
        quote_mint: String,
        level_depth: usize
    ) -> Result<Vec<Path>, SoulOsrError> {
        let _span = info_span!(
            "find_the_best_cold_path",
            base_mint = base_mint,
            quote_mint = quote_mint,
            level_depth = level_depth,
            network = self.network.as_str()
        ).entered();

        let started = Instant::now();

        let mut best_cold_path: Vec<Path> = Vec::new();

        let filtered_all_possible_path = self.tokens_graph.get_filtered_paths(
            &base_mint,
            &quote_mint,
        )?;

        if filtered_all_possible_path.is_empty() {
            return Err(SoulOsrError::CouldntDeriveFilteredPath)
        }

        if filtered_all_possible_path.len() <= MIN_CANDIDATES_LENGTH_REQUIREMENTS {
            return Ok(filtered_all_possible_path);
        }

        trace!("filtered_all_possible_path length: {:?}", filtered_all_possible_path.len());

        let mut all_probe_results: HashMap<u128, Vec<(u128, &Path)>> = HashMap::new();

        let base_mint_decimals = self.tokens_graph.tokens
            .get(&base_mint)
            .ok_or(SoulOsrError::ThisTokenWasNotFoundInTokens)?
            .decimals;

        let timestamp = time::SystemTime::now()
            .duration_since(UNIX_EPOCH)?
            .as_secs();

        for path in filtered_all_possible_path.iter() {
            for probe_amount in PROBE_AMOUNT {
                let atomic_probe_amount = (probe_amount * 10f64.powi(base_mint_decimals as i32)) as u128;

                let probe_result = self.path_swap_loop(
                    base_mint.as_str(),
                    quote_mint.as_str(),
                    atomic_probe_amount,
                    timestamp,
                    path
                );

                match probe_result {
                    Ok(result) => {
                        if result == 0 {
                            continue
                        }

                        all_probe_results
                            .entry(atomic_probe_amount)
                            .or_insert_with(
                                Vec::new
                            )
                            .push((result, path))
                    },
                    Err(e) => {
                        trace!("In path({path:?}) occurred error: {e}");
                        break
                    }
                }
            }
        }

        for (_, probe_results) in all_probe_results.iter_mut() {
            probe_results.sort_by(|a, b| b.0.cmp(&a.0));

            for (level, (_, path)) in probe_results.iter().enumerate() {
                if level >= level_depth {
                    break
                }

                if !best_cold_path.contains(path) {
                    best_cold_path.push((*path).clone())
                }
            }
        }

        trace!("all_probe_results : {:?}", all_probe_results);

        info!(
            elapsed_ts = started.elapsed().as_millis() as u64,
            routes = best_cold_path.len(),
            "cold path computed for {}/{}",
            base_mint,
            quote_mint,
        );

        debug!(
            "routes for {}/{}: {:?}",
            base_mint,
            quote_mint,
            best_cold_path,
        );

        Ok(best_cold_path)
    }
}