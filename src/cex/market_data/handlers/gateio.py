#!/usr/bin/env python3
"""Gate.io market-data handlers (cex_v2). Both carry a real best bid/ask AND the per-symbol native price
`tick` the OB plugin needs as the wsbridge merge param (a fixed merge collapses cheap coins). Two
endpoints each, fetched concurrently:

SPOT    : /spot/tickers (BBO/last/volume) + /spot/currency_pairs (price `precision` -> tick = 10^-precision).
FUTURES : /futures/usdt/tickers (BBO/mark/index/funding/volume/quanto_multiplier) +
          /futures/usdt/contracts (`order_price_round` = tick). quanto_multiplier is PUBLISHED so the OB can
          convert contract-denominated depth to base-asset (okx ctVal pattern).
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


def _tick_from_precision(p):
    try:
        p = int(p)
    except (ValueError, TypeError):
        return None
    if p <= 0:
        return "1"
    return "0." + "0" * (p - 1) + "1"


class GateioSpotMarketData(BaseMarketDataHandler):
    TICKER = "https://api.gateio.ws/api/v4/spot/tickers"
    PAIRS = "https://api.gateio.ws/api/v4/spot/currency_pairs"

    def __init__(self):
        cfg = get_market_data_config("gateio", "spot") or {}
        super().__init__("gateio", "spot", api_endpoint=self.TICKER,
                         redis_key=get_market_data_key("gateio", "spot"),
                         update_interval=cfg.get("update_interval", 3))

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        d = self._get_many([self.TICKER, self.PAIRS])
        return self.parse_api_response(d.get(self.TICKER), d.get(self.PAIRS))

    def parse_api_response(self, tickers, pairs=None) -> List[Dict[str, Any]]:
        by_id = {p.get("id"): p for p in (pairs or [])}
        out = []
        for t in (tickers or []):
            cp = t.get("currency_pair")
            if not cp or "_" not in cp:
                continue
            if cp.rsplit("_", 1)[-1].upper() not in ACCEPTABLE_QUOTE_ASSETS:
                continue
            if not (_pos(t.get("highest_bid")) and _pos(t.get("lowest_ask"))):
                continue
            info = by_id.get(cp)
            tick = _tick_from_precision(info.get("precision")) if info else None
            if not tick:                       # need the native tick (wsbridge merge); else OB can't subscribe
                continue
            out.append({"symbol": cp.replace("_", "").upper(), "data": {
                "best_bid": _s(t.get("highest_bid")), "best_ask": _s(t.get("lowest_ask")),
                "lastPrice": _s(t.get("last")),
                "24h_volume_usdt": _fnum(t.get("quote_volume")),
                "tick": tick,
            }})
        return out


class GateioFuturesMarketData(BaseMarketDataHandler):
    TICKER = "https://fx-api.gateio.ws/api/v4/futures/usdt/tickers"
    CONTRACTS = "https://fx-api.gateio.ws/api/v4/futures/usdt/contracts"

    def __init__(self):
        cfg = get_market_data_config("gateio", "futures") or {}
        super().__init__("gateio", "futures", api_endpoint=self.TICKER,
                         redis_key=get_market_data_key("gateio", "futures"),
                         update_interval=cfg.get("update_interval", 3))

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        d = self._get_many([self.TICKER, self.CONTRACTS])
        return self.parse_api_response(d.get(self.TICKER), d.get(self.CONTRACTS))

    def parse_api_response(self, tickers, contracts=None) -> List[Dict[str, Any]]:
        by_name = {c.get("name"): c for c in (contracts or [])}
        out = []
        for t in (tickers or []):
            c = t.get("contract")
            if not c or not c.endswith("_USDT"):   # /futures/usdt/ settles USDT-margined perps only
                continue
            if not (_pos(t.get("highest_bid")) and _pos(t.get("lowest_ask"))):
                continue
            info = by_name.get(c, {})
            tick = info.get("order_price_round")
            quanto = t.get("quanto_multiplier") or info.get("quanto_multiplier")
            if not tick or not _pos(quanto):       # need both tick (merge) and quanto (contracts->base)
                continue
            out.append({"symbol": c.replace("_", "").upper(), "data": {
                "best_bid": _s(t.get("highest_bid")), "best_ask": _s(t.get("lowest_ask")),
                "lastPrice": _s(t.get("last")),
                "markPrice": _s(t.get("mark_price")),
                "indexPrice": _s(t.get("index_price")),
                "24h_volume_usdt": _fnum(t.get("volume_24h_quote")),
                "tick": _s(tick),
                "quanto_multiplier": _s(quanto),
                "funding_rate_percent": _fnum(t.get("funding_rate")) * 100,
            }})
        return out
