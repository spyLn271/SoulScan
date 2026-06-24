use std::collections::BTreeMap;
use std::{thread, time};
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;
use std::time::{Instant, UNIX_EPOCH};
use evmap::handles::{ReadHandle, WriteHandle};

use r2d2::Pool;
use r2d2_redis::redis::Commands;
use r2d2_redis::redis::streams::StreamMaxlen;
use r2d2_redis::RedisConnectionManager;

use rusted_soul_dex::dex::metadata::Metadata;
use rusted_soul_dex::smart_router::v2::router::{PoolStateV2, SmartRouterV2};

use crate::api::dex::snapshot::{
    TokenData,
    get_metadata_for_network,
    get_pool_state_for_network,
    get_token_addresses
};
use crate::api::cex::orderbook::get_whole_order_book;
use crate::api::cex::address_resolver::get_addr_supported_cex;
use crate::config::{
    SWAP_FEE_RATE,
    SUPPORTED_NETWORK_LIST,
    NETWORK_QUOTES,
    CEX_TAKER_FEE,
    MIN_PROFIT,
    OPPORTUNITY_STREAM,
    POOL_STATE_DECAY
};
use crate::errors::SoulEngineErrors;

use tracing::{debug, error, info, info_span, trace, warn};

const WORKER_RETRY_DELAY: time::Duration = time::Duration::from_secs(1);
const WORKER_IDLE_DELAY: time::Duration = time::Duration::from_secs(5);
const HEALTH_CHECK_INTERVAL: time::Duration = time::Duration::from_secs(5);
const WRITER_FAILURE_ALERT_THRESHOLD: u32 = 5;


#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum DataV2 {
    PoolState {
        pool_state: Arc<PoolStateV2>,
        ts: u64
    },
    Metadata(Arc<BTreeMap<String, Metadata>>),
    Tokens(Arc<BTreeMap<usize, (String, TokenData)>>),
}

#[derive(Debug, serde::Serialize)]
pub struct ArbOpportunity {
    pub id: String,
    pub network: String,
    pub cex: String,
    pub direction: &'static str,

    pub base_symbol: String,
    pub base_mint: String,
    pub quote_symbol: String,
    pub quote_mint: String,

    pub cex_amount_in: f64,
    pub cex_amount_out: f64,
    pub cex_start_price: f64,
    pub cex_end_price: f64,
    pub cex_avg_price: f64,
    pub cex_orderbook_depth: u16,

    pub dex_amount_in: f64,
    pub dex_amount_out: f64,
    pub dex_avg_price: f64,

    pub profit_usd: f64,
    pub profit_percentage: f64,
    pub orderbook_ts_ms: u64,
}

#[derive(Debug, Copy, Clone)]
enum ScanMode {
    CexToDex,
    DexToCex,
}

impl ScanMode {
    fn as_str(&self) -> &'static str {
        match self {
            ScanMode::CexToDex => "cex_to_dex",
            ScanMode::DexToCex => "dex_to_cex",
        }
    }
}

struct CexDexScanner<'a, 'b> {
    base_mint: String,
    base_symbol: String,
    base_decimals: u32,
    quote_mint: String,
    quote_symbol: String,
    quote_decimals: u32,
    network: String,
    cex: String,
    smart_router_v2: &'b mut SmartRouterV2<'a>,
}

struct ProfitTracker {
    dex_amount_in: f64,
    dex_amount_out: f64,
    cex_amount_in: f64,
    cex_amount_out: f64,
    profit: f64
}

struct ScannerLoopResult {
    // DEX
    dex_amount_in: f64,
    dex_amount_out: f64,
    dex_avg_price: f64,

    // CEX
    cex_amount_in: f64,
    cex_amount_out: f64,
    cex_start_price: f64,
    cex_end_price: f64,
    cex_avg_price: f64,
    cex_orderbook_depth: u16,

    // data
    profit: f64
}

impl<'a, 'b> CexDexScanner<'a, 'b> {
    fn scanner(
        &mut self,
        redis_conn_pool: &Pool<RedisConnectionManager>,
        orderbook: &Vec<Vec<f64>>,
        orderbook_ts: u64,
        scan_mode: ScanMode,
    ) {
        let _span = info_span!(
            "scan",
            cex = %self.cex,
            base = %self.base_symbol,
            quote = %self.quote_symbol,
            direction = scan_mode.as_str()
        ).entered();

        let scanner_started = Instant::now();

        let scanner_result = self.scanner_loop(
            orderbook,
            scan_mode,
        );

        let opportunity = match scanner_result {
            Ok(data) => data,
            Err(err) => {
                warn!(%err, "scan aborted");
                return;
            }
        };

        if opportunity.profit < MIN_PROFIT {
            trace!(profit = opportunity.profit, "no opportunity above min profit");
            return;
        }

        let id = format!(
            "{}:{}:{}:{}:{}",
            self.network,
            self.cex,
            self.base_mint,
            self.quote_mint,
            scan_mode.as_str()
        );

        let profit_percentage = match scan_mode {
            ScanMode::CexToDex => {
                (opportunity.profit / opportunity.cex_amount_in) * 100.0
            },
            ScanMode::DexToCex => {
                (opportunity.profit / opportunity.dex_amount_in) * 100.0
            }
        };

        let arb_opportunity = ArbOpportunity {
            id,
            network: self.network.clone(),
            cex: self.cex.clone(),
            direction: scan_mode.as_str(),

            base_symbol: self.base_symbol.clone(),
            base_mint: self.base_mint.clone(),
            quote_symbol: self.quote_symbol.clone(),
            quote_mint: self.quote_mint.clone(),

            cex_amount_in: opportunity.cex_amount_in,
            cex_amount_out: opportunity.cex_amount_out,
            cex_start_price: opportunity.cex_start_price,
            cex_end_price: opportunity.cex_end_price,
            cex_avg_price: opportunity.cex_avg_price,
            cex_orderbook_depth: opportunity.cex_orderbook_depth,

            dex_amount_in: opportunity.dex_amount_in,
            dex_amount_out: opportunity.dex_amount_out,
            dex_avg_price: opportunity.dex_avg_price,

            profit_usd: opportunity.profit,
            profit_percentage,

            orderbook_ts_ms: orderbook_ts
        };

        let payload = match serde_json::to_string(&arb_opportunity) {
            Ok(payload) => payload,
            Err(err) => {
                error!(%err, "failed to serialize opportunity");
                return;
            }
        };

        let mut conn = match redis_conn_pool.get() {
            Ok(conn) => conn,
            Err(err) => {
                warn!(%err, "redis pool unavailable, opportunity dropped");
                return;
            }
        };

        let status: Result<String, _> = conn.xadd_maxlen(
            OPPORTUNITY_STREAM,
            StreamMaxlen::Approx(10_000),
            "*",
            &[("data", payload.as_str()), ("type", "dex_cex")],
        );

        match status {
            Ok(_) => {
                info!(
                    elapsed_ts = scanner_started.elapsed().as_millis() as u64,
                    profit_usd = arb_opportunity.profit_usd,
                    profit_percentage = arb_opportunity.profit_percentage,
                    cex_orderbook_depth = arb_opportunity.cex_orderbook_depth,
                    "arbitrage opportunity published"
                );
            }
            Err(err) => {
                warn!(%err, "failed to publish opportunity");
            }
        }
    }

    fn scanner_loop(
        &mut self,
        orderbook: &Vec<Vec<f64>>,
        scan_mode: ScanMode,
    ) -> Result<ScannerLoopResult, SoulEngineErrors> {
        let mut profit_tracker = ProfitTracker {
            dex_amount_in: 0.0,
            dex_amount_out: 0.0,
            cex_amount_in: 0.0,
            cex_amount_out: 0.0,
            profit: 0.0
        };

        let mut cex_start_price: f64 = 0.0;
        let mut cex_end_price: f64 = 0.0;
        let mut cex_orderbook_depth: u16 = 0;

        let cex_taker_fee = *CEX_TAKER_FEE
            .get(self.cex.as_str())
            .ok_or(SoulEngineErrors::TakerFeeRateNotFound)?;

        'level_loop: for orderbook_level in orderbook.iter() {
            let cex_price = *orderbook_level
                .get(0)
                .ok_or(SoulEngineErrors::NoPriceFoundInLevelOrderbook)?;

            let cex_amount = *orderbook_level
                .get(1)
                .ok_or(SoulEngineErrors::NoAmountFoundInLevelOrderbook)?;

            // Greedy Scan
            let greedy_profit = self.calculate_profit(
                cex_price,
                cex_amount,
                cex_taker_fee,
                scan_mode,
                &profit_tracker
            );

            match greedy_profit {
                Ok(new_profit_tracker) => {
                    if new_profit_tracker.profit > profit_tracker.profit {
                        profit_tracker = new_profit_tracker;

                        cex_start_price = if cex_orderbook_depth == 0 { cex_price } else { cex_start_price };
                        cex_end_price = cex_price;
                        cex_orderbook_depth += 1;

                        continue
                    }
                }
                Err(err) => {
                    trace!(%err, cex_price, "greedy pricing failed");
                }
            }

            // Probing
            for i in 0..10 {
                let probing_profit = self.calculate_profit(
                    cex_price,
                    cex_amount * 1.0 / 10f64,
                    cex_taker_fee,
                    scan_mode,
                    &profit_tracker
                );

                match probing_profit {
                    Ok(new_profit_tracker) => {
                        if new_profit_tracker.profit > profit_tracker.profit {
                            profit_tracker = new_profit_tracker;

                            if i == 0 {
                                cex_start_price = if cex_orderbook_depth == 0 { cex_price } else { cex_start_price };
                                cex_end_price = cex_price;
                                cex_orderbook_depth += 1;
                            }

                        } else {
                            break 'level_loop;
                        }
                    }
                    Err(err) => {
                        trace!(%err, cex_price, "probing pricing failed");
                        break 'level_loop;
                    }
                }
            }
        }

        let (dex_avg_price, cex_avg_price) = match scan_mode {
            ScanMode::CexToDex => {
                (
                    profit_tracker.dex_amount_out / profit_tracker.dex_amount_in,
                    profit_tracker.cex_amount_in / profit_tracker.cex_amount_out
                )
            }
            ScanMode::DexToCex => {
                (
                    profit_tracker.dex_amount_in / profit_tracker.dex_amount_out,
                    profit_tracker.cex_amount_out / profit_tracker.cex_amount_in
                )
            }
        };

        Ok(
            ScannerLoopResult {
                dex_amount_in: profit_tracker.dex_amount_in,
                dex_amount_out: profit_tracker.dex_amount_out,
                dex_avg_price,
                cex_amount_in: profit_tracker.cex_amount_in,
                cex_amount_out: profit_tracker.cex_amount_out,
                cex_start_price,
                cex_end_price,
                cex_avg_price,
                cex_orderbook_depth,
                profit: profit_tracker.profit
            }
        )
    }

    fn calculate_profit(
        &mut self,
        cex_price: f64,
        cex_amount: f64,
        cex_taker_fee: f64,
        scan_mode: ScanMode,
        profit_tracker: &ProfitTracker
    ) -> Result<ProfitTracker, SoulEngineErrors> {
        match scan_mode {
            ScanMode::CexToDex => {
                // here we are looking at asks order book(the clients from CEX want to sell)
                // and we need to buy tokenX from CEX and sell it in DEX.
                // the cex amount in is USD(T, C) and cex amount out is tokenX
                // we take cex amount out(which is tokenX) and put it in Smart Router
                // to know how many USD(T, C) we get for amount of tokenX
                // we put flag 'a_to_b' as true (base token mint is TokenX, quote mint is USD(T, C))
                // and we set 'asii' as true.

                let (cex_amount_in, cex_amount_out) = (
                    profit_tracker.cex_amount_in + cex_price * cex_amount,
                    profit_tracker.cex_amount_out + cex_amount * (1.0 - cex_taker_fee)
                );

                let sor_v2_result = self.smart_router_v2.smart_router(
                    self.base_mint.as_str(), // token X
                    self.quote_mint.as_str(), // USDT, USDC stable coin
                    (cex_amount_out * 10u128.pow(self.base_decimals) as f64 * (1f64 - SWAP_FEE_RATE)) as u128,
                    true, // tokenX -> USD
                    true // input is tokenX, and we want to take how many USD we get for amount of tokenX
                )?;

                let dex_atomic_amount_out: u128 = sor_v2_result.total_amount_out;

                let cex_atomic_count_in: u128 = (cex_amount_in * 10u128.pow(self.quote_decimals) as f64) as u128;

                let profit = if cex_atomic_count_in > dex_atomic_amount_out {
                    -1.0
                } else {
                    let atomic_profit = dex_atomic_amount_out - cex_atomic_count_in;

                    atomic_profit as f64 / (10u128.pow(self.quote_decimals) as f64)
                };

                Ok(
                    ProfitTracker {
                        dex_amount_in: cex_amount_out,
                        dex_amount_out: dex_atomic_amount_out as f64 / 10u128.pow(self.quote_decimals) as f64,
                        cex_amount_in,
                        cex_amount_out,
                        profit
                    }
                )
            },
            ScanMode::DexToCex => {
                // here we are looking at bids order book(the clients from CEX want to buy)
                // and we need to buy tokenX from DEX and sell it in CEX.
                // the cex amount in is tokenX and cex amount out is USD(T, C)
                // we take cex amount in(which is tokenX) and put it in Smart Router
                // to know how many USD(T, C) we need to give in order to get amount of tokenX
                // we put flag 'a_to_b' as false (base token mint is TokenX, quote mint is USD(T, C))
                // and we set 'asii' as false.

                let (cex_amount_in, cex_amount_out) = (
                    profit_tracker.cex_amount_in + cex_amount,
                    profit_tracker.cex_amount_out + cex_price * cex_amount * (1.0 - cex_taker_fee)
                );

                let sor_v2_result = self.smart_router_v2.smart_router(
                    self.base_mint.as_str(), // token X
                    self.quote_mint.as_str(), // USDT, USDC stable coin
                    (cex_amount_in * 10u128.pow(self.base_decimals) as f64) as u128,
                    false, // USD -> tokenX
                    false // input is tokenX, and we want to know how many of USD we need to give to get amount of tokenX
                )?;

                let dex_atomic_amount_in: u128 = sor_v2_result.total_amount_in * 1_000_000
                    / (1_000_000 - (SWAP_FEE_RATE * 1_000_000f64) as u128);

                let cex_atomic_amount_out: u128 = (cex_amount_out * 10u128.pow(self.quote_decimals) as f64) as u128;

                let profit = if dex_atomic_amount_in > cex_atomic_amount_out {
                    -1.0
                } else {
                    let atomic_profit = cex_atomic_amount_out - dex_atomic_amount_in;

                    atomic_profit as f64 / (10u128.pow(self.quote_decimals) as f64)
                };

                Ok(
                    ProfitTracker {
                        dex_amount_in: dex_atomic_amount_in as f64 / 10u128.pow(self.quote_decimals) as f64,
                        dex_amount_out: cex_amount_in,
                        cex_amount_in,
                        cex_amount_out,
                        profit
                    }
                )
            },
        }
    }
}


fn writer_loop(
    network: String,
    writer: Arc<Mutex<WriteHandle<&str, Arc<DataV2>>>>,
    redis_conn_pool: Pool<RedisConnectionManager>,
) {
    let _span = info_span!("writer", %network).entered();
    info!("writer started");

    let mut consecutive_failures: u32 = 0;

    loop {
        let cycle_started = time::Instant::now();

        match data_generation_for_writer(&redis_conn_pool, network.as_str()) {
            Ok((pool_state, metadata, tokens)) => {
                let mut writer_guard = writer
                    .lock()
                    .unwrap_or_else(|poisoned| poisoned.into_inner());

                writer_guard.update(
                    "state",
                    Arc::new(pool_state)
                );
                writer_guard.update(
                    "metadata",
                    Arc::new(metadata)
                );
                writer_guard.update(
                    "tokens",
                    Arc::new(tokens)
                );
                writer_guard.publish();

                consecutive_failures = 0;
                debug!(
                    elapsed_ms = cycle_started.elapsed().as_millis() as u64,
                    "generation published"
                );
            },
            Err(err) => {
                consecutive_failures += 1;

                if consecutive_failures >= WRITER_FAILURE_ALERT_THRESHOLD {
                    error!(%err, consecutive_failures, "writer cycles failing repeatedly, workers will go stale");
                } else {
                    warn!(%err, consecutive_failures, "writer cycle failed, keeping last generation");
                }
            }
        };

        thread::sleep(time::Duration::from_secs(1));
    }
}

fn data_generation_for_writer(
    redis_conn_pool: &Pool<RedisConnectionManager>,
    network: &str,
) -> Result<(DataV2, DataV2, DataV2), SoulEngineErrors> {
    let pool_state = DataV2::PoolState {
        pool_state: Arc::new(
            get_pool_state_for_network(
                redis_conn_pool,
                network, 
                true
            )?
        ),
        ts: time::SystemTime::now()
                .duration_since(UNIX_EPOCH)?
                .as_secs()
    };

    let metadata = DataV2::Metadata(
        Arc::new(
            get_metadata_for_network(
                redis_conn_pool,
                network
            )?
        )
    );

    let tokens = DataV2::Tokens(
        Arc::new(
            get_token_addresses(
                redis_conn_pool,
                network
            )?
        )
    );

    Ok((pool_state, metadata, tokens))
}

fn worker(
    id: usize,
    total_workers_num: usize,
    network: String,
    redis_conn_pool: Pool<RedisConnectionManager>,
    reader: ReadHandle<&str, Arc<DataV2>>
) {
    if !SUPPORTED_NETWORK_LIST.contains(&network.as_str()) {
        panic!("Unknown network {}", network)
    }

    let _span = info_span!("worker", id, %network).entered();
    info!("worker started");

    loop {
        let tokens = match get_tokens(&reader) {
            Ok(data) => data,
            Err(err) => {
                debug!(%err, "tokens not published yet");
                thread::sleep(WORKER_RETRY_DELAY);
                continue;
            }
        };

        let (start, end) = match get_start_and_end(id, total_workers_num, tokens.len()) {
            Some(data) => data,
            None => {
                debug!(tokens_len = tokens.len(), "no shard for this worker, idling");
                thread::sleep(WORKER_IDLE_DELAY);
                continue;
            },
        };

        let pool_state = match get_pool_state(&reader) {
            Ok(data) => data,
            Err(SoulEngineErrors::StalePoolStateData) => {
                warn!("pool state is stale, writer is behind");
                thread::sleep(WORKER_RETRY_DELAY);
                continue;
            }
            Err(err) => {
                debug!(%err, "pool state not published yet");
                thread::sleep(WORKER_RETRY_DELAY);
                continue;
            }
        };

        let metadata = match get_metadata(&reader) {
            Ok(data) => data,
            Err(err) => {
                debug!(%err, "metadata not published yet");
                thread::sleep(WORKER_RETRY_DELAY);
                continue;
            }
        };

        let mut smart_router_v2 = SmartRouterV2::new(
            &metadata,
            &pool_state,
            &redis_conn_pool
        );

        let pass_started = time::Instant::now();

        for (_, token) in tokens.range(start..end) {
            let supported_cex = get_addr_supported_cex(
                &redis_conn_pool,
                network.as_str(),
                token.0.as_str(),
            );

            let cex_map = match supported_cex {
                Ok(data) => data,
                Err(err) => {
                    trace!(%err, token = %token.0, "cex address resolution failed");
                    continue;
                }
            };


            for quote in NETWORK_QUOTES.get(network.as_str()).unwrap() {
                for (cex, base_symbol) in cex_map.iter() {
                    let symbol = format!("{}{}", base_symbol, quote.0);

                    let orderbook = get_whole_order_book(
                        &redis_conn_pool,
                        cex.as_str(),
                        symbol.as_str(),
                    );

                    match orderbook {
                        Ok(orderbook) => {
                            let mut scan = CexDexScanner {
                                base_mint: token.0.to_string(),
                                base_symbol: base_symbol.to_string(),
                                base_decimals: token.1.decimals,
                                quote_mint: quote.1.to_string(),
                                quote_symbol: quote.0.to_string(),
                                quote_decimals: quote.2,
                                network: network.clone(),
                                cex: cex.to_string(),
                                smart_router_v2: &mut smart_router_v2,
                            };

                            scan.scanner(
                                &redis_conn_pool,
                                &orderbook.asks,
                                orderbook.timestamp_ms,
                                ScanMode::CexToDex
                            );
                            scan.scanner(
                                &redis_conn_pool,
                                &orderbook.bids,
                                orderbook.timestamp_ms,
                                ScanMode::DexToCex
                            );

                        },
                        Err(err) => {
                            trace!(%err, %cex, %symbol, "orderbook unavailable");
                        }
                    }
                }
            }
        }

        debug!(
            tokens = end - start,
            elapsed_ms = pass_started.elapsed().as_millis() as u64,
            "scan pass complete"
        );
    }
}

fn get_pool_state(
    reader: &ReadHandle<&str, Arc<DataV2>>
) -> Result<Arc<PoolStateV2>, SoulEngineErrors> {
    let pool_state_option = reader
        .get("state")
        .ok_or(SoulEngineErrors::NoPoolState)?
        .get_one()
        .ok_or(SoulEngineErrors::NoPoolState)?
        .clone();

    match &*pool_state_option {
        DataV2::PoolState{ pool_state, ts } => {
            let current_ts = time::SystemTime::now()
                .duration_since(UNIX_EPOCH)?
                .as_secs();

            if current_ts.saturating_sub(*ts) > POOL_STATE_DECAY {
                return Err(SoulEngineErrors::StalePoolStateData)
            }

            Ok(pool_state.clone())
        },
        _ => {Err(SoulEngineErrors::WrongKeyForReadHandler)}
    }
}

fn get_metadata(
    reader: &ReadHandle<&str, Arc<DataV2>>
) -> Result<Arc<BTreeMap<String, Metadata>>, SoulEngineErrors> {
    let metadata_option = reader
        .get("metadata")
        .ok_or(SoulEngineErrors::NoMetadata)?
        .get_one()
        .ok_or(SoulEngineErrors::NoMetadata)?
        .clone();

    match &*metadata_option {
        DataV2::Metadata(metadata) => {
            Ok(metadata.clone())
        },
        _ => {Err(SoulEngineErrors::WrongKeyForReadHandler)}
    }
}

fn get_tokens(
    reader: &ReadHandle<&str, Arc<DataV2>>
) -> Result<Arc<BTreeMap<usize, (String, TokenData)>>, SoulEngineErrors> {
    let tokens_option = reader
        .get("tokens")
        .ok_or(SoulEngineErrors::NoTokens)?
        .get_one()
        .ok_or(SoulEngineErrors::NoTokens)?
        .clone();

    match &*tokens_option {
        DataV2::Tokens(tokens) => {
            Ok(tokens.clone())
        },
        _ => {Err(SoulEngineErrors::WrongKeyForReadHandler)}
    }
}

fn get_start_and_end(
    id: usize,
    total_workers_num: usize,
    tokens_len: usize,
) -> Option<(usize, usize)> {
    for workers_num in (1..total_workers_num + 1).rev() {
        if id >= workers_num {
            return None;
        }

        let chunk = tokens_len / workers_num;
        if chunk == 0 {
            continue;
        }

        let r = tokens_len % workers_num;

        let start = if r != 0 {
            let offset = if id < r { id } else { r };
            chunk * id + offset
        } else {
            chunk * id
        };

        let end = if r != 0 {
            let offset = if id < r { id + 1 } else { r };
            chunk * (id + 1) + offset
        } else {
            chunk * (id + 1)
        };

        return Some((start, end));
    }

    None
}


pub fn start_cex_dex_scanner_supervisor (
    network: String,
    total_workers_num: usize,
    redis_url: &str
) {
    if !SUPPORTED_NETWORK_LIST.contains(&network.as_str()) {
        panic!("{network} network is not supported");
    }

    if total_workers_num == 0 {
        panic!("{network} total workers cannot be 0");
    }

    info!(%network, total_workers_num, "cex-dex scanner supervisor starting");

    let client = RedisConnectionManager::new(redis_url)
        .expect("invalid redis url");
    let redis_conn_pool = Pool::builder()
        .max_size(50)
        .build(client)
        .expect("failed to build redis connection pool, is redis running?");

    let (writer, reader) = unsafe {
        evmap::new_assert_stable::<&'static str, Arc<DataV2>>()
    };

    let arc_mutex_writer = Arc::new(Mutex::new(writer));

    let spawn_writer = |network: String| {
        let worker_writer = arc_mutex_writer.clone();
        let writer_redis_conn_pool = redis_conn_pool.clone();

        thread::Builder::new()
            .name("writer".to_string())
            .spawn(move || {
                writer_loop(
                    network,
                    worker_writer,
                    writer_redis_conn_pool,
                )
            })
            .expect("failed to spawn writer thread")
    };

    let spawn_worker = |id: usize, network: String| {
        let worker_redis_conn_pool = redis_conn_pool.clone();
        let worker_reader = reader.clone();

        let handle = thread::Builder::new()
            .name(format!("worker-{id}"))
            .spawn(move || {
                worker(
                    id,
                    total_workers_num,
                    network,
                    worker_redis_conn_pool,
                    worker_reader
                );
            })
            .expect("failed to spawn worker thread");

        (id, handle)
    };

    let mut writer_thread = spawn_writer(network.clone());

    let mut worker_threads = (0..total_workers_num).map(|id| {
        spawn_worker(id, network.clone())
    }).collect::<Vec<(usize, JoinHandle<()>)>>();

    info!("all threads spawned, supervising");

    loop {
        thread::sleep(HEALTH_CHECK_INTERVAL);

        if writer_thread.is_finished() {
            warn!("writer thread died, respawning");
            writer_thread = spawn_writer(network.clone());
        }

        for worker_entry in worker_threads.iter_mut() {
            if worker_entry.1.is_finished() {
                warn!(worker_id = worker_entry.0, "worker thread died, respawning");
                *worker_entry = spawn_worker(worker_entry.0, network.clone());
            }
        }
    }
}
