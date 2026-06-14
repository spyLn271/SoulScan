use std::path::PathBuf;

use clap::{Parser, ValueEnum};

#[derive(Debug, Parser)]
#[command(name = "rusted_engine", version, about, long_about = None)]
pub struct Cli {
    #[arg(
        short = 'n',
        long = "network",
        value_enum,
        required_if_eq_any = [("mode", "dex_cex"), ("mode", "cex_dex")]
    )]
    pub network: Option<Network>,

    #[arg(short = 'm', long = "mode", value_enum)]
    pub mode: Mode,

    #[arg(short = 'w', long = "workers", default_value_t = default_workers())]
    pub workers: usize,

    #[arg(short = 'l', long = "log-dir", env = "ENGINE_LOG_DIR", default_value = "../test_data/logs")]
    pub log_dir: PathBuf,

    #[arg(long = "redis-url", env = "REDIS_URL", default_value = "redis://127.0.0.1:6379/0")]
    pub redis_url: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, ValueEnum)]
pub enum Network {
    Eth,
    Base,
    Arbitrum,
    Bsc,
    Solana,
}

impl Network {
    pub fn as_str(self) -> &'static str {
        match self {
            Network::Eth => "eth",
            Network::Base => "base",
            Network::Arbitrum => "arbitrum",
            Network::Bsc => "bsc",
            Network::Solana => "solana",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, ValueEnum)]
pub enum Mode {
    #[value(name = "dex_cex")]
    DexCex,
    #[value(name = "cex_dex")]
    CexDex,

    // #[value(name = "cex_cex")]
    // CexCex,
}

impl Mode {
    pub fn as_str(self) -> &'static str {
        match self {
            Mode::DexCex => "dex_cex",
            Mode::CexDex => "cex_dex",
            // Mode:CexCex => "cex_cex"
        }
    }
}

fn default_workers() -> usize {
    std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(4)
}
