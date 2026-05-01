use rusted_engine::cex_api::address_resolver::get_addr_supported_cex;
use r2d2_redis::RedisConnectionManager;
use r2d2::Pool;


#[test]
fn test_addr_resolver() {
    let client = RedisConnectionManager::new("redis://127.0.0.1:6379/0")
        .unwrap();
    let redis_conn_pool = Pool::builder()
        .max_size(10)
        .build(client)
        .unwrap();

    let addr_to_test: [&str; 4] = [
        "So11111111111111111111111111111111111111112",
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "0xa0B86991C6218b36c1d19D4A2E9eB0ce3606eb48",
        "0xdac17f958d2ee523a2206206994597c13d831ec7"
    ];

    for addr in addr_to_test {
        let resolved_list = get_addr_supported_cex(
            &redis_conn_pool,
            addr
        );

        println!("{resolved_list:?}")
    }

}