"""
SoulScan Supervisor Entry Points for systemd
Usage: python -m scripts.run_supervisor <supervisor_name>
"""
import sys
import multiprocessing
from src.SoulSupervisors import RUN_METADATA_FETCHERS, RUN_STATE_FETCHERS, OSRSupervisor
from src.SoulSupervisors.EngineSupervisor import ScannerSupervisor

multiprocessing.set_start_method('spawn', force=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.run_supervisor <supervisor_name>")
        print("Available supervisors:")
        print("  metadata_fetcher  - Fetches pool metadata from DEX APIs")
        print("  state_fetcher     - Fetches live pool state via RPC")
        print("  smart_router      - Computes optimal swap routes")
        print("  scanner           - Scans for CEX/DEX arbitrage opportunities")
        sys.exit(1)

    supervisor = sys.argv[1].lower()

    if supervisor == "metadata_fetcher":
        RUN_METADATA_FETCHERS()
    elif supervisor == "state_fetcher":
        RUN_STATE_FETCHERS()
    elif supervisor == "smart_router":
        OSRSupervisor().RUN_ONLINE_SMART_ROUTER()
    elif supervisor == "scanner":
        ScannerSupervisor().RUN_ONLINE_SCANNER()
    else:
        print(f"Unknown supervisor: {supervisor}")
        sys.exit(1)


if __name__ == "__main__":
    main()
