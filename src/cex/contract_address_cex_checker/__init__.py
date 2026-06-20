"""CEX contract-address resolver: maps each exchange's tradable symbol to its on-chain contract
address per network (network:address -> {exchange: base_symbol}) so a DEX token address resolves to
the CEX symbols that trade it. Runs via `python -m src.main cex_contracts`."""
