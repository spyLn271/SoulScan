#!/usr/bin/env python3
"""BingX market-data handlers (cex_v2), documented REST. Spot merges common/symbols (status, dash
symbol) + ticker/24hr (bid/ask/last + quoteVolume). Futures merges swap contracts (status, currency)
+ ticker + premiumIndex (markPrice/indexPrice/funding). USDT/USDC only; dash symbols -> canonical
(BTC-USDT -> BTCUSDT). BingX returns prices as JSON NUMBERS, so we stringify them (md is full-precision
strings by convention; the order book itself comes through the WS as strings)."""
from typing import Any, Dict, List

from src.cex.market_data.base import BaseMarketDataHandler
from src.cex.config import get_market_data_config, get_market_data_key, ACCEPTABLE_QUOTE_ASSETS

API = "https://open-api.bingx.com"


def _canon(sym) -> str:
    return (sym or "").upper().replace("-", "")


def _quote(sym) -> str:
    return (sym or "").rsplit("-", 1)[-1].upper()


def _s(v):
    return None if v is None else str(v)


def _prices_ok(bid, ask, last) -> bool:
    try:
        return bid is not None and ask is not None and last is not None \
            and float(bid) > 0 and float(ask) > 0 and float(last) > 0
    except (ValueError, TypeError):
        return False


def _fnum(v) -> float:
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


class BingxSpotMarketData(BaseMarketDataHandler):
    SYMBOLS = f"{API}/openApi/spot/v1/common/symbols"
    TICKERS = f"{API}/openApi/spot/v1/ticker/24hr"

    def __init__(self):
        cfg = get_market_data_config("bingx", "spot") or {}
        super().__init__("bingx", "spot", api_endpoint=self.TICKERS,
                         redis_key=get_market_data_key("bingx", "spot"),
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
                if s.get("status") == 1 and _quote(s.get("symbol")) in ACCEPTABLE_QUOTE_ASSETS}
        out = []
        for t in tickers:
            if t.get("symbol") not in meta:
                continue
            bid, ask, last = t.get("bidPrice"), t.get("askPrice"), t.get("lastPrice")
            if not _prices_ok(bid, ask, last):
                continue
            out.append({"symbol": _canon(t["symbol"]), "data": {
                "best_bid": _s(bid), "best_ask": _s(ask), "lastPrice": _s(last),
                "24h_volume_usdt": _fnum(t.get("quoteVolume")),
            }})
        return out


class BingxFuturesMarketData(BaseMarketDataHandler):
    CONTRACTS = f"{API}/openApi/swap/v2/quote/contracts"
    TICKERS = f"{API}/openApi/swap/v2/quote/ticker"
    PREMIUM = f"{API}/openApi/swap/v2/quote/premiumIndex"

    def __init__(self):
        cfg = get_market_data_config("bingx", "futures") or {}
        super().__init__("bingx", "futures", api_endpoint=self.TICKERS,
                         redis_key=get_market_data_key("bingx", "futures"),
                         update_interval=cfg.get("update_interval", 3))

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        res = self._get_many([self.CONTRACTS, self.TICKERS, self.PREMIUM])
        return self._merge(res[self.CONTRACTS].get("data") or [],
                           res[self.TICKERS].get("data") or [], res[self.PREMIUM].get("data") or [])

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:   # single-endpoint fallback (tests/ABC)
        return self._merge(self._get(self.CONTRACTS).get("data") or [],
                           resp.get("data") or [], self._get(self.PREMIUM).get("data") or [])

    def _merge(self, contracts, tickers, premium) -> List[Dict[str, Any]]:
        meta = {c["symbol"] for c in contracts
                if c.get("status") == 1 and c.get("currency") in ACCEPTABLE_QUOTE_ASSETS}
        prem = {p["symbol"]: p for p in (premium or [])}
        out = []
        for t in tickers:
            sym = t.get("symbol")
            if sym not in meta:
                continue
            bid, ask, last = t.get("bidPrice"), t.get("askPrice"), t.get("lastPrice")
            if not _prices_ok(bid, ask, last):
                continue
            p = prem.get(sym, {})
            nft = p.get("nextFundingTime")
            out.append({"symbol": _canon(sym), "data": {
                "best_bid": _s(bid), "best_ask": _s(ask), "lastPrice": _s(last),
                "24h_volume_usdt": _fnum(t.get("quoteVolume")),
                "markPrice": _s(p.get("markPrice")), "indexPrice": _s(p.get("indexPrice")),
                "funding_rate_percent": _fnum(p.get("lastFundingRate")) * 100,
                "next_funding_time": int(nft) // 1000 if nft else None,   # ms -> s
            }})
        return out
