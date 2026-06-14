mod cli;

use clap::Parser;

use rusted_engine::logging;

use crate::cli::{Cli, Mode};

fn main() {
    let cli = Cli::parse();

    let _guard = logging::init(&cli.log_dir)
        .expect("failed to initialize logging");

    logging::install_panic_hook();

    tracing::info!(
        network = cli.network.map(|n| n.as_str()).unwrap_or("none"),
        mode = cli.mode.as_str(),
        workers = cli.workers,
        log_dir = %cli.log_dir.display(),
        "rusted_engine starting"
    );

    match cli.mode {
        Mode::CexDex | Mode::DexCex => {
            let network = cli.network
                .expect("--network is required for dex_cex/cex_dex");
            rusted_engine::scanner::dex_cex::start_cex_dex_scanner_supervisor(
                network.as_str().to_string(),
                cli.workers,
                &cli.redis_url,
            );
        }
        // Mode::CexCex => {
        //     rusted_engine::scanner::cex_cex::start_cex_cex_scanner_supervisor(
        //         cli.workers,
        //         &cli.redis_url,
        //     );
        // }
    }

}
