use std::backtrace::Backtrace;
use std::io::stdout;
use std::path::Path;


use tracing_appender::{
    non_blocking::{NonBlocking, WorkerGuard},
    rolling::{ RollingFileAppender, Rotation }
};
use tracing_subscriber::{
    fmt, EnvFilter, prelude::*
};

pub fn init(log_dir: &Path) -> Result<WorkerGuard, Box<dyn std::error::Error>> {
    std::fs::create_dir_all(log_dir)?;

    let file_appender = RollingFileAppender::builder()
        .rotation(Rotation::HOURLY)
        .max_log_files(7)
        .filename_suffix("log")
        .filename_prefix("web_analytics")
        .build(log_dir)?;

    let (non_blocking, worker) = NonBlocking::new(file_appender);

    let filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new("info,web_analytics=trace"));

    tracing_subscriber::registry()
        .with(filter)
        .with(
            fmt::layer()
                .with_writer(non_blocking)
                .with_ansi(false)
                .with_target(true)
                .with_thread_names(true)
        )
        .with(
            fmt::layer()
                .with_writer(stdout)
                .with_thread_names(true)
        )
        .init();

    Ok(worker)
}

pub fn install_panic_hook() {
    std::panic::set_hook(Box::new(|info| {
        let backtrace = Backtrace::capture();

        tracing::error!(
            thread = %std::thread::current().name().unwrap_or("unnamed"),
            %info,
            %backtrace,
            "thread panicked"
        )
    }));
}