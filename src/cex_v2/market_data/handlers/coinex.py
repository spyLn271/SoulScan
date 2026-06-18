#!/usr/bin/env python3
"""CoinEx market-data handlers (cex_v2), v2 REST. Neither the spot nor the futures ticker carries a
best bid/ask, so both are LAST-PRICED (best_bid/best_ask=None — the live book is the OB WS stream).

SPOT    : /spot/market (filter: status online, quote USDT/USDC) + /spot/ticker (last + `value`=quote vol).
FUTURES : /futures/market (filter: contract_type linear, quote USDT/USDC, available) + /futures/ticker
          (last/index_price/mark_price/open_interest_volume + `value`=quote vol) + /futures/funding-rate
          (latest_funding_rate, next_funding_time). LINEAR only — inverse + USD contracts excluded.

Symbols are ALREADY canonical (BASE+QUOTE concatenated, e.g. BTCUSDT); futures USDC perps are <BASE>USDC
(distinct from USDT, no collision)."""
from typing import Any, Dict, List

from src.cex_v2.market_data.base import BaseMarketDataHandler
from src.cex_v2.config import get_market_data_config, get_market_data_key, ACCEPTABLE_QUOTE_ASSETS

API = "https://api.coinex.com/v2"


def _fnum(v) -> float:
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def _inum(v):
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def _pos(v) -> bool:
    try:
        return v is not None and float(v) > 0
    except (ValueError, TypeError):
        return False


class CoinexSpotMarketData(BaseMarketDataHandler):
    MARKETS = f"{API}/spot/market"
    TICKER = f"{API}/spot/ticker"

    def __init__(self):
        cfg = get_market_data_config("coinex", "spot") or {}
        super().__init__("coinex", "spot", api_endpoint=self.TICKER,
                         redis_key=get_market_data_key("coinex", "spot"),
                         update_interval=cfg.get("update_interval", 3))

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        res = self._get_many([self.MARKETS, self.TICKER])
        return self._merge(res[self.MARKETS].get("data") or [], res[self.TICKER].get("data") or [])

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:   # single-endpoint fallback (ABC/tests)
        markets = self._get(self.MARKETS).get("data") or []
        return self._merge(markets, resp.get("data") or [])

    def _merge(self, markets, tickers) -> List[Dict[str, Any]]:
        ok = {m["market"] for m in markets
              if m.get("status") == "online" and m.get("quote_ccy") in ACCEPTABLE_QUOTE_ASSETS
              and not m.get("delisted_at")}
        out = []
        for t in tickers:
            mk = t.get("market")
            if mk not in ok or not _pos(t.get("last")):
                continue
            out.append({"symbol": mk, "data": {
                "best_bid": None, "best_ask": None,   # CoinEx ticker has no BBO -> last-priced (book is in WS)
                "lastPrice": str(t.get("last")),
                "24h_volume_usdt": _fnum(t.get("value")),   # `value` = quote-ccy 24h turnover
            }})
        return out


class CoinexFuturesMarketData(BaseMarketDataHandler):
    MARKETS = f"{API}/futures/market"
    TICKER = f"{API}/futures/ticker"
    FUNDING = f"{API}/futures/funding-rate"

    def __init__(self):
        cfg = get_market_data_config("coinex", "futures") or {}
        super().__init__("coinex", "futures", api_endpoint=self.TICKER,
                         redis_key=get_market_data_key("coinex", "futures"),
                         update_interval=cfg.get("update_interval", 3))

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        res = self._get_many([self.MARKETS, self.TICKER, self.FUNDING])
        return self._merge(res[self.MARKETS].get("data") or [], res[self.TICKER].get("data") or [],
                           res[self.FUNDING].get("data") or [])

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:   # single-endpoint fallback (ABC/tests)
        res = self._get_many([self.MARKETS, self.FUNDING])
        return self._merge(res[self.MARKETS].get("data") or [], resp.get("data") or [],
                           res[self.FUNDING].get("data") or [])

    def _merge(self, markets, tickers, funding) -> List[Dict[str, Any]]:
        ok = {m["market"] for m in markets
              if m.get("contract_type") == "linear" and m.get("quote_ccy") in ACCEPTABLE_QUOTE_ASSETS
              and m.get("status") == "online" and not m.get("delisted_at")}
        fund = {f.get("market"): f for f in (funding or [])}
        out = []
        for t in tickers:
            mk = t.get("market")
            if mk not in ok or not _pos(t.get("last")):
                continue
            f = fund.get(mk, {})
            nft = _inum(f.get("next_funding_time"))
            out.append({"symbol": mk, "data": {
                "best_bid": None, "best_ask": None,   # no BBO -> last-priced (book is in WS)
                "lastPrice": str(t.get("last")),
                "indexPrice": str(t.get("index_price")) if t.get("index_price") is not None else None,
                "markPrice": str(t.get("mark_price")) if t.get("mark_price") is not None else None,
                "24h_volume_usdt": _fnum(t.get("value")),
                "open_interest": t.get("open_interest_volume"),
                "funding_rate_percent": _fnum(f.get("latest_funding_rate")) * 100,
                "next_funding_time": nft // 1000 if nft else None,   # ms -> s
            }})
        return out
