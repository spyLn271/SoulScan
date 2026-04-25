// 1. Orderbook streams — live depth (the hot path)
//
// Key: stream:orderbook:{exchange}:{market_type}:{symbol} — Redis Stream, MAXLEN ~10 per symbol.
//
// ┌──────────────┬───────────────────┬────────────────────────────────────────────────────────────┐
// │    Field     │       Type        │                           Notes                            │
// ├──────────────┼───────────────────┼────────────────────────────────────────────────────────────┤
// │ timestamp_ms │ i64 (string)      │ producer's wall clock                                      │
// ├──────────────┼───────────────────┼────────────────────────────────────────────────────────────┤
// │ symbol       │ string            │ uppercased; KuCoin uses raw BTC-USDT form                  │
// ├──────────────┼───────────────────┼────────────────────────────────────────────────────────────┤
// │ bids         │ JSON string       │ [[price, amount], ...] — both as strings, descending price │
// ├──────────────┼───────────────────┼────────────────────────────────────────────────────────────┤
// │ asks         │ JSON string       │ [[price, amount], ...] — both as strings, ascending price  │
// ├──────────────┼───────────────────┼────────────────────────────────────────────────────────────┤
// │ worker_id    │ string (optional) │ base_connector only — "none" or int as string              │
// ├──────────────┼───────────────────┼────────────────────────────────────────────────────────────┤
// │ update_id    │ string (optional) │ KuCoin only — exchange sequence                            │
// └──────────────┴───────────────────┴────────────────────────────────────────────────────────────┘
//
// Read patterns:
// - Latest snapshot: XREVRANGE key + - COUNT 1
// - Tailing: XREAD BLOCK 0 STREAMS key $ (block forever for new entries)
// - Discovery: KEYS stream:orderbook:* or maintain your own list
//
// Lowercase exchange and market_type, uppercase symbol when constructing the key (matches src/CEX/CEXAPI.py:47 and src/CEX/stream_watcher_function.py:89 exactly).
//
// 11 exchanges currently produced: bybit, okx, mexc, bingx, bitget, bitmart, coinex, htx, lbank, gateio, kucoin. Spot for all; futures only on bybit/okx/kucoin/gateio.
//
// Number values in bids/asks are quoted strings — keep them as strings, parse to Decimal only when arithmetic-needed.
//
// 2. Market-data hashes — symbol universe + funding/mark
//
// Key: {market_type}-market-data:{exchange} — Redis Hash, fully replaced every 1–3 seconds.
//
// Field = symbol, value = JSON. Reserved field _version is a nanosecond timestamp — filter out any field starting with _ before treating it as a symbol.
//
// Spot value shape:
// { "24h_volume_usdt": "123456.78", "best_bid": "50000.1",
// "best_ask": "50000.2", "lastPrice": "50000.15", "dumpScale": 2 }
//
// Futures value shape (extra fields):
// { "24h_volume_usdt": "...", "best_bid": "...", "best_ask": "...",
// "lastPrice": "...", "indexPrice": "...", "markPrice": "...",
// "funding_rate_percent": 0.01, "next_funding_time": 1729015200 }
//
// funding_rate_percent is already multiplied ×100 at write time, so 0.01 means 0.01%, not 1%. next_funding_time is Unix seconds (epoch).
//
// Read patterns:
// - Full snapshot: HGETALL {market_type}-market-data:{exchange} → iterate fields, skip _version
// - Single symbol: HGET key SYMBOL
// - Change detection: poll HGET key _version — nanosecond ts changes on each rewrite (cheap)
//
// 12 spot hashes (everything except hyperliquid/asterdex/dydx). 13 futures hashes (everything except lbank/dydx).
//
// Symbol formats are per-exchange raw — Bybit BTCUSDT, KuCoin BTC-USDT, Gate.io BTC_USDT, OKX spot BTC-USDT / OKX futures BTC-USDT-SWAP. Don't try to normalize blindly.
//
// 3. Contract index — CEX ↔ on-chain mapping
//
// Key: cex:contract_index — Redis Hash, atomically rebuilt every 20 minutes.
//
// Field = contract address, value = JSON of which CEXes list the corresponding token:
// {"binance": "USDC", "bybit": "USDC", "kucoin": "USDC", ...}
//
// Critical normalization rule (already applied write-side):
// - EVM: lowercased (0x + 40 hex chars)
// - Solana / non-EVM: case preserved verbatim (base58 is case-sensitive)
//
// Apply the same on the Rust side at lookup time:
// fn normalize(addr: &str) -> Cow<str> {
//     if addr.len() == 42 && addr.starts_with("0x")
//         && addr[2..].chars().all(|c| c.is_ascii_hexdigit()) {
//         Cow::Owned(addr.to_ascii_lowercase())
//     } else {
//         Cow::Borrowed(addr)
//     }
// }
//
// Supporting keys (read-only, optional):
// - cex:data:{exchange} (String, JSON array) — raw per-exchange dump of {coin, network, contract_address} triples. Useful if you need network info (the index hash drops the network field,
// so two chains with the same address would collide; rare but real).
// - cex:last_update:{exchange} (String, Unix seconds) — staleness check.
// - cex:coins:{exchange} (Hash) — observed live; coin → details. Same data as cex:data:* but as a hash.
//
// 10 exchanges resolved: binance, bybit, okx, mexc, bingx, coinex, kucoin, bitget, htx, gateio.
//
// 4. Auxiliary signals (optional)
//
// - symbols_status:{exchange}:{market_type}:active_symbols — Set of symbols currently producing orderbook ticks. Fresh-data signal.
// - symbols_status:{exchange}:{market_type}:inactive_symbols — Set of symbols disconnected/failing. Don't bother subscribing to these.
// - watchdog:{exchange}:error_queue — List of producer errors. Your reader can ignore; this is for the (not-yet-merged) watchdog.
//
// Operational requirements
//
// - Redis at localhost:6379 by default (override via REDIS_HOST / REDIS_PORT env, or whatever your Rust config does).
// - All three SoulScan supervisors must be running for live data:
// - python -m scripts.run_supervisor cex_orderbooks — feeds stream:orderbook:*
// - python -m scripts.run_supervisor cex_market_data — feeds *-market-data:*
// - python -m scripts.run_supervisor cex_contracts — feeds cex:contract_index
// - Or the matching systemd units: soulscan-cex-{orderbooks,market-data,contracts}.service.
// - The contract resolver's first cycle takes ~10 minutes (OKX/Gate.io are sequential per-token); orderbooks and market-data populate within seconds.
//
// Rust crate suggestions
//
// - redis (0.27+) for sync, redis::aio or fred for async. fred has nicer pub-sub + connection-pool ergonomics if you'll fan out.
// - serde + serde_json for the bid/ask/value parsing.
// - rust_decimal if you need arithmetic on prices/amounts; otherwise keep them as strings.
// - For XREAD BLOCK 0, set the connection's read timeout to None — redis-rs defaults can fight you here.
// - For typed CEX-side keys, generate a small enum Exchange { Bybit, Okx, ... } and enum Market { Spot, Futures }, then impl Display to lowercase strings — this prevents typos in key
// construction.
// 
// Stuff to avoid
//
// - Don't lowercase bid/ask price strings (case isn't relevant) or symbols that aren't EVM addresses.
// - Don't assume bids is sorted descending in every exchange — most are normalized to that, but the producer's requires_orderbook_normalization flag covers a few that aren't. Sort
// defensively if you depend on order.
// - Don't read cex:contract_index to get the network — it's collapsed. Use cex:data:{exchange} or cex:coins:{exchange} if you need that.
// - Don't treat _version as a symbol when iterating market-data hashes.
//
// That's the entire reader contract — three keys families plus metadata. Write the API, then verify against the live data: redis-cli HLEN cex:contract_index should show 13k+, redis-cli
// KEYS 'stream:orderbook:bybit:spot:*' | wc -l should show ~hundreds when the orderbook supervisor is running.