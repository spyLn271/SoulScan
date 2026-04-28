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

pub mod order_book;
pub mod address_resolver;