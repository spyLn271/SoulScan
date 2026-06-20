"""
cex_v2 — clean-room rebuild of the CEX order-book producer.

Self-contained: only parts proven in production are carried over (orphan guards, the SOCKS5
connect helper, backoff, and the Redis key contract the Rust engine depends on). The connector
base and supervisor are rebuilt from the invariants in SoulAudit/hardening/ORDERBOOK_PRODUCER_SPEC.md.
Exchanges are onboarded one by one; the legacy src/cex path keeps running until each is migrated.
"""
