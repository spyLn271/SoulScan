#!/usr/bin/env python3
"""Binance market-data handlers (cex_v2). Fixes vs legacy: include USDC pairs (not USDT-only),
keep prices as full-precision strings, drop malformed records instead of writing the literal "None".
Spot = single 24hr-ticker endpoint; futures = merge 24hr ticker + bookTicker + premiumIndex."""
from typing import Any, Dict, List

from src.cex.market_data.base import BaseMarketDataHandler
from src.cex.config import get_market_data_config, get_market_data_key, ACCEPTABLE_QUOTE_ASSETS


class BinanceSpotMarketData(BaseMarketDataHandler):
    def __init__(self):
        cfg = get_market_data_config("binance", "spot") or {}
        super().__init__("binance", "spot",
                         api_endpoint=cfg["api_endpoint"],
                         redis_key=get_market_data_key("binance", "spot"),
                         update_interval=cfg.get("update_interval", 3))

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:
        if not isinstance(resp, list):
            self.logger.error("binance: expected list response")
            return []
        out = []
        for t in resp:
            sym = t.get("symbol")
            if not sym or not any(sym.endswith(q) for q in ACCEPTABLE_QUOTE_ASSETS):
                continue  # USDT + USDC (legacy dropped USDC)
            bid, ask, last = t.get("bidPrice"), t.get("askPrice"), t.get("lastPrice")
            if not bid or not ask or not last:
                continue  # drop malformed — never store "None"
            try:
                if float(bid) <= 0 or float(ask) <= 0:
                    continue  # delisted/halted (0.00000000) — keep the universe to live pairs only
            except (ValueError, TypeError):
                continue
            try:
                vol = float(t.get("quoteVolume") or 0)
            except (ValueError, TypeError):
                vol = 0.0
            out.append({"symbol": sym, "data": {
                "24h_volume_usdt": vol,
                "best_bid": bid, "best_ask": ask, "lastPrice": last,  # full-precision strings
            }})
        return out


class BinanceFuturesMarketData(BaseMarketDataHandler):
    """USDT-M futures: merge 24hr ticker (volume/lastPrice) + bookTicker (bid/ask) +
    premiumIndex (mark/index/funding/nextFundingTime) by symbol."""

    def __init__(self):
        cfg = get_market_data_config("binance", "futures") or {}
        eps = cfg.get("endpoints", {})
        super().__init__("binance", "futures",
                         api_endpoint=eps.get("ticker", ""),
                         redis_key=get_market_data_key("binance", "futures"),
                         update_interval=cfg.get("update_interval", 3))
        self._ep_ticker = eps["ticker"]
        self._ep_book = eps["book"]
        self._ep_premium = eps["premium"]

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:  # unused; futures overrides fetch_parsed
        return []

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        resp = self._get_many([self._ep_ticker, self._ep_book, self._ep_premium])  # 3 endpoints concurrently
        ticker, book, premium = resp[self._ep_ticker], resp[self._ep_book], resp[self._ep_premium]
        if not (isinstance(ticker, list) and isinstance(book, list) and isinstance(premium, list)):
            self.logger.error("binance futures: non-list response")
            return []
        bmap = {b["symbol"]: b for b in book if "symbol" in b}
        pmap = {p["symbol"]: p for p in premium if "symbol" in p}
        out = []
        for t in ticker:
            sym = t.get("symbol")
            if not sym or not any(sym.endswith(q) for q in ACCEPTABLE_QUOTE_ASSETS):
                continue
            b, p = bmap.get(sym), pmap.get(sym)
            if not b or not p:
                continue  # need complete data across all three endpoints
            bid, ask, last = b.get("bidPrice"), b.get("askPrice"), t.get("lastPrice")
            if not bid or not ask or not last:
                continue
            try:
                if float(bid) <= 0 or float(ask) <= 0:
                    continue  # delisted/halted — keep the universe to live pairs only
            except (ValueError, TypeError):
                continue
            try:
                vol = float(t.get("quoteVolume") or 0)
            except (ValueError, TypeError):
                vol = 0.0
            try:
                funding = float(p.get("lastFundingRate") or 0) * 100
            except (ValueError, TypeError):
                funding = 0.0
            nft = p.get("nextFundingTime") or 0
            out.append({"symbol": sym, "data": {
                "24h_volume_usdt": vol,
                "best_bid": bid, "best_ask": ask, "lastPrice": last,   # full-precision strings
                "indexPrice": p.get("indexPrice"), "markPrice": p.get("markPrice"),
                "funding_rate_percent": funding,
                "next_funding_time": int(nft) // 1000 if nft else None,
            }})
        return out
