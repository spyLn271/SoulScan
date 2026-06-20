"""cex_v2 market-data feeder — REST-poll ticker feeders that populate the
{market}-market-data:{exchange} Redis hashes (the symbol universe + subscribe-metadata source
the order-book fetcher reads). Hardened from the SoulAudit/hardening/MARKET_DATA_AUDIT.md findings."""
