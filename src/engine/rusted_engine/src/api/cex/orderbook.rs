use r2d2::Pool;
use r2d2_redis::redis::Commands;
use r2d2_redis::RedisConnectionManager;
use r2d2_redis::redis::streams::StreamReadReply;
use r2d2_redis::redis::from_redis_value;

use crate::errors::SoulEngineErrors;
use crate::config::SUPPORTED_CEX_LIST;

#[derive(Debug)]
pub struct OneSideOrderBook {
    pub timestamp_ms: u64,
    pub order_book: Vec<Vec<f64>>,
}

#[derive(Debug)]
pub struct OrderBook {
    pub timestamp_ms: u64,
    pub asks: Vec<Vec<f64>>,
    pub bids: Vec<Vec<f64>>,
}

pub fn get_oder_book(
    redis_conn_pool: &Pool<RedisConnectionManager>,
    exchange: &str,
    symbol: &str,
    order_side: &str
) -> Result<OneSideOrderBook, SoulEngineErrors> {
    if order_side != "asks" && order_side != "bids" {
        return Err(SoulEngineErrors::NotSupportedOrderSide);
    }

    if !SUPPORTED_CEX_LIST.contains(&exchange) {
        return Err(SoulEngineErrors::NotSupportedExchange);
    }

    let mut conn = redis_conn_pool.get()?;

    // better to use active_symbols, as inactive_symbols set is deleted if there is no inactive
    // symbols, and it causes the trouble " could not find the set with a key "
    let key_to_active_symbols: String = format!("symbols_status:{}:spot:active_symbols", exchange);
    let key_to_orderbook: String = format!("stream:orderbook:{exchange}:spot:{symbol}");

    if !conn.sismember(&key_to_active_symbols, symbol)? {
        return Err(SoulEngineErrors::InactiveSymbol);
    }

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

    let timestamp_ms: u64 = from_redis_value(raw_timestamp_ms)?;

    Ok(
        OneSideOrderBook {
            timestamp_ms,
            order_book,
        }
    )
}

pub fn get_whole_order_book(
    redis_conn_pool: &Pool<RedisConnectionManager>,
    exchange: &str,
    symbol: &str,
) -> Result<OrderBook, SoulEngineErrors> {
    if !SUPPORTED_CEX_LIST.contains(&exchange) {
        return Err(SoulEngineErrors::NotSupportedExchange);
    }

    let mut conn = redis_conn_pool.get()?;

    // better to use active_symbols, as inactive_symbols set is deleted if there is no inactive
    // symbols, and it causes the trouble " could not find the set with a key "
    let key_to_active_symbols: String = format!("symbols_status:{}:spot:active_symbols", exchange);
    let key_to_orderbook: String = format!("stream:orderbook:{exchange}:spot:{symbol}");

    if !conn.sismember(&key_to_active_symbols, symbol)? {
        return Err(SoulEngineErrors::InactiveSymbol);
    }

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

    let raw_asks_order_book: String = from_redis_value(
        raw_map
            .get("asks")
            .ok_or(SoulEngineErrors::OrderBookDataNotFound)?
    )?;

    let raw_bids_order_book: String = from_redis_value(
        raw_map
            .get("bids")
            .ok_or(SoulEngineErrors::OrderBookDataNotFound)?
    )?;

    let asks_order_book: Vec<Vec<f64>> = serde_json::from_str(&raw_asks_order_book)?;

    let bids_order_book: Vec<Vec<f64>> = serde_json::from_str(&raw_bids_order_book)?;

    let timestamp_ms: u64 = from_redis_value(raw_timestamp_ms)?;

    Ok(
        OrderBook {
            asks: asks_order_book,
            bids: bids_order_book,
            timestamp_ms,
        }
    )
}