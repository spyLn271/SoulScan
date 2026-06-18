#!/usr/bin/env python3
"""OKX market-data handlers (cex_v2). Multi-endpoint merge (like binance futures): the instrument
list (instId, baseCcy/quoteCcy or instFamily, state, and for SWAP settleCcy/ctVal) is merged with
/market/tickers (bidPx/askPx/last + 24h volume), plus mark-price for futures.

Hygiene matches the other venues: USDT/USDC only, full-precision STRING prices, drop malformed/zero/
non-live. The hash is keyed by the CANONICAL symbol (BTCUSDT) with the OKX `instId`
(BTC-USDT / BTC-USDT-SWAP) stored as a FIELD — the order-book plugin reads instId to subscribe and
keeps the core in one (canonical) symbol space. Futures also carry markPrice + ctVal/ctValCcy so a
consumer can convert the contract-denominated order-book sizes to base/notional.

OKX terminology: SPOT = spot; SWAP = perpetual (our "futures", LINEAR only -> settleCcy in USDT/USDC,
inverse <BASE>-USD-SWAP excluded); FUTURES = dated (not used); OPTION = options (not used)."""
from typing import Any, Dict, List

from src.cex_v2.market_data.base import BaseMarketDataHandler
from src.cex_v2.config import get_market_data_config, get_market_data_key, ACCEPTABLE_QUOTE_ASSETS

OKX = "https://www.okx.com"


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


class OkxSpotMarketData(BaseMarketDataHandler):
    """SPOT: merge instruments (baseCcy/quoteCcy/state) with tickers (bid/ask/last/quote-volume)."""

    INSTRUMENTS = f"{OKX}/api/v5/public/instruments?instType=SPOT"
    TICKERS = f"{OKX}/api/v5/market/tickers?instType=SPOT"

    def __init__(self):
        cfg = get_market_data_config("okx", "spot") or {}
        super().__init__("okx", "spot",
                         api_endpoint=self.TICKERS,
                         redis_key=get_market_data_key("okx", "spot"),
                         update_interval=cfg.get("update_interval", 3))

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        res = self._get_many([self.INSTRUMENTS, self.TICKERS])
        return self._merge(res[self.INSTRUMENTS].get("data", []), res[self.TICKERS].get("data", []))

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:   # single-endpoint fallback (tests/ABC)
        return self._merge(self._get(self.INSTRUMENTS).get("data", []), resp.get("data", []))

    def _merge(self, instruments, tickers) -> List[Dict[str, Any]]:
        meta = {i["instId"]: i for i in instruments
                if i.get("state") == "live" and i.get("quoteCcy") in ACCEPTABLE_QUOTE_ASSETS
                and i.get("baseCcy")}
        out = []
        for t in tickers:
            i = meta.get(t.get("instId"))
            if not i:
                continue
            bid, ask, last = t.get("bidPx"), t.get("askPx"), t.get("last")
            if not _prices_ok(bid, ask, last):
                continue
            out.append({"symbol": i["baseCcy"] + i["quoteCcy"], "data": {
                "instId": i["instId"],                                # OKX subscribe target
                "best_bid": bid, "best_ask": ask, "lastPrice": last,  # full-precision strings
                "24h_volume_usdt": _fnum(t.get("volCcy24h")),         # quote-ccy (USDT/USDC) 24h volume
            }})
        return out


class OkxFuturesMarketData(BaseMarketDataHandler):
    """SWAP (perps): merge instruments (settleCcy/ctVal/state) with tickers + mark-price. LINEAR only."""

    INSTRUMENTS = f"{OKX}/api/v5/public/instruments?instType=SWAP"
    TICKERS = f"{OKX}/api/v5/market/tickers?instType=SWAP"
    MARK = f"{OKX}/api/v5/public/mark-price?instType=SWAP"

    def __init__(self):
        cfg = get_market_data_config("okx", "futures") or {}
        super().__init__("okx", "futures",
                         api_endpoint=self.TICKERS,
                         redis_key=get_market_data_key("okx", "futures"),
                         update_interval=cfg.get("update_interval", 3))

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        res = self._get_many([self.INSTRUMENTS, self.TICKERS, self.MARK])
        return self._merge(res[self.INSTRUMENTS].get("data", []),
                           res[self.TICKERS].get("data", []), res[self.MARK].get("data", []))

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:   # single-endpoint fallback (tests/ABC)
        return self._merge(self._get(self.INSTRUMENTS).get("data", []),
                           resp.get("data", []), self._get(self.MARK).get("data", []))

    def _merge(self, instruments, tickers, mark) -> List[Dict[str, Any]]:
        meta = {i["instId"]: i for i in instruments
                if i.get("state") == "live" and i.get("settleCcy") in ACCEPTABLE_QUOTE_ASSETS}
        marks = {m["instId"]: m.get("markPx") for m in (mark or [])}
        out = []
        for t in tickers:
            i = meta.get(t.get("instId"))
            if not i:
                continue
            bid, ask, last = t.get("bidPx"), t.get("askPx"), t.get("last")
            if not _prices_ok(bid, ask, last):
                continue
            canon = (i.get("instFamily") or "").replace("-", "")
            if not canon:
                continue   # no instFamily -> can't form a canonical symbol; skip rather than key on ""
            ct_val = _fnum(i.get("ctVal"))
            # USD notional 24h volume = contracts * contract-value(base) * last(price). volCcy24h is in
            # base ccy for SWAP, so vol24h(contracts)*ctVal*last is the cleaner USDT figure.
            vol_usdt = _fnum(t.get("vol24h")) * ct_val * _fnum(last)
            out.append({"symbol": canon, "data": {
                "instId": i["instId"],
                "best_bid": bid, "best_ask": ask, "lastPrice": last,
                "24h_volume_usdt": vol_usdt,
                "markPrice": marks.get(i["instId"]),
                "ctVal": i.get("ctVal"), "ctValCcy": i.get("ctValCcy"),   # contract -> base conversion
            }})
        return out
