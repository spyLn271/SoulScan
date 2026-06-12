mod cli;

use std::path::PathBuf;

use rusted_engine::logging;

fn main() {
    let log_dir = std::env::var("ENGINE_LOG_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("logs"));

    let _guard = logging::init(&log_dir)
        .expect("failed to initialize logging");

    logging::install_panic_hook();

    tracing::info!(log_dir = %log_dir.display(), "rusted_engine starting");

    // TEST: temporary hardcoded start until cli.rs is implemented
    rusted_engine::scanner::dex_cex::start_cex_dex_scanner_supervisor("solana".to_string(), 2);

    // parse CLI (-n network, -m mode, -w workers, -l log_dir) and start:
    // rusted_engine::scanner::dex_cex::start_cex_dex_scanner_supervisor(network, workers);
}
