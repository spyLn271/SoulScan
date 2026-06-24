mod cli;

use crate::cli::{Cli};

use clap::Parser;

use rusted_osr::osr::engine::v1::OsrEngine;
use rusted_osr::logging;
use rusted_osr::errors::SoulOsrError;
use rusted_osr::config::{SUPPORTED_QUOTES, SUPPORTED_NETWORK_LIST};

use crossbeam::channel;
use crossbeam::channel::{Sender, Receiver};

use r2d2_redis::RedisConnectionManager;
use r2d2::Pool;

use std::thread;
use std::sync::Arc;
use std::thread::JoinHandle;
use std::time;
use std::time::{Duration, Instant, UNIX_EPOCH};

use arc_swap::ArcSwap;

use rusted_engine::api::dex::snapshot::{get_pool_state_for_network, get_metadata_for_network};

use rusted_soul_dex::dex::metadata::ColdPath;
use rusted_soul_dex::config::COLD_PATH_KEY;

use tracing::{info, info_span, debug, error, warn};



const WRITER_FAILURE_ESCALATION: u32 = 5;
const CHANEL_CAPACITY: usize = 3000;
const TASK_PRODUCER_INTERVAL: u64 = 2000;
const HEALTH_CHECK_INTERVAL: Duration = Duration::from_secs(5);

fn build_osr_engine(
    redis_pool: &Pool<RedisConnectionManager>,
    network: &str,
) -> Result<OsrEngine, SoulOsrError> {
    let metadata   = Arc::new(get_metadata_for_network(redis_pool, network)?);
    let pool_state = Arc::new(get_pool_state_for_network(redis_pool, network, false)?); // need to change in future to 'true'
    OsrEngine::new(network.to_string(), metadata, pool_state)
}

fn writer_loop(
    engine_cell: Arc<ArcSwap<OsrEngine>>,
    redis_pool_connection: Pool<RedisConnectionManager>,
    network: String,
    refresh_interval: Duration,
) {
    let _span = info_span!("osr_writer", network = %network).entered();
    info!("osr writer started");

    let mut consecutive_failures: u32 = 0;

    loop {
        let started = Instant::now();

        match build_osr_engine(&redis_pool_connection, &network) {
            Ok(engine) => {
                let nodes = engine.tokens_graph.graph.node_count();
                let edges = engine.tokens_graph.graph.edge_count();

                engine_cell.store(Arc::new(engine));
                consecutive_failures = 0;

                debug!(
                    elapsed_ms = started.elapsed().as_millis() as u64,
                    nodes,
                    edges,
                    "engine snapshot published"
                );
            }
            Err(err) => {
                consecutive_failures += 1;
                if consecutive_failures >= WRITER_FAILURE_ESCALATION {
                    error!(consecutive_failures, "writer refresh failed (escalated), serving stale snapshot: {err}");
                } else {
                    warn!(consecutive_failures, "writer refresh failed, keeping last snapshot: {err}");
                }
            }
        }

        thread::sleep(refresh_interval);
    }
}


fn tasks_producer_loop(
    sender_task: Sender<(String, String)>,
    engine_cell: Arc<ArcSwap<OsrEngine>>,
    network: String,
) {
    let _span = info_span!("osr_tasks_producer", network = %network).entered();
    info!("osr tasks producer started");

    let quote_mints = SUPPORTED_QUOTES.get(network.as_str())
        .expect("This network doesnt have quotes in SUPPORTED_QUOTES");

    loop {
        let bases = {
            let engine = engine_cell.load_full();
            engine.tokens_graph.tokens.clone()
        };

        let batch = bases.len() * quote_mints.len();
        let cap   = sender_task.capacity().unwrap_or(CHANEL_CAPACITY);

        if batch >= cap {
            error!(batch, cap, "task batch >= channel capacity; raise the channel capacity");
        } else if cap - sender_task.len() >= batch {
            for (base_mint, _) in &bases {
                for quote_mint in quote_mints {
                    if quote_mint == base_mint { continue; }

                    if sender_task.send((base_mint.clone(), quote_mint.to_string())).is_err() {
                        warn!("task channel disconnected, producer exiting");
                        return;
                    }
                }
            }
        }

        thread::sleep(Duration::from_millis(TASK_PRODUCER_INTERVAL));
    }
}

fn worker_loop(
    id: usize,
    network: String,
    engine_cell: Arc<ArcSwap<OsrEngine>>,
    receiver_task: Receiver<(String, String)>,
    sender_data: Sender<(String, String, ColdPath)>,
    level_depth: usize
) {
    let _span = info_span!("osr_worker", network = %network, id = %id).entered();
    info!("osr worker started");

    loop {
        match receiver_task.recv() {
            Ok((base_mint, quote_mint)) => {
                let engine = engine_cell.load_full();
                let result = engine.find_the_best_cold_path(
                    base_mint.clone(),
                    quote_mint.clone(),
                    level_depth
                );

                match result {
                    Ok(paths) => {
                        let cold_path = ColdPath {
                            routes: paths,
                            ts: time::SystemTime::now()
                                .duration_since(UNIX_EPOCH)
                                .unwrap()
                                .as_secs()
                                .to_string()
                        };

                        if sender_data.send((base_mint, quote_mint, cold_path)).is_err() {
                            warn!("data channel disconnected, worker exiting");
                            return;
                        };
                    },
                    Err(err) => {
                        warn!(
                            base_mint=base_mint,
                            quote_mint=quote_mint,
                            "Error occured while computing cold path: {}",
                            err
                        );
                    }
                }

            }
            Err(_) => {
                warn!("worker channel disconnected, worker exiting");
                return;
            }
        }
    }
}

fn redis_publisher_loop(
    redis_pool_connection: Pool<RedisConnectionManager>,
    receiver_data: Receiver<(String, String, ColdPath)>,
) {
    let _span = info_span!("redis_publisher").entered();
    info!("redis publisher started");

    loop {
        match receiver_data.recv() {
            Ok(first) => {
                let mut batch = vec![first];
                batch.extend(receiver_data.try_iter());

                let mut conn =match redis_pool_connection.get() {
                    Ok(conn) => conn,
                    Err(err) => { warn!("Error occurred when tried to get conn from pool {err} "); continue }
                };

                let mut pipe = r2d2_redis::redis::pipe();
                let mut queued = 0usize;

                for (base_mint, quote_mint, cold_path) in batch {
                    let payload = match serde_json::to_vec(&cold_path) {
                        Ok(bytes) => bytes,
                        Err(err)  => { warn!(%base_mint, %quote_mint, "serialize failed: {err}"); continue }
                    };

                    pipe.hset(
                        COLD_PATH_KEY,
                        format!("{base_mint}/{quote_mint}"),
                        payload
                    );

                    queued += 1;
                }

                if queued > 0 {
                    if let Err(err) = pipe.query::<()>(&mut *conn) {
                        warn!("publisher pipeline HSET failed: {err}");
                    }
                }
            }
            Err(_) => { warn!("publisher channel disconnected, exiting"); return }
        };

    }
}

fn main() {
    let cli = Cli::parse();

    let network = cli.network.as_str().to_owned();
    let workers_num = cli.workers;
    let level_depth = cli.level_depth;

    if !SUPPORTED_NETWORK_LIST.contains(&network.as_str()) {
        panic!("{network} network is not supported");
    }

    if workers_num == 0 {
        panic!("{network} total workers cannot be 0");
    }

    if level_depth < 3 {
        panic!("{network} level depth cannot be less than 3");
    }

    let _guard = logging::init(&cli.log_dir)
        .expect("failed to initialize logging");

    logging::install_panic_hook();

    info!(%network, workers_num, "osr supervisor starting");

    let client = RedisConnectionManager::new(
        String::from(cli.redis_url.as_str()),
    ).expect("failed to initialize redis connection");
    let redis_conn_pool= Pool::builder()
        .max_size(15)
        .build(client)
        .unwrap();

    let (sender_task, receiver_task) = channel::bounded::<(String, String)>(CHANEL_CAPACITY);
    let (sender_data, receiver_data) = channel::unbounded::<(String, String, ColdPath)>();

    let engine_cell: Arc<ArcSwap<OsrEngine>> = Arc::new(
        ArcSwap::new(
            Arc::new(
                build_osr_engine(&redis_conn_pool, cli.network.as_str()).unwrap()
            )
        )
    );


    let spawn_writer =
        |
            engine_cell: Arc<ArcSwap<OsrEngine>>,
            redis_pool_connection: Pool<RedisConnectionManager>,
            network: String,
            refresh_interval: Duration,
        | {
            thread::Builder::new()
                .name("writer".to_string())
                .spawn( move || {
                    writer_loop(
                        engine_cell,
                        redis_pool_connection,
                        network,
                        refresh_interval
                    )
                })
                .expect("failed to spawn writer thread")
        };

    let spawn_task_producer =
        |
            sender: Sender<(String, String)>,
            engine_cell: Arc<ArcSwap<OsrEngine>>,
            network: String,
        | {
            thread::Builder::new()
                .name("producer".to_string())
                .spawn(move || {
                    tasks_producer_loop(
                        sender,
                        engine_cell,
                        network,
                    )
                })
                .expect("failed to spawn task thread")

        };

    let spawn_worker =
        |
            id: usize,
            network: String,
            engine_cell: Arc<ArcSwap<OsrEngine>>,
            receiver_task: Receiver<(String, String)>,
            sender_data: Sender<(String, String, ColdPath)>,
            level_depth: usize
        | {
            let handle = thread::Builder::new()
                .name(format!("worker-{}", id))
                .spawn(move || {
                    worker_loop(
                        id,
                        network,
                        engine_cell,
                        receiver_task,
                        sender_data,
                        level_depth
                    )
                }).expect("failed to spawn worker thread");

            (id, handle)
        };

    let spawn_redis_publisher =
        |
            redis_pool_connection: Pool<RedisConnectionManager>,
            receiver_data: Receiver<(String, String, ColdPath)>,
        | {
            thread::Builder::new()
                .name("redis_publisher".to_string())
                .spawn(move || {
                    redis_publisher_loop(
                        redis_pool_connection,
                        receiver_data,
                    )
                }).expect("failed to spawn redis publisher thread")
        };


    let mut writer_thread = spawn_writer(
        engine_cell.clone(),
        redis_conn_pool.clone(),
        network.clone(),
        Duration::from_millis(2500),
    );

    let mut producer_thread = spawn_task_producer(
        sender_task.clone(),
        engine_cell.clone(),
        network.clone(),
    );

    let mut worker_threads = (0..workers_num).map( |id| {
        spawn_worker(
            id,
            network.clone(),
            engine_cell.clone(),
            receiver_task.clone(),
            sender_data.clone(),
            level_depth,
        )
    }).collect::<Vec<(usize, JoinHandle<()>)>>();

    let mut redis_publisher_thread = spawn_redis_publisher(
        redis_conn_pool.clone(),
        receiver_data.clone(),
    );

    info!("all threads spawned, supervising");

    loop {
        thread::sleep(HEALTH_CHECK_INTERVAL);

        if writer_thread.is_finished() {
            warn!("writer thread died, respawning");
            writer_thread = spawn_writer(
                engine_cell.clone(),
                redis_conn_pool.clone(),
                network.clone(),
                Duration::from_millis(2500)
            );
        }

        if producer_thread.is_finished() {
            warn!("producer thread died, respawning");
            producer_thread = spawn_task_producer(
                sender_task.clone(),
                engine_cell.clone(),
                network.clone(),
            );
        }

        if redis_publisher_thread.is_finished() {
            warn!("redis publisher thread died, respawning");
            redis_publisher_thread = spawn_redis_publisher(
                redis_conn_pool.clone(),
                receiver_data.clone(),
            );
        }

        for worker_entry in worker_threads.iter_mut() {
            if worker_entry.1.is_finished() {
                warn!(worker_id = worker_entry.0, "worker thread died, respawning");
                *worker_entry = spawn_worker(
                    worker_entry.0,
                    network.clone(),
                    engine_cell.clone(),
                    receiver_task.clone(),
                    sender_data.clone(),
                    level_depth,
                );
            }
        }
    }
}