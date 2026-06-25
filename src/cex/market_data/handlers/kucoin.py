#!/usr/bin/env python3
"""KuCoin market-data handlers (cex_v2). Both publish the exchange WIRE symbol so the OB plugin can
subscribe without reverse-mapping (spot BTC-USDT; futures XBTUSDTM where XBT=BTC).

SPOT    : /api/v1/market/allTickers -> data.ticker[] {symbol BTC-USDT, buy, sell, last, volValue}. Real BBO.
FUTURES : /api/v1/contracts/active (multiplier, mark/index/funding, turnover, base/quote, isInverse) MERGED
          with /api/v1/allTickers (bestBidPrice/bestAskPrice). USDT-M perps only (quote USDT/USDC, not
          inverse). multiplier is PUBLISHED so the OB converts contract-denominated depth to base-asset.
"""
from typing import Any, Dict, List

from src.cex.market_data.base import BaseMarketDataHandler
from src.cex.config import get_market_data_config, get_market_data_key, ACCEPTABLE_QUOTE_ASSETS


def _fnum(v) -> float:
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def _pos(v) -> bool:
    try:
        return v is not None and float(v) > 0
    except (ValueError, TypeError):
        return False


def _s(v):
    return str(v) if v is not None else None


class KucoinSpotMarketData(BaseMarketDataHandler):
    TICKER = "https://api.kucoin.com/api/v1/market/allTickers"

    def __init__(self):
        cfg = get_market_data_config("kucoin", "spot") or {}
        super().__init__("kucoin", "spot", api_endpoint=self.TICKER,
                         redis_key=get_market_data_key("kucoin", "spot"),
                         update_interval=cfg.get("update_interval", 3))

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:
        rows = ((resp or {}).get("data") or {}).get("ticker") or []
        out = []
        for t in rows:
            sym = t.get("symbol")            # BTC-USDT
            if not sym or "-" not in sym:
                continue
            if sym.rsplit("-", 1)[-1].upper() not in ACCEPTABLE_QUOTE_ASSETS:
                continue
            if not (_pos(t.get("buy")) and _pos(t.get("sell"))):
                continue
            out.append({"symbol": sym.replace("-", "").upper(), "data": {
                "best_bid": _s(t.get("buy")), "best_ask": _s(t.get("sell")),
                "lastPrice": _s(t.get("last")),
                "24h_volume_usdt": _fnum(t.get("volValue")),   # quote-ccy 24h turnover
                "wire": sym,
            }})
        return out


class KucoinFuturesMarketData(BaseMarketDataHandler):
    CONTRACTS = "https://api-futures.kucoin.com/api/v1/contracts/active"
    TICKERS = "https://api-futures.kucoin.com/api/v1/allTickers"

    def __init__(self):
        cfg = get_market_data_config("kucoin", "futures") or {}
        super().__init__("kucoin", "futures", api_endpoint=self.CONTRACTS,
                         redis_key=get_market_data_key("kucoin", "futures"),
                         update_interval=cfg.get("update_interval", 3))

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        d = self._get_many([self.CONTRACTS, self.TICKERS])
        if not ((d.get(self.TICKERS) or {}).get("data")):
            # /allTickers is the ONLY BBO source; a 200-but-empty response would publish all-null BBO over
            # the full universe (count stays full so never-blank/min_fraction don't trip). Raise to preserve
            # the existing md hash (base.update_once catches + keeps the prior data).
            raise RuntimeError("kucoin futures /allTickers returned no data; preserving existing md")
        return self.parse_api_response(d.get(self.CONTRACTS), d.get(self.TICKERS))

    def parse_api_response(self, contracts_resp, tickers_resp=None) -> List[Dict[str, Any]]:
        contracts = (contracts_resp or {}).get("data") or []
        tickers = (tickers_resp or {}).get("data") or []
        bbo = {t.get("symbol"): t for t in tickers}
        out = []
        for c in contracts:
            sym = c.get("symbol")            # XBTUSDTM
            q = (c.get("quoteCurrency") or "").upper()
            if not sym or q not in ACCEPTABLE_QUOTE_ASSETS or c.get("isInverse") or c.get("status") != "Open":
                continue
            mult = c.get("multiplier")
            if not _pos(mult):
                continue                      # OB needs the multiplier to scale contracts -> base
            base = (c.get("baseCurrency") or "").upper()
            base = "BTC" if base == "XBT" else base
            canon = base + q
            tk = bbo.get(sym, {})
            out.append({"symbol": canon, "data": {
                "best_bid": _s(tk.get("bestBidPrice")), "best_ask": _s(tk.get("bestAskPrice")),
                "lastPrice": _s(tk.get("price") or c.get("markPrice")),
                "markPrice": _s(c.get("markPrice")),
                "indexPrice": _s(c.get("indexPrice")),
                "24h_volume_usdt": _fnum(c.get("turnoverOf24h")),
                "multiplier": _s(mult),       # OB scales contracts -> base by this
                "funding_rate_percent": _fnum(c.get("fundingFeeRate")) * 100,
                "wire": sym,
            }})
        return out
