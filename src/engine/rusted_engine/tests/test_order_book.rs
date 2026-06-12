use r2d2::Pool;
use r2d2_redis::RedisConnectionManager;
use rusted_engine::config;
use rusted_engine::api::cex;


#[test]
fn test_bids_order_side() {
    let client = RedisConnectionManager::new("redis://127.0.0.1:6379/0").unwrap();
    let redis_conn_pool = Pool::builder()
        .max_size(10)
        .build(client)
        .unwrap();


    for cex in config::SUPPORTED_CEX_LIST {
        println!("{cex} BIDS");
        let order_book = cex::orderbook::get_oder_book(
            &redis_conn_pool,
            cex,
            "SOLUSDT",
            "bids"
        );
        println!("{order_book:?}");
        println!("_________________________________");
    }
}

#[test]
fn test_asks_order_side() {
    let client = RedisConnectionManager::new("redis://127.0.0.1:6379/0").unwrap();
    let redis_conn_pool = Pool::builder()
        .max_size(10)
        .build(client)
        .unwrap();


    for cex in config::SUPPORTED_CEX_LIST {
        println!("{cex} ASKS");
        let order_book = cex::orderbook::get_oder_book(
            &redis_conn_pool,
            cex,
            "SOLUSDT",
            "asks"
        );
        println!("{order_book:?}");
        println!("_________________________________");
    }
}

#[test]
fn test_whole_order_book() {
    let client = RedisConnectionManager::new("redis://127.0.0.1:6379/0").unwrap();
    let redis_conn_pool = Pool::builder()
        .max_size(10)
        .build(client)
        .unwrap();


    for cex in config::SUPPORTED_CEX_LIST {
        println!("{cex} ASKS");
        let order_book = cex::orderbook::get_whole_order_book(
            &redis_conn_pool,
            cex,
            "SOLUSDT",
        );
        println!("{order_book:?}");
        println!("_________________________________");
    }
}