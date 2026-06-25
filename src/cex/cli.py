"""
  python -m src.cex orderbook  --market spot              # all spot order-book exchanges
  python -m src.cex orderbook  --market futures --exchanges binance
  python -m src.cex orderbook  --market both   --exchanges binance,bybit
  python -m src.cex marketdata --market futures --exchanges all
"""
import argparse
from typing import List, Optional, Tuple


def parse_markets(s: str) -> Tuple[str, ...]:
    s = s.strip().lower()

    if s == "both":
        return ("spot", "futures")

    if s in ("spot", "futures"):
        return (s,)

    raise argparse.ArgumentTypeError("--market must be spot | futures | both")


def parse_exchanges(s: str) -> Optional[List[str]]:
    s = s.strip().lower()

    if s in ("all", "", "*"):
        return None

    return [x.strip().lower() for x in s.split(",") if x.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m src.cex", description="cex_v2 order-book / market-data runner")
    ap.add_argument("component", choices=["orderbook", "marketdata"], help="which subsystem to run")
    ap.add_argument("--market", default="spot", help="spot | futures | both (default: spot)")
    ap.add_argument("--exchanges", default="all", help="comma-separated names or 'all' (default: all)")
    a = ap.parse_args(argv)

    markets = parse_markets(a.market)
    exchanges = parse_exchanges(a.exchanges)

    if a.component == "orderbook":
        from src.cex.supervisor import RUN
        RUN(markets=markets, exchanges=exchanges)
    else:
        from src.cex.market_data.manager import RUN
        RUN(markets=markets, exchanges=exchanges)


if __name__ == "__main__":
    main()
