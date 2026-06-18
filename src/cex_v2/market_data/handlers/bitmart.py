#!/usr/bin/env python3
"""BitMart market-data handlers (cex_v2). SPOT merges /spot/v1/symbols/details (trade_status, quote)
with /spot/quotation/v3/tickers (POSITIONAL arrays: [symbol,last,v24,qv24,open,high,low,fluct,bidPx,
bidSz,askPx,askSz,ts]). FUTURES uses the v2 contract /details endpoint alone — it carries last/index/
funding/OI/contract_size for every perp but NO bid/ask, so futures md is last-priced (the order book
itself comes through the WS). All product_type=1 perps; exclude USD inverse. USDT/USDC only; symbols
-> canonical (BTC_USDT -> BTCUSDT; futures BTCUSDT already canonical)."""
from typing import Any, Dict, List

from src.cex_v2.market_data.base import BaseMarketDataHandler
from src.cex_v2.config import get_market_data_config, get_market_data_key, ACCEPTABLE_QUOTE_ASSETS

SPOT_API = "https://api-cloud.bitmart.com"
FUT_API = "https://api-cloud-v2.bitmart.com"


def _canon(sym) -> str:
    return (sym or "").upper().replace("_", "")


def _pos(v) -> bool:
    try:
        return v is not None and float(v) > 0
    except (ValueError, TypeError):
        return False


def _fnum(v) -> float:
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def _inum(v):
    """-> int or None. A single non-numeric funding_time must not raise out of parse_api_response and
    drop the ENTIRE futures md batch (the base handler builds the whole list in one call)."""
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


class BitmartSpotMarketData(BaseMarketDataHandler):
    SYMBOLS = f"{SPOT_API}/spot/v1/symbols/details"
    TICKERS = f"{SPOT_API}/spot/quotation/v3/tickers"

    def __init__(self):
        cfg = get_market_data_config("bitmart", "spot") or {}
        super().__init__("bitmart", "spot", api_endpoint=self.TICKERS,
                         redis_key=get_market_data_key("bitmart", "spot"),
                         update_interval=cfg.get("update_interval", 3))

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        res = self._get_many([self.SYMBOLS, self.TICKERS])
        syms = (res[self.SYMBOLS].get("data") or {}).get("symbols", [])
        return self._merge(syms, res[self.TICKERS].get("data") or [])

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:   # single-endpoint fallback (tests/ABC)
        syms = (self._get(self.SYMBOLS).get("data") or {}).get("symbols", [])
        return self._merge(syms, resp.get("data") or [])

    def _merge(self, symbols, tickers) -> List[Dict[str, Any]]:
        meta = {s["symbol"] for s in symbols
                if s.get("trade_status") == "trading" and s.get("quote_currency") in ACCEPTABLE_QUOTE_ASSETS}
        out = []
        for t in tickers:                       # positional array per ticker
            if not isinstance(t, list) or len(t) < 11 or t[0] not in meta:
                continue
            last, bid, ask = t[1], t[8], t[10]
            if not (_pos(bid) and _pos(ask) and _pos(last)):
                continue
            out.append({"symbol": _canon(t[0]), "data": {
                "best_bid": str(bid), "best_ask": str(ask), "lastPrice": str(last),
                "24h_volume_usdt": _fnum(t[3]),   # quote-ccy 24h volume
            }})
        return out


class BitmartFuturesMarketData(BaseMarketDataHandler):
    DETAILS = f"{FUT_API}/contract/public/details"

    def __init__(self):
        cfg = get_market_data_config("bitmart", "futures") or {}
        super().__init__("bitmart", "futures", api_endpoint=self.DETAILS,
                         redis_key=get_market_data_key("bitmart", "futures"),
                         update_interval=cfg.get("update_interval", 3))

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:
        d = resp.get("data")
        contracts = d.get("symbols") if isinstance(d, dict) else d
        out = []
        for c in (contracts or []):
            if c.get("status") != "Trading" or c.get("quote_currency") not in ACCEPTABLE_QUOTE_ASSETS:
                continue
            last = c.get("last_price")
            if not _pos(last):
                continue
            ft = _inum(c.get("funding_time"))
            out.append({"symbol": _canon(c["symbol"]), "data": {
                # contract details has no bid/ask -> last-priced (the live book is in the WS stream)
                "best_bid": None, "best_ask": None, "lastPrice": str(last),
                "indexPrice": str(c.get("index_price")) if c.get("index_price") is not None else None,
                "24h_volume_usdt": _fnum(c.get("turnover_24h")),
                "funding_rate_percent": _fnum(c.get("funding_rate")) * 100,
                "next_funding_time": ft // 1000 if ft else None,   # ms -> s
                "open_interest": c.get("open_interest"),
                "contract_size": c.get("contract_size"),   # for contract->base conversion
            }})
        return out
