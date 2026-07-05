use std::collections::HashMap;
use std::sync::{Arc};

use crate::errors::WebErrors;
use crate::AppState;

use axum::{
    extract::{
        ws::{ WebSocket, WebSocketUpgrade, Message },
        State
    },
    routing::any,
    response::{ Response },
    Router
};

use deadpool_redis::{
    redis::{AsyncTypedCommands, from_redis_value}
};
use futures_util::{sink::SinkExt, stream::{StreamExt, SplitSink}};

use serde::{Deserialize, Serialize};
use tokio::{
    task::JoinHandle,
    sync::Mutex
};
use serde_json::{from_str, };

pub fn router(app_state: AppState) -> Router {
    Router::new()
        .route("/ws", any(handler))
        .with_state(app_state)
}

async fn handler(
    ws: WebSocketUpgrade,
    State(app_state): State<AppState>
) -> Response {


    ws.on_upgrade(|socket| { handle_socket(socket, app_state)})
}

#[derive(Deserialize)]
#[serde(rename_all = "lowercase", tag = "action")]
enum ClientMessage {
    Subscribe {
        exchange: Exchange,
        symbol: String,
        market: Market,
        latency: u64,
    },
    Unsubscribe {
        exchange: Exchange,
        symbol: String,
        market: Market,
    }
}

#[derive(Debug, Serialize)]
pub struct OrderBook {
    pub timestamp_ms: u64,
    pub asks: Vec<Vec<f64>>,
    pub bids: Vec<Vec<f64>>,
}

#[derive(Deserialize, Copy, Clone)]
#[serde(rename_all = "lowercase", tag = "market_type")]
enum Market {
    Spot,
    Futures
}

#[derive(Deserialize, Copy, Clone)]
#[serde(rename_all = "lowercase", tag = "exchange_type")]
enum Exchange {
    Binance,
    Bybit,
    Okx,
    Mexc,
    Bingx,
    Bitget,
    Bitmart,
    Coinex,
    Htx,
    Lbank,
    Gateio,
    Kucoin
}

async fn handle_socket(
    socket: WebSocket,
    app_state: AppState
) {
    let mut connected_steams: HashMap<String, JoinHandle<()>> = HashMap::new();

    let (sender, mut receiver) = socket.split();

    let sender = Arc::new(Mutex::new(sender));

    while let Some(msg) = receiver.next().await {
        let msg = if let Ok(msg) = msg {
            msg
        } else {
            return;
        };

        let Message::Text(text) = msg else { continue };

        let action = if let Ok(act) = from_str::<ClientMessage>(text.as_str()) {
            act
        } else {
            continue
        };

        match action {
            ClientMessage::Subscribe { exchange, symbol, market, latency} => {
                let key = format!("{}{symbol}{}", exchange.as_str(), market.as_str());

                if connected_steams.contains_key(&key) { continue };

                let feeder = tokio::spawn(
                    feeder(
                        symbol.clone(),
                        latency,
                        market,
                        exchange,
                        sender.clone(),
                        app_state.redis_pool_conn.clone()
                    )
                );

                connected_steams.insert(key, feeder);
            }
            ClientMessage::Unsubscribe { exchange, symbol, market } => {
                let key = format!("{}{symbol}{}", exchange.as_str(), market.as_str());

                if let Some(feeder) = connected_steams.remove(&key) {
                    feeder.abort();
                }
            }
        };
    }


    for (_, feeder) in connected_steams {
        feeder.abort();
    }
}

async fn feeder(
    symbol: String,
    latency: u64,
    market: Market,
    exchange: Exchange,
    sender: Arc<Mutex<SplitSink<WebSocket, Message>>>,
    redis_conn_pool: deadpool_redis::Pool,
) {
    let key_to_active_symbols: String = format!("symbols_status:{}:{}:active_symbols", exchange.as_str(), market.as_str());
    let key_to_orderbook: String = format!("stream:orderbook:{}:{}:{}", exchange.as_str(), market.as_str(), symbol.as_str());

    let mut conn = redis_conn_pool.get().await.unwrap();

    let mut guard = sender.lock().await;

    if !conn.sismember(&key_to_active_symbols, symbol.as_str()).await.unwrap() {
        if guard.send(Message::Text("this symbol is inactive".into())).await.is_err() {
            return;
        }
    };

    drop(conn);
    drop(guard);

    loop {
        let orderbook = if let Ok(orderbook) = get_orderbook(
            redis_conn_pool.clone(),
            key_to_orderbook.clone()
        ).await {
            orderbook
        } else {
            tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
            continue
        };

        let json = serde_json::to_string(&orderbook)
            .expect("OrderBook serialization");

        let mut guard = sender.lock().await;

        if guard.send(Message::Text(json.into())).await.is_err() {
            return;
        }

        drop(guard);

        tokio::time::sleep(tokio::time::Duration::from_millis(latency)).await;
    }
}


async fn get_orderbook(
    redis_conn_pool: deadpool_redis::Pool,
    key_to_orderbook: String,
) -> Result<OrderBook, WebErrors> {
    let mut conn = redis_conn_pool.get().await?;

    let raw_data = conn
        .xread(&[key_to_orderbook.as_str()], &["+"])
        .await?
        .ok_or(WebErrors::Error("No steam was found".to_string()))?;

    drop(conn);

    let stream = raw_data
        .keys
        .first()
        .ok_or(WebErrors::Error("No steam was found".to_string()))?;

    let entry = stream
        .ids
        .first()
        .ok_or(WebErrors::Error("No entry was found".to_string()))?;

    let raw_map = entry
        .map
        .clone();

    let raw_timestamp_ms = raw_map
        .get("timestamp_ms")
        .ok_or(WebErrors::Error("No timestamp was found".to_string()))?
        .clone();

    let raw_asks_order_book: String = from_redis_value(
        raw_map
            .get("asks")
            .ok_or(WebErrors::Error("No asks orderbook was found".to_string()))?
            .clone()
    )?;

    let raw_bids_order_book: String = from_redis_value(
        raw_map
            .get("bids")
            .ok_or(WebErrors::Error("No bids orderbook was found".to_string()))?
            .clone()
    )?;

    let asks_order_book: Vec<Vec<f64>> = from_str(&raw_asks_order_book)?;

    let bids_order_book: Vec<Vec<f64>> = from_str(&raw_bids_order_book)?;

    let timestamp_ms: u64 = from_redis_value(raw_timestamp_ms)?;

    Ok(
        OrderBook {
            asks: asks_order_book,
            bids: bids_order_book,
            timestamp_ms,
        }
    )
}




impl Exchange {
    fn as_str(&self) -> &'static str {
        match self {
            Exchange::Binance => "binance",
            Exchange::Bybit => "bybit",
            Exchange::Okx => "okx",
            Exchange::Mexc => "mexc",
            Exchange::Bingx => "bingx",
            Exchange::Bitget => "bitget",
            Exchange::Bitmart => "bitmart",
            Exchange::Coinex => "coinex",
            Exchange::Htx => "htx",
            Exchange::Lbank => "lbank",
            Exchange::Gateio => "gateio",
            Exchange::Kucoin => "kucoin",
        }
    }
}

impl Market {
    fn as_str(&self) -> &'static str {
        match self {
            Market::Spot => "spot",
            Market::Futures => "futures",
        }
    }
}