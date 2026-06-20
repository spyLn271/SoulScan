#!/usr/bin/env python3
"""Bybit market-data handlers (cex_v2). Bybit v5 /market/tickers returns bid1Price/ask1Price/lastPrice
+ turnover24h (quote-currency volume), and for linear ALSO indexPrice/markPrice/fundingRate/
nextFundingTime — all in ONE response per category. So both spot and futures are single-endpoint
(no multi-endpoint merge like binance futures). Same hygiene as binance: USDT/USDC only, prices kept
as full-precision strings, drop malformed + zero-priced (delisted/halted)."""
from typing import Any, Dict, List

from src.cex.market_data.base import BaseMarketDataHandler
from src.cex.config import get_market_data_config, get_market_data_key, ACCEPTABLE_QUOTE_ASSETS


def _ticker_list(resp, logger) -> List[Dict[str, Any]]:
    """Validate the bybit v5 envelope -> result.list; [] on a bad shape (preserves the existing hash)."""
    if not isinstance(resp, dict) or resp.get("retCode") != 0:
        rc = resp.get("retCode") if isinstance(resp, dict) else "n/a"
        logger.error("bybit: bad response envelope (retCode=%s)", rc)
        return []
    res = resp.get("result")
    lst = res.get("list") if isinstance(res, dict) else None
    return lst if isinstance(lst, list) else []


def _quote_ok(sym) -> bool:
    return bool(sym) and any(sym.endswith(q) for q in ACCEPTABLE_QUOTE_ASSETS)


def _quote_ok_linear(sym) -> bool:
    # USDT linear perps end in USDT; bybit's USDC-settled perps are named <BASE>PERP (e.g. BTCPERP),
    # NOT <BASE>USDC — accept both so the ~$100M/day USDC-perp market isn't silently dropped.
    return _quote_ok(sym) or (bool(sym) and sym.endswith("PERP"))


def _prices_ok(bid, ask, last) -> bool:
    if not bid or not ask or not last:
        return False  # drop malformed — never store "None"
    try:
        return float(bid) > 0 and float(ask) > 0  # drop delisted/halted (0-priced)
    except (ValueError, TypeError):
        return False


def _vol(t) -> float:
    try:
        return float(t.get("turnover24h") or 0)  # turnover24h = quote (USDT/USDC) 24h volume
    except (ValueError, TypeError):
        return 0.0


def _dump_scale(*prices) -> int:
    """Per-symbol price precision = max significant decimals across bid/ask/last. This is the dumpScale
    the SPOT order-book uses to subscribe to bybit's mergedDepth feed (the website's grouped view)."""
    m = 0
    for p in prices:
        s = str(p) if p is not None else ""
        if "." in s:
            m = max(m, len(s.split(".")[-1].rstrip("0")))
    return m


class BybitSpotMarketData(BaseMarketDataHandler):
    def __init__(self):
        cfg = get_market_data_config("bybit", "spot") or {}
        super().__init__("bybit", "spot",
                         api_endpoint=cfg["api_endpoint"],
                         redis_key=get_market_data_key("bybit", "spot"),
                         update_interval=cfg.get("update_interval", 3))

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:
        out = []
        for t in _ticker_list(resp, self.logger):
            sym = t.get("symbol")
            if not _quote_ok(sym):
                continue
            bid, ask, last = t.get("bid1Price"), t.get("ask1Price"), t.get("lastPrice")
            if not _prices_ok(bid, ask, last):
                continue
            out.append({"symbol": sym, "data": {
                "24h_volume_usdt": _vol(t),
                "best_bid": bid, "best_ask": ask, "lastPrice": last,  # full-precision strings
                "dumpScale": _dump_scale(bid, ask, last),  # for the ws2 mergedDepth order-book subscribe
            }})
        return out


class BybitFuturesMarketData(BaseMarketDataHandler):
    """USDT-perp (linear): one tickers endpoint already carries bid/ask/last + index/mark/funding."""

    def __init__(self):
        cfg = get_market_data_config("bybit", "futures") or {}
        super().__init__("bybit", "futures",
                         api_endpoint=cfg["api_endpoint"],
                         redis_key=get_market_data_key("bybit", "futures"),
                         update_interval=cfg.get("update_interval", 3))

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:
        out = []
        for t in _ticker_list(resp, self.logger):
            sym = t.get("symbol")
            if not _quote_ok_linear(sym):
                continue
            if t.get("deliveryTime") not in ("0", 0, None):
                continue  # perpetuals only (dated/delivery futures carry a nonzero deliveryTime)
            bid, ask, last = t.get("bid1Price"), t.get("ask1Price"), t.get("lastPrice")
            if not _prices_ok(bid, ask, last):
                continue
            try:
                funding = float(t.get("fundingRate") or 0) * 100
            except (ValueError, TypeError):
                funding = 0.0
            try:
                nft = int(t.get("nextFundingTime") or 0)   # bybit sends a STRING; normalize numerically
            except (ValueError, TypeError):
                nft = 0
            out.append({"symbol": sym, "data": {
                "24h_volume_usdt": _vol(t),
                "best_bid": bid, "best_ask": ask, "lastPrice": last,  # full-precision strings
                "indexPrice": t.get("indexPrice"), "markPrice": t.get("markPrice"),
                "funding_rate_percent": funding,
                "next_funding_time": nft // 1000 if nft > 0 else None,  # ms -> s
            }})
        return out
