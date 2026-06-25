#!/usr/bin/env python3
"""LBank market-data handler (cex_v2) — SPOT. LAST-PRICED (the ticker carries NO best bid/ask; the live
book is the OB WS stream, same as coinex/bitmart-futures).

SPOT: /v2/ticker.do?symbol=all -> {"data":[{"symbol":"btc_usdt","ticker":{high,low,vol,change,turnover,
latest}}]}. No BBO field exists (verified — buy/sell are absent; only a per-symbol depth.do has it), so
best_bid/best_ask=None; `latest` = last, `turnover` = quote-ccy 24h turnover. Filter quote USDT/USDC + a
valid last; symbol btc_usdt -> canonical BTCUSDT. (Futures skipped — see config.py.)
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


class LbankSpotMarketData(BaseMarketDataHandler):
    TICKER = "https://api.lbkex.com/v2/ticker.do?symbol=all"

    def __init__(self):
        cfg = get_market_data_config("lbank", "spot") or {}
        super().__init__("lbank", "spot", api_endpoint=self.TICKER,
                         redis_key=get_market_data_key("lbank", "spot"),
                         update_interval=cfg.get("update_interval", 3))

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:
        out = []
        for item in (resp.get("data") or []):
            sym = item.get("symbol")
            t = item.get("ticker") or {}
            if not sym or "_" not in sym:
                continue
            if sym.rsplit("_", 1)[-1].upper() not in ACCEPTABLE_QUOTE_ASSETS:
                continue
            if not _pos(t.get("latest")):   # drop dead pairs with no valid last price
                continue
            out.append({"symbol": sym.replace("_", "").upper(), "data": {
                "best_bid": None, "best_ask": None,   # no BBO in the ticker -> last-priced (book is in WS)
                "lastPrice": _s(t.get("latest")),
                "24h_volume_usdt": _fnum(t.get("turnover")),   # quote-ccy 24h turnover
            }})
        return out
