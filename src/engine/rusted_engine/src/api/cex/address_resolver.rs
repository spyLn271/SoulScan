use std::collections::HashMap;
use r2d2::Pool;
use r2d2_redis::redis::Commands;
use r2d2_redis::RedisConnectionManager;

use crate::errors::SoulEngineErrors;
use crate::config::SUPPORTED_NETWORK_LIST;



pub fn get_addr_supported_cex(
    redis_conn_pool: &Pool<RedisConnectionManager>,
    network: &str,
    addr: &str
) -> Result<HashMap<String, String>, SoulEngineErrors> {
    if !SUPPORTED_NETWORK_LIST.contains(&network) {
        return Err(SoulEngineErrors::NotSupportedNetwork);
    }
    
    let mut conn = redis_conn_pool.get()?;

    let normalized_addr = format!("{}:{}", network, normalize(addr));

    let raw_cex_dict: String = conn.hget("cex:contract_index", &normalized_addr)?;

    let cex_dict: HashMap<String, String> = serde_json::from_str(&raw_cex_dict)?;

    Ok(cex_dict)
}


fn normalize(
    addr: &str
) -> String {
    if addr.len() == 42 && addr.starts_with("0x") {
        addr.to_ascii_lowercase()
    } else {
        addr.to_string()
    }
}