import sys
import multiprocessing
from src.supervisors import RUN_METADATA_FETCHERS, RUN_STATE_FETCHERS, SolanaOnlineSmartRouterSupervisor, RUN_CEX_ORDERBOOKS, RUN_CEX_MARKET_DATA, RUN_CEX_CONTRACTS

multiprocessing.set_start_method('spawn', force=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.main <supervisor_name>")
        print("Available supervisors:")
        print("  metadata_fetcher  - Fetches pool metadata from dex APIs")
        print("  state_fetcher     - Fetches live pool state via RPC")
        print("  online_smart_router      - Computes optimal swap routes")
        print("  cex_orderbooks    - Streams cex orderbooks to Redis for the reader contract")
        print("  cex_market_data   - Refreshes {market_type}-market-data:{exchange} Redis hashes")
        print("  cex_contracts     - Maps cex coin tickers to on-chain contract addresses")
        sys.exit(1)

    supervisor = sys.argv[1].lower()

    if supervisor == "metadata_fetcher":
        RUN_METADATA_FETCHERS()
    elif supervisor == "state_fetcher":
        RUN_STATE_FETCHERS()
    elif supervisor == "online_smart_router":
        SolanaOnlineSmartRouterSupervisor().RUN_ONLINE_SMART_ROUTER()
    elif supervisor == "cex_orderbooks":
        RUN_CEX_ORDERBOOKS()
    elif supervisor == "cex_market_data":
        RUN_CEX_MARKET_DATA()
    elif supervisor == "cex_contracts":
        RUN_CEX_CONTRACTS()
    else:
        print(f"Unknown supervisor: {supervisor}")
        sys.exit(1)


if __name__ == "__main__":
    main()