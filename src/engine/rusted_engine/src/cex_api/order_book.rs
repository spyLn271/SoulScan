use r2d2::Pool;
use r2d2_redis::redis::Commands;
use r2d2_redis::RedisConnectionManager;
use r2d2_redis::redis::streams::StreamReadReply;
use r2d2_redis::redis::from_redis_value;

use crate::errors::SoulEngineErrors;
use crate::config::SUPPORTED_CEX_LIST;

#[derive(Debug)]
pub struct OrderBook {
    pub timestamp_ms: u128,
    pub order_book: Vec<Vec<f64>>,
}

pub fn get_oder_book(
    redis_conn_pool: &Pool<RedisConnectionManager>,
    exchange: &str,
    symbol: &str,
    order_side: &str
) -> Result<OrderBook, SoulEngineErrors> {
    if order_side != "asks" && order_side != "bids" {
        return Err(SoulEngineErrors::NotSupportedOrderSide);
    }

    if !SUPPORTED_CEX_LIST.contains(&exchange) {
        return Err(SoulEngineErrors::NotSupportedExchange);
    }

    let mut conn = redis_conn_pool.get()?;

    let key_to_orderbook: String = format!("stream:orderbook:{exchange}:spot:{symbol}");

    let raw_data: StreamReadReply = conn
        .xread(&[key_to_orderbook], &["+"])?;

    let stream =  raw_data.keys
        .first()
        .ok_or(SoulEngineErrors::StreamWasNotFound)?;

    let entry = stream.ids
        .first()
        .ok_or(SoulEngineErrors::NoEntry)?;

    let raw_map = entry.map
        .clone();

    let raw_timestamp_ms = raw_map
        .get("timestamp_ms")
        .ok_or(SoulEngineErrors::OrderBookDataNotFound)?;

    let raw_order_book = raw_map
        .get(order_side)
        .ok_or(SoulEngineErrors::OrderBookDataNotFound)?;

    let raw_order_book_string: String = from_redis_value(raw_order_book)?;

    let order_book: Vec<Vec<f64>> = serde_json::from_str(&raw_order_book_string)?;

    let timestamp_ms: u128 = from_redis_value(raw_timestamp_ms)?;

    Ok(
        OrderBook {
            timestamp_ms,
            order_book,
        }
    )
}