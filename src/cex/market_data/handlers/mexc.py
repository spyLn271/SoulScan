#!/usr/bin/env python3
"""MEXC market-data handler (cex_v2) — SPOT, on the v3 REST API. Merges /exchangeInfo (quoteAsset,
status, isSpotTradingAllowed) with /ticker/24hr (bid/ask/last + quoteVolume). USDT/USDC only,
full-precision STRING prices, drop malformed/zero/non-trading. Plain symbols (BTCUSDT) — no remap.

MEXC FUTURES is a separate API (contract.mexc.com) and is not wired yet."""
from typing import Any, Dict, List

from src.cex.market_data.base import BaseMarketDataHandler
from src.cex.config import get_market_data_config, get_market_data_key, ACCEPTABLE_QUOTE_ASSETS

API = "https://api.mexc.com"


def _prices_ok(bid, ask, last) -> bool:
    if not bid or not ask or not last:
        return False
    try:
        return float(bid) > 0 and float(ask) > 0 and float(last) > 0
    except (ValueError, TypeError):
        return False


def _fnum(v) -> float:
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


class MexcSpotMarketData(BaseMarketDataHandler):
    EXCHANGE_INFO = f"{API}/api/v3/exchangeInfo"
    TICKERS = f"{API}/api/v3/ticker/24hr"

    def __init__(self):
        cfg = get_market_data_config("mexc", "spot") or {}
        super().__init__("mexc", "spot",
                         api_endpoint=self.TICKERS,
                         redis_key=get_market_data_key("mexc", "spot"),
                         update_interval=cfg.get("update_interval", 3))

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        res = self._get_many([self.EXCHANGE_INFO, self.TICKERS])
        return self._merge(res[self.EXCHANGE_INFO].get("symbols", []), res[self.TICKERS])

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:   # single-endpoint fallback (tests/ABC)
        return self._merge(self._get(self.EXCHANGE_INFO).get("symbols", []), resp)

    def _merge(self, symbols, tickers) -> List[Dict[str, Any]]:
        meta = {s["symbol"]: s for s in symbols
                if s.get("status") == "1" and s.get("isSpotTradingAllowed")
                and s.get("quoteAsset") in ACCEPTABLE_QUOTE_ASSETS}
        out = []
        for t in (tickers or []):
            if t.get("symbol") not in meta:
                continue
            bid, ask, last = t.get("bidPrice"), t.get("askPrice"), t.get("lastPrice")
            if not _prices_ok(bid, ask, last):
                continue
            out.append({"symbol": t["symbol"], "data": {
                "best_bid": bid, "best_ask": ask, "lastPrice": last,   # full-precision strings
                "24h_volume_usdt": _fnum(t.get("quoteVolume")),        # quote (USDT/USDC) 24h volume
            }})
        return out
