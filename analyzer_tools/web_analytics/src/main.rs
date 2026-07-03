mod cli;
mod errors;
mod handlers;

use std::time::Duration;
use clap::Parser;

use axum::{
    routing::{get, },
    Router,
};

use sqlx::postgres::Postgres;
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

    let app_state = create_app_state(&cli).await;

    let api = Router::new()
        .nest("/api", handlers::dex::routes(app_state));
    
    let app: Router<()> = Router::new()
        .route("/", get(|| async { "Hello, World!" }))
        .merge(api);

    let listener = tokio::net::TcpListener::bind(("127.0.0.1", cli.port))
        .await
        .unwrap();

    axum::serve(listener, app).await.unwrap();
}
