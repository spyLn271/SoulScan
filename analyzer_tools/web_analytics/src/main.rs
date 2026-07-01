mod cli;
mod errors;
mod handlers;

use clap::Parser;

use axum::{
    routing::{get, },
    Router,
};
use r2d2_redis::RedisConnectionManager;
use sqlx::postgres::Postgres;
use crate::cli::Cli;

#[derive(Debug, Clone)]
struct AppState {
    redis_pool_conn: r2d2::Pool<RedisConnectionManager>,
    pg_pool_conn: sqlx::Pool<Postgres>
}


async fn create_app_state(cli: &Cli) -> AppState {
    let pg_pool_conn = sqlx::postgres::PgPoolOptions::new()
        .max_connections(10)
        .connect(cli.postgres_url.as_str())
        .await
        .unwrap();

    let manager = RedisConnectionManager::new(cli.redis_url.as_str()).unwrap();
    
    let redis_pool_conn = r2d2::Pool::builder()
        .max_size(15)
        .build(manager)
        .unwrap();

    AppState {
        redis_pool_conn,
        pg_pool_conn
    }
}


#[tokio::main]
async fn main() {
    let cli = cli::Cli::parse();

    let app_state = crate::create_app_state(&cli).await;
    
    let app: Router<()> = Router::new()
        .route("/", get(|| async { "Hello, World!" }));

    let listener = tokio::net::TcpListener::bind(("127.0.0.1", 3000))
        .await
        .unwrap();

    axum::serve(listener, app).await.unwrap();
}
