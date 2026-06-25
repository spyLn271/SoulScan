#!/usr/bin/env python3
"""Bitget market-data handlers (cex_v2), on the v2 REST API. Multi-endpoint merge: the instrument
list (symbol, quoteCoin, status — and for futures the product line + perpetual flag) merged with
/market/tickers (bidPr/askPr/lastPr + usdtVolume, and for futures fundingRate/markPrice/indexPrice/OI).

Hygiene matches the other venues: USDT/USDC only, full-precision STRING prices, drop malformed/zero/
non-live. The hash is keyed by the plain symbol (BTCUSDT spot; BTCUSDT USDT-perp; <BASE>PERP USDC-perp
— all distinct, no remap). FUTURES also stores `instType` (USDT-FUTURES / USDC-FUTURES) so the
order-book plugin knows which product line to subscribe each symbol under.

Bitget terms: SPOT = spot; USDT-FUTURES + USDC-FUTURES = linear perps (our "futures"); COIN-FUTURES =
inverse (quoteCoin USD) -> excluded, matching the USDT/USDC-only policy."""
from typing import Any, Dict, List

from src.cex.market_data.base import BaseMarketDataHandler
from src.cex.config import get_market_data_config, get_market_data_key, ACCEPTABLE_QUOTE_ASSETS

API = "https://api.bitget.com"


def _prices_ok(bid, ask, last) -> bool:
    if not bid or not ask or not last:
        return False
    try:
        return float(bid) > 0 and float(ask) > 0 and float(last) > 0   # a live pair has a positive last
    except (ValueError, TypeError):
        return False


def _fnum(v) -> float:
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


class BitgetSpotMarketData(BaseMarketDataHandler):
    """SPOT: merge public/symbols (quoteCoin/status) with market/tickers (bid/ask/last + usdtVolume)."""

    SYMBOLS = f"{API}/api/v2/spot/public/symbols"
    TICKERS = f"{API}/api/v2/spot/market/tickers"

    def __init__(self):
        cfg = get_market_data_config("bitget", "spot") or {}
        super().__init__("bitget", "spot",
                         api_endpoint=self.TICKERS,
                         redis_key=get_market_data_key("bitget", "spot"),
                         update_interval=cfg.get("update_interval", 3))

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        res = self._get_many([self.SYMBOLS, self.TICKERS])
        return self._merge(res[self.SYMBOLS].get("data", []), res[self.TICKERS].get("data", []))

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:   # single-endpoint fallback (tests/ABC)
        return self._merge(self._get(self.SYMBOLS).get("data", []), resp.get("data", []))

    def _merge(self, symbols, tickers) -> List[Dict[str, Any]]:
        # Drop tokenized stocks/ETFs (areaSymbol=="yes", e.g. rNVDA/rQQQ): Bitget reports a ticker +
        # volume for them but they have NO L2 order book (RFQ-quoted), so they never produce an
        # order-book snapshot and would otherwise inflate the universe by ~497 never-active symbols.
        meta = {s["symbol"]: s for s in symbols
                if s.get("status") == "online" and s.get("quoteCoin") in ACCEPTABLE_QUOTE_ASSETS
                and s.get("areaSymbol") != "yes"}
        out = []
        for t in tickers:
            if t.get("symbol") not in meta:
                continue
            bid, ask, last = t.get("bidPr"), t.get("askPr"), t.get("lastPr")
            if not _prices_ok(bid, ask, last):
                continue
            out.append({"symbol": t["symbol"], "data": {
                "best_bid": bid, "best_ask": ask, "lastPrice": last,   # full-precision strings
                "24h_volume_usdt": _fnum(t.get("usdtVolume")),
            }})
        return out


class BitgetFuturesMarketData(BaseMarketDataHandler):
    """Linear perps: merge contracts + tickers for USDT-FUTURES and USDC-FUTURES product lines."""

    PRODUCTS = ("USDT-FUTURES", "USDC-FUTURES")
    CONTRACTS = f"{API}/api/v2/mix/market/contracts?productType="
    TICKERS = f"{API}/api/v2/mix/market/tickers?productType="

    def __init__(self):
        cfg = get_market_data_config("bitget", "futures") or {}
        super().__init__("bitget", "futures",
                         api_endpoint=self.TICKERS + "USDT-FUTURES",
                         redis_key=get_market_data_key("bitget", "futures"),
                         update_interval=cfg.get("update_interval", 3))

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        urls = [self.CONTRACTS + p for p in self.PRODUCTS] + [self.TICKERS + p for p in self.PRODUCTS]
        res = self._get_many(urls)
        contracts = {}   # symbol -> (product, contract)  (symbols are unique across products)
        tickers = {}
        for p in self.PRODUCTS:
            for c in res[self.CONTRACTS + p].get("data", []):
                contracts[c["symbol"]] = (p, c)
            for t in res[self.TICKERS + p].get("data", []):
                tickers[t["symbol"]] = t
        return self._merge(contracts, tickers)

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:   # ABC requirement; OB uses fetch_parsed
        return self.fetch_parsed()

    def _merge(self, contracts, tickers) -> List[Dict[str, Any]]:
        out = []
        for sym, (product, c) in contracts.items():
            if c.get("symbolStatus") != "normal" or c.get("symbolType") != "perpetual":
                continue
            if c.get("quoteCoin") not in ACCEPTABLE_QUOTE_ASSETS:   # exclude inverse (COIN-FUTURES = USD)
                continue
            t = tickers.get(sym)
            if not t:
                continue
            bid, ask, last = t.get("bidPr"), t.get("askPr"), t.get("lastPr")
            if not _prices_ok(bid, ask, last):
                continue
            out.append({"symbol": sym, "data": {
                "instType": product,                                  # for the OB subscribe (product line)
                "best_bid": bid, "best_ask": ask, "lastPrice": last,
                "24h_volume_usdt": _fnum(t.get("usdtVolume")),
                "markPrice": t.get("markPrice"), "indexPrice": t.get("indexPrice"),
                "funding_rate_percent": _fnum(t.get("fundingRate")) * 100,
                "open_interest": t.get("holdingAmount"),
            }})
        return out
