use std::path::PathBuf;

use clap::{Parser, ValueEnum};

#[derive(Debug, Parser)]
#[command(name = "rusted_osr", version, about, long_about = None)]
pub struct Cli {
    #[arg(short = 'n', long = "network", value_enum)]
    pub network: Network,

    #[arg(short = 'w', long = "workers", default_value_t = 5)]
    pub workers: usize,

    #[arg(short = 'd', long = "level-depth", default_value_t = 6)]
    pub level_depth: usize,

    #[arg(short = 'l', long = "log-dir", env = "OSR_LOG_DIR", default_value = "../logs")]
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