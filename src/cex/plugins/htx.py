#!/usr/bin/env python3
"""
HTX (Huobi) order books on the cex_v2 core — spot AND futures (USDT-M linear swaps) — via the WEBSITE
sockets the HTX site itself renders:
  spot    -> wss://www.htx.com/-/s/pro/ws
  futures -> wss://www.htx.com/futures/api/linear-swap-ws   (REQUIRES Origin: https://www.htx.com)

Both push a FULL top-N depth SNAPSHOT every frame on `market.<sym>.depth.step0` (verified live: 150
levels each side, every frame a complete book) -> STATELESS, collapse-to-latest, no diff/checksum. Frames
are GZIP-compressed (spot gzips by default; futures via "zip":1) -> gzip.decompress. HTX sends a
{"ping": ts} keepalive that MUST be answered with {"pong": ts} (handled in handle_control; size-gated so
big depth frames are never double-decompressed).

Spot depth amounts are BASE-ASSET. Futures (linear swap) amounts are in CONTRACTS -> multiply by the
contract_size (base-asset per contract; e.g. BTC-USDT = 0.001) so the stream stays uniform base-asset like
every other venue (same idea as okx ctVal / bitmart contract_size). The contract_size + the dashed
contract_code are read from the market-data hash (published by the md handler), exactly as okx reads
instId/ctVal.

Symbols: spot wire is lowercase concat (btcusdt); futures wire is dashed upper (BTC-USDT). Canonical is
BTCUSDT for both -> normalize = upper().replace("-",""). Spot vs futures never collide (separate md keys).
"""
import gzip
import heapq
import json as _json
from typing import Dict, List, Optional

from src.cex.core.connector import OrderBookConnector, Book
from src.cex.config import get_market_data_key

try:
    import orjson

    def _loads(raw):
        return orjson.loads(raw)
except ImportError:
    def _loads(raw):
        return _json.loads(raw)


def _text(raw):
    """HTX frames are gzip-compressed binary; decode to str (best-effort fallback on a bad frame)."""
    if isinstance(raw, (bytes, bytearray)):
        try:
            return gzip.decompress(raw).decode("utf-8", "replace")
        except Exception:
            return bytes(raw).decode("utf-8", "replace")
    return raw


def _scale(levels, mult):
    """CONTRACT sizes -> BASE-ASSET (size*mult); price is NEVER touched. mult==1.0 -> unchanged (spot)."""
    if mult == 1.0:
        return levels
    out = []
    for lvl in levels:
        try:
            out.append([lvl[0], float(lvl[1]) * mult])
        except (ValueError, TypeError, IndexError):
            out.append(lvl)
    return out


def _topn(levels, n, reverse):
    """Top-n levels by NUMERIC price (bids: highest n; asks: lowest n). HTX sends bids desc / asks asc, but
    selecting explicitly (heapq, O(n)) costs ~nothing and removes the trust-the-server-order assumption; it
    also drops any malformed/non-numeric-price level so it can't strand the book (matches okx's nlargest/
    nsmallest)."""
    good = [lvl for lvl in levels if len(lvl) >= 2 and _isnum(lvl[0])]
    return (heapq.nlargest(n, good, key=lambda l: float(l[0])) if reverse
            else heapq.nsmallest(n, good, key=lambda l: float(l[0])))


def _isnum(v) -> bool:
    try:
        float(v)
        return True
    except (ValueError, TypeError):
        return False


class _HtxBase(OrderBookConnector):
    def __init__(self, market_type: str, worker_id: int = None, num_workers: int = None):
        super().__init__("htx", market_type, worker_id=worker_id, num_workers=num_workers)
        self.depth_level = int(self.special_params.get("depth_level", 50))
        self._mult: Dict[str, float] = {}   # canonical -> contract_size (futures; spot stays empty -> 1.0)

    async def ws_url(self) -> str:
        return self.market_config["ws_url"]

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.upper().replace("-", "")   # btcusdt / BTC-USDT -> BTCUSDT (idempotent on canonical)

    async def _wire_map(self, symbols: List[str]) -> Dict[str, str]:
        return {s: s.lower() for s in symbols}   # spot: canonical -> wire (lowercase concat)

    def _sub_msg(self, wire: str) -> dict:
        raise NotImplementedError   # per-leaf (spot pick form / futures zip form)

    async def subscribe(self, ws, symbols: List[str]) -> None:
        # HTX takes ONE `sub` per topic -> send one message per symbol (the connection's full set).
        wm = await self._wire_map(symbols)
        for s in symbols:
            await ws.send(_json.dumps(self._sub_msg(wm[s])))
        self.logger.info("SUBSCRIBE %d symbols", len(symbols))

    async def handle_control(self, ws, raw) -> bool:
        # {"ping": ts} keepalive -> reply {"pong": ts}. Frames are normally tiny gzip BYTES; also handle a
        # str-framed ping defensively (a proxy/protocol change could deliver text -> a missed pong would
        # cause silent server-side reconnect churn). Gate so big depth snapshots are never decompressed/
        # scanned here (parse() handles those once via _text); the gate is perf-only — a non-ping small
        # frame just falls through to parse(), which is harmless.
        m = None
        if isinstance(raw, (bytes, bytearray)):
            if len(raw) > 300:
                return False
            try:
                m = _loads(gzip.decompress(raw))
            except Exception:
                return False
        elif isinstance(raw, str):
            if '"ping"' not in raw:
                return False
            try:
                m = _loads(raw)
            except Exception:
                return False
        else:
            return False
        if isinstance(m, dict) and "ping" in m:
            await ws.send(_json.dumps({"pong": m["ping"]}))
            return True
        return False

    def _scale_for(self, canon: str, levels):
        return levels   # spot no-op; futures overrides with x contract_size

    def parse(self, raw) -> Optional[List[Book]]:
        try:
            m = _loads(_text(raw))
        except (ValueError, TypeError):
            return None
        if not isinstance(m, dict):
            return None
        ch = m.get("ch")
        tick = m.get("tick")
        if not ch or not isinstance(tick, dict):
            return None   # sub ack / ping / status / a non-depth channel
        parts = ch.split(".")
        if len(parts) < 2:
            return None
        canon = self.normalize_symbol(parts[1])   # market.<sym>.depth.step0 -> <sym>
        bids = tick.get("bids") or []
        asks = tick.get("asks") or []
        if not bids or not asks:
            return None   # never emit a one-sided/empty book
        L = self.depth_level
        out_b = self._scale_for(canon, _topn(bids, L, reverse=True))    # robust top-L by price (no order assumption)
        out_a = self._scale_for(canon, _topn(asks, L, reverse=False))
        try:
            if float(out_b[0][0]) >= float(out_a[0][0]):
                return None   # never emit a crossed book
        except (ValueError, TypeError, IndexError):
            return None
        ts = m.get("ts")
        return [Book(symbol=canon, bids=out_b, asks=out_a, event_ts_ms=int(ts) if ts else None)]


class HtxSpotConnector(_HtxBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("spot", worker_id=worker_id, num_workers=num_workers)

    def _sub_msg(self, wire: str) -> dict:
        # website spot form: per-symbol depth.step0 with `pick` to cap levels server-side.
        return {"sub": f"market.{wire}.depth.step0", "symbol": wire,
                "pick": [f"bids.{self.depth_level}", f"asks.{self.depth_level}"], "step": "step0"}


class HtxFuturesConnector(_HtxBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("futures", worker_id=worker_id, num_workers=num_workers)

    async def _connection_kwargs(self, proxied: bool) -> dict:
        kw = await super()._connection_kwargs(proxied)
        kw["origin"] = "https://www.htx.com"   # the futures socket rejects the handshake without it
        return kw

    def _sub_msg(self, wire: str) -> dict:
        return {"sub": f"market.{wire}.depth.step0", "zip": 1}   # zip:1 -> gzip frames

    def _derive_wire(self, canon: str) -> str:
        # fallback if the md hash hasn't published contract_code yet: BTCUSDT -> BTC-USDT.
        for q in ("USDT", "USDC"):
            if canon.endswith(q) and len(canon) > len(q):
                return f"{canon[:-len(q)]}-{q}"
        return canon

    async def _wire_map(self, symbols: List[str]) -> Dict[str, str]:
        # canonical -> dashed contract_code, and cache contract_size (mult) — both from the md hash
        # (published by the md handler), exactly as okx resolves instId + caches ctVal.
        try:
            vals = await self.redis.hmget(get_market_data_key("htx", "futures"), *symbols)
        except Exception:
            vals = [None] * len(symbols)
        out = {}
        for s, v in zip(symbols, vals):
            code = None
            if v:
                try:
                    meta = _loads(v)
                    code = meta.get("contract_code")
                    cs = meta.get("contract_size")
                    if cs is not None:
                        cf = float(cs)
                        if cf > 0:
                            self._mult[s] = cf
                except Exception:
                    pass
            out[s] = code or self._derive_wire(s)   # best-effort fallback (resubscribe fixes it once md fills)
        return out

    def _scale_for(self, canon: str, levels):
        return _scale(levels, self._mult.get(canon, 1.0))
