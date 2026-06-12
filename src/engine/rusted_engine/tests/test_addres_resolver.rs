use std::collections::HashMap;
use rusted_engine::api::cex::address_resolver::get_addr_supported_cex;
use r2d2_redis::RedisConnectionManager;
use r2d2::Pool;

use rusted_engine::api::dex::snapshot::get_token_addresses;


fn token_addr_resolution_analyzer(redis_conn_pool: &Pool<RedisConnectionManager>, network: &str) {
    let eth_tokens = get_token_addresses(
        redis_conn_pool,
        network
    ).unwrap();

    let mut founded_addresses_count = 0;
    let mut unfounded_addresses_count = 0;

    let mut avg_cex_count = 0;

    for (idx, data) in eth_tokens.iter() {
        let cex_token_data = get_addr_supported_cex(
            redis_conn_pool,
            network,
            data.0.as_str()
        );

        match &cex_token_data {
            Ok(cex) => {
                founded_addresses_count += 1;
                avg_cex_count += cex.len();
            },
            Err(_) => {unfounded_addresses_count += 1}
        }

        println!("{:?}", data.0.as_str());
        println!("{:?}", cex_token_data);
        println!("_____________________________________________________");
    }

    println!("found {} addresses", founded_addresses_count);
    println!("unfound {} addresses", unfounded_addresses_count);
    println!("avg_cex_count {}", (avg_cex_count as f32) / (founded_addresses_count as f32));
}

#[test]
fn test_addr_resolver() {
    let client = RedisConnectionManager::new("redis://127.0.0.1:6379/0")
        .unwrap();
    let redis_conn_pool = Pool::builder()
        .max_size(10)
        .build(client)
        .unwrap();

    token_addr_resolution_analyzer(&redis_conn_pool, "arbitrum");
}