use clap::Parser;

use std::path::PathBuf;

#[derive(Debug, Parser)]
#[command(name = "soul_web_analyzer", version, about, author)]
pub struct Cli {
    #[arg(short = 'l', long = "log-dir", env = "OSR_LOG_DIR", default_value = "./logs")]
    pub log_dir: PathBuf,

    #[arg(long = "redis-url", env = "REDIS_URL", default_value = "redis://127.0.0.1:6379/0")]
    pub redis_url: String,

    #[arg(long = "postgres-url", env = "POSTGRES_URL", default_value = "postgres://postgres:postgres@127.0.0.1:5432/postgres")]
    pub postgres_url: String,
    
    #[arg(short = 'p', long = "port", default_value = "3000")]
    pub port: u16,
    
    #[arg(long = "ip", default_value = "127.0.0.1")]
    pub ip: String,
}