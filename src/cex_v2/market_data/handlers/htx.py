#!/usr/bin/env python3
"""HTX (Huobi) market-data handlers (cex_v2). Both carry a real best bid/ask (NOT last-priced).

SPOT    : /v2/settings/common/symbols (state online + quote USDT/USDC) + /market/tickers (close=last,
          bid/ask BBO, `vol`=quote-ccy 24h turnover). Symbol code `sc` is lowercase concat (btcusdt)
          -> canonical = sc.upper() (BTCUSDT).
FUTURES : USDT-M LINEAR swaps. linear-swap-api swap_contract_info (contract_size + the listed universe)
          + linear-swap-ex batch_merged (bid/ask/close + `trade_turnover`=quote turnover) +
          swap_batch_funding_rate. contract_code is dashed (BTC-USDT) -> canonical BTCUSDT; contract_size
          and contract_code are PUBLISHED so the OB plugin can resolve the wire code + convert contract
          sizes to base-asset (x contract_size), the same way okx publishes instId/ctVal.
"""
from typing import Any, Dict, List

from src.cex_v2.market_data.base import BaseMarketDataHandler
from src.cex_v2.config import get_market_data_config, get_market_data_key, ACCEPTABLE_QUOTE_ASSETS


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


def _s(v):
    return str(v) if v is not None else None


class HtxSpotMarketData(BaseMarketDataHandler):
    SYMBOLS = "https://api.htx.com/v2/settings/common/symbols"
    TICKER = "https://api.htx.com/market/tickers"

    def __init__(self):
        cfg = get_market_data_config("htx", "spot") or {}
        super().__init__("htx", "spot", api_endpoint=self.TICKER,
                         redis_key=get_market_data_key("htx", "spot"),
                         update_interval=cfg.get("update_interval", 3))

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        res = self._get_many([self.SYMBOLS, self.TICKER])
        return self._merge(res[self.SYMBOLS].get("data") or [], res[self.TICKER].get("data") or [])

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:   # single-endpoint fallback (ABC/tests)
        return self._merge(self._get(self.SYMBOLS).get("data") or [], resp.get("data") or [])

    def _merge(self, symbols, tickers) -> List[Dict[str, Any]]:
        ok = {s.get("sc") for s in symbols
              if s.get("state") == "online" and str(s.get("qc", "")).upper() in ACCEPTABLE_QUOTE_ASSETS}
        out = []
        for t in tickers:
            sc = t.get("symbol")
            # real-BBO venue: require a live bid AND ask (drops no-book illiquid pairs, e.g. SYRUPUSDT with
            # bid=0) so the hash never carries a 0/None BBO — same gate as binance/okx/bitmart-spot.
            if sc not in ok or not (_pos(t.get("bid")) and _pos(t.get("ask"))):
                continue
            out.append({"symbol": sc.upper(), "data": {
                "best_bid": _s(t.get("bid")), "best_ask": _s(t.get("ask")),
                "lastPrice": _s(t.get("close")),
                "24h_volume_usdt": _fnum(t.get("vol")),   # `vol` = quote-ccy 24h turnover
            }})
        return out


class HtxFuturesMarketData(BaseMarketDataHandler):
    CONTRACTS = "https://api.hbdm.com/linear-swap-api/v1/swap_contract_info"
    TICKER = "https://api.hbdm.com/linear-swap-ex/market/detail/batch_merged"
    FUNDING = "https://api.hbdm.com/linear-swap-api/v1/swap_batch_funding_rate"

    def __init__(self):
        cfg = get_market_data_config("htx", "futures") or {}
        super().__init__("htx", "futures", api_endpoint=self.TICKER,
                         redis_key=get_market_data_key("htx", "futures"),
                         update_interval=cfg.get("update_interval", 3))

    def fetch_parsed(self) -> List[Dict[str, Any]]:
        res = self._get_many([self.CONTRACTS, self.TICKER, self.FUNDING])
        return self._merge(res[self.CONTRACTS].get("data") or [], res[self.TICKER].get("ticks") or [],
                           res[self.FUNDING].get("data") or [])

    def parse_api_response(self, resp) -> List[Dict[str, Any]]:   # single-endpoint fallback (ABC/tests)
        res = self._get_many([self.CONTRACTS, self.FUNDING])
        return self._merge(res[self.CONTRACTS].get("data") or [], resp.get("ticks") or [],
                           res[self.FUNDING].get("data") or [])

    def _merge(self, contracts, tickers, funding) -> List[Dict[str, Any]]:
        info = {c.get("contract_code"): c for c in contracts
                if c.get("contract_status") == 1 and c.get("business_type") == "swap"
                and str(c.get("trade_partition", "")).upper() in ACCEPTABLE_QUOTE_ASSETS}
        fund = {f.get("contract_code"): f for f in (funding or [])}
        out = []
        for t in tickers:
            code = t.get("contract_code")
            c = info.get(code)
            if not c:
                continue
            bid, ask = t.get("bid"), t.get("ask")
            bp = bid[0] if isinstance(bid, (list, tuple)) and bid else None
            ap = ask[0] if isinstance(ask, (list, tuple)) and ask else None
            if not (_pos(bp) and _pos(ap)):   # real-BBO venue: require a live bid AND ask
                continue
            bb, ba = _s(bp), _s(ap)
            f = fund.get(code, {})
            nft = _inum(f.get("next_funding_time"))
            out.append({"symbol": code.replace("-", "").upper(), "data": {
                "best_bid": bb, "best_ask": ba,
                "lastPrice": _s(t.get("close")),
                "24h_volume_usdt": _fnum(t.get("trade_turnover")),   # quote-ccy 24h turnover
                "contract_code": code,                               # dashed wire code (OB resolves it)
                "contract_size": _fnum(c.get("contract_size")),      # base-asset per contract (OB scales by it)
                "funding_rate_percent": _fnum(f.get("funding_rate")) * 100,
                "next_funding_time": nft // 1000 if nft else None,   # ms -> s
            }})
        return out
