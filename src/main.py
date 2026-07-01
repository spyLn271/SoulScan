import sys
import multiprocessing
from src.supervisors import (
    RUN_METADATA_FETCHERS,
    RUN_STATE_FETCHERS,
    RUN_CEX_CONTRACTS,
)

multiprocessing.set_start_method('spawn', force=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.main <supervisor_name>")
        print("Available supervisors:")
        print("  metadata_fetcher  - Fetches pool metadata from dex APIs")
        print("  state_fetcher     - Fetches live pool state via RPC")
        print("  osr_eth          - Computes optimal swap routes for Ethereum")
        print("  osr_solana        - Computes optimal swap routes for Solana")
        print("  osr_bsc          - Computes optimal swap routes for Binance Smart Chain")
        print("  osr_base         - Computes optimal swap routes for Base")
        print("  osr_arbitrum     - Computes optimal swap routes for Arbitrum")
        print("  cex_contracts     - Maps cex coin tickers to on-chain contract addresses")
        sys.exit(1)

    supervisor = sys.argv[1].lower()

    if supervisor == "metadata_fetcher":
        RUN_METADATA_FETCHERS()
    elif supervisor == "state_fetcher":
        RUN_STATE_FETCHERS()
    elif supervisor == "cex_contracts":
        RUN_CEX_CONTRACTS()
    else:
        print(f"Unknown supervisor: {supervisor}")
        sys.exit(1)


if __name__ == "__main__":
    main()