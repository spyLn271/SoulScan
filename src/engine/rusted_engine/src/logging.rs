use std::path::Path;

use tracing_appender::non_blocking::WorkerGuard;
use tracing_appender::rolling::{RollingFileAppender, Rotation};
use tracing_subscriber::{fmt, EnvFilter};
use tracing_subscriber::prelude::*;

pub fn init(log_dir: &Path) -> Result<WorkerGuard, Box<dyn std::error::Error>> {
    std::fs::create_dir_all(log_dir)?;

    let file_appender = RollingFileAppender::builder()
        .rotation(Rotation::HOURLY)
        .filename_prefix("rusted_engine")
        .filename_suffix("log")
        .max_log_files(7)
        .build(log_dir)?;

    let (file_writer, guard) = tracing_appender::non_blocking(file_appender);

    let filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new("info,rusted_engine=debug"));

    tracing_subscriber::registry()
        .with(filter)
        .with(
            fmt::layer()
                .with_writer(file_writer)
                .with_ansi(false)
                .with_target(true)
                .with_thread_names(true)
        )
        .with(
            fmt::layer()
                .with_writer(std::io::stderr)
                .with_thread_names(true)
        )
        .init();

    Ok(guard)
}

pub fn install_panic_hook() {
    std::panic::set_hook(Box::new(|panic_info| {
        let backtrace = std::backtrace::Backtrace::capture();

        tracing::error!(
            thread = %std::thread::current().name().unwrap_or("unnamed"),
            %panic_info,
            %backtrace,
            "thread panicked"
        );
    }));
}
