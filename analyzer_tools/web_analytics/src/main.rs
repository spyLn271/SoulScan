mod cli;
mod errors;
mod handlers;
mod logging;

use std::time::Duration;
use clap::Parser;

use axum::{
    Router,
};
use tower_http::{
    services::{ ServeDir, ServeFile }
};

use sqlx::postgres::Postgres;
use tower_http::trace::TraceLayer;
use crate::cli::Cli;

#[derive(Debug, Clone)]
struct AppState {
    redis_pool_conn: deadpool_redis::Pool,
    blocking_redis_pool_conn: r2d2::Pool<r2d2_redis::RedisConnectionManager>,
    pg_pool_conn: sqlx::Pool<Postgres>
}


async fn create_app_state(cli: &Cli) -> AppState {
    let pg_pool_conn = sqlx::postgres::PgPoolOptions::new()
        .max_connections(10)
        .connect(cli.postgres_url.as_str())
        .await
        .unwrap();

    let mut cfg = deadpool_redis::Config::from_url(cli.redis_url.as_str());

    cfg.pool = Some(
        deadpool_redis::PoolConfig {
            max_size: 100,
            timeouts: deadpool_redis::Timeouts {
                wait: None,
                create: Some(Duration::from_secs(10)),
                recycle: Some(Duration::from_secs(10))
            },
            ..Default::default()
        }
    );

    let redis_pool_conn = cfg
        .create_pool(Some(deadpool_redis::Runtime::Tokio1))
        .unwrap();

    let manager = r2d2_redis::RedisConnectionManager::new(cli.redis_url.as_str()).unwrap();

    let blocking_redis_pool_conn = r2d2::Pool::builder()
        .max_size(15)
        .build(manager)
        .unwrap();

    AppState {
        redis_pool_conn,
        blocking_redis_pool_conn,
        pg_pool_conn
    }
}


#[tokio::main(flavor = "multi_thread", worker_threads = 8)]
async fn main() {
    let cli = Cli::parse();

    let _guard = logging::init(&cli.log_dir)
        .expect("logging initialization failed");

    logging::install_panic_hook();

    tracing::info!(
        "Starting server at address {}:{}",
        &cli.ip,
        &cli.port
    );

    let app_state = create_app_state(&cli).await;

    let api = Router::new()
        .nest("/api", handlers::dex::routes(app_state.clone()))
        .route_layer(handlers::login::AuthLayer::new());

    let spa = ServeDir::new("frontend/dist")
        .not_found_service(ServeFile::new("frontend/dist/index.html"));

    
    let app: Router<()> = Router::new()
        .merge(api)
        .merge(handlers::ws_orderbooks::router(app_state.clone()))
        .merge(handlers::login::routes(app_state.clone()))
        .layer(
            TraceLayer::new_for_http()
        )
        .fallback_service(spa);

    let listener = tokio::net::TcpListener::bind((cli.ip, cli.port))
        .await
        .unwrap();

    axum::serve(listener, app).await.unwrap();
}
