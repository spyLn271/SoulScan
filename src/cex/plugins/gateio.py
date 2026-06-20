#!/usr/bin/env python3
"""
Gate.io order books on the cex_v2 core — spot AND futures (USDT-M perps) — via the WEBSITE feeds
(spot-webws / fx-webws on wsbridge.com, origin www.gate.com). These carry the SAME deep book the
gate.com UI shows; gate's documented public API (api.gateio.ws REST + v4 WS) serves a thin/sampled book
(~tens-of-x shallower, verified live), so we deliberately use the website feeds the engine must match.

  spot    -> wss://spot-webws.wsbridge.com/v3?device_type=0     v3  method "depth.update"
  futures -> wss://fx-webws.wsbridge.com/v4/ws/usdt?device_type=0   v4  channel "futures.order_book"

Both push a FULL top-N snapshot EVERY frame (spot params[0]=clean=true always, 30/30 levels; futures
event "all") -> STATELESS, collapse-to-latest, no diff/checksum.

SUBSCRIBE — two different shapes:
  spot: ONE v3 depth.subscribe carrying a NESTED ARRAY of [wire, limit, merge] (this is how it BATCHES —
        sequential depth.subscribe calls REPLACE each other; the nested array does not):
          {"method":"depth.subscribe","params":[["BTC_USDT",30,"0.00001"],...],"id":n}
  futures: ONE futures.order_book subscribe PER contract (v4 channel subs accumulate on a connection):
          {"channel":"futures.order_book","event":"subscribe","payload":[wire,"30",merge],"id":n,"time":s}

MERGE param = the symbol's NATIVE price tick (spot 10^-precision; futures order_price_round). A fixed
"0.1" is BTC's tick but COLLAPSES cheap coins to an empty book (e.g. DOGE@0.08) -> they never stream;
the native tick gives the raw, deepest book for every symbol. The tick (and futures quanto_multiplier)
is published per-symbol in the md hash and read at subscribe.

Spot depth sizes are BASE-ASSET ([[price, size]]). Futures sizes are in CONTRACTS ([{p,s}]) ->
x quanto_multiplier (base per contract; BTC=0.0001) to keep the stream uniform base-asset.

Keepalive: spot a client {"method":"server.ping"}; futures {"channel":"futures.ping","time":s}.
Symbols: wire BTC_USDT <-> canonical BTCUSDT (normalize=replace("_","").upper(); _wire splits USDT/USDC).
"""
import asyncio
import heapq
import itertools
import json as _json
import time
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

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
       "Chrome/149.0.0.0 Safari/537.36")


def _isnum(v) -> bool:
    try:
        float(v)
        return True
    except (ValueError, TypeError):
        return False


def _topn(levels, n, reverse):
    """Top-n levels by NUMERIC price, dropping rows with a bad price; bids=highest n, asks=lowest n."""
    good = [l for l in levels if isinstance(l, (list, tuple)) and len(l) >= 2 and _isnum(l[0])]
    return (heapq.nlargest(n, good, key=lambda l: float(l[0])) if reverse
            else heapq.nsmallest(n, good, key=lambda l: float(l[0])))


class _GateioBase(OrderBookConnector):
    def __init__(self, market_type: str, worker_id: int = None, num_workers: int = None):
        super().__init__("gateio", market_type, worker_id=worker_id, num_workers=num_workers)
        self.depth_level = int(self.special_params.get("depth_level", 30))
        self.sub_delay = float(self.special_params.get("sub_delay", 0.01))
        self._req = itertools.count(1)
        self._tick: Dict[str, str] = {}    # canonical -> native price tick (the merge param)

    async def ws_url(self) -> str:
        return self.market_config["ws_url"]

    async def _connection_kwargs(self, proxied: bool) -> dict:
        kw = await super()._connection_kwargs(proxied)
        kw["origin"] = "https://www.gate.com"        # wsbridge rejects the handshake without it
        kw["user_agent_header"] = _UA
        return kw

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.replace("_", "").upper()       # BTC_USDT -> BTCUSDT (idempotent on canonical)

    def _wire(self, canon: str) -> str:
        for q in ("USDT", "USDC"):
            if canon.endswith(q) and len(canon) > len(q):
                return f"{canon[:-len(q)]}_{q}"       # BTCUSDT -> BTC_USDT
        return canon

    async def _load_spec(self, symbols: List[str]) -> None:
        """Cache per-symbol native tick (+ futures quanto) from the md hash. Re-run each (re)subscribe."""
        try:
            vals = await self.redis.hmget(get_market_data_key("gateio", self.market_type), *symbols)
        except Exception:
            return
        for s, v in zip(symbols, vals):
            if not v:
                continue
            try:
                d = _loads(v)
                tk = d.get("tick")
                if tk:
                    self._tick[s] = str(tk)
                self._cache_extra(s, d)
            except Exception:
                pass

    def _cache_extra(self, canon: str, md: dict) -> None:
        pass   # futures overrides to cache quanto_multiplier


class GateioSpotConnector(_GateioBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("spot", worker_id=worker_id, num_workers=num_workers)
        self._conn_syms: Dict[int, list] = {}   # id(ws) -> assigned symbols (for tick-resolution re-subscribe)
        self._conn_sent: Dict[int, int] = {}    # id(ws) -> # symbols sent in the last subscribe

    async def _send_subscribe(self, ws, symbols: List[str]) -> int:
        await self._load_spec(symbols)
        # ONE nested-array depth.subscribe = the batched form (sequential calls would replace). Re-sending
        # the full resolvable set REPLACES the subscription, so it cleanly picks up newly-resolved symbols.
        params = [[self._wire(s), self.depth_level, self._tick[s]] for s in symbols if s in self._tick]
        if params:
            await ws.send(_json.dumps({"method": "depth.subscribe", "params": params, "id": next(self._req)}))
        n = len(params)
        if n < len(symbols):
            log = self.logger.warning if n == 0 else self.logger.info
            log("SUBSCRIBE %d/%d symbols (%d awaiting tick)", n, len(symbols), len(symbols) - n)
        return n

    async def subscribe(self, ws, symbols: List[str]) -> None:
        self._conn_syms[id(ws)] = list(symbols)
        self._conn_sent[id(ws)] = await self._send_subscribe(ws, symbols)

    async def _ping_loop(self, ws):
        # Also the ONLY retry path for tick-less symbols: a connection never reconnects while co-located
        # symbols keep streaming, so subscribe() is never re-run by the core. Each tick we re-resolve any
        # still-unsubscribed assigned symbols and, if a tick has since published, re-send the full set.
        interval = max((self.ping_interval or 20000) / 1000.0, 5)
        key = id(ws)
        try:
            while not self.shutdown.is_set():
                try:
                    await ws.send(_json.dumps({"method": "server.ping", "id": next(self._req), "params": []}))
                except Exception:
                    break
                syms = self._conn_syms.get(key)
                if syms and self._conn_sent.get(key, 0) < len(syms):
                    await self._load_spec(syms)
                    if sum(1 for s in syms if s in self._tick) > self._conn_sent.get(key, 0):
                        try:
                            self._conn_sent[key] = await self._send_subscribe(ws, syms)
                        except Exception:
                            break
                await asyncio.sleep(interval)
        finally:
            self._conn_syms.pop(key, None)
            self._conn_sent.pop(key, None)

    def parse(self, raw) -> Optional[List[Book]]:
        try:
            m = _loads(raw)
        except (ValueError, TypeError):
            return None
        if not isinstance(m, dict) or m.get("method") != "depth.update":
            return None   # sub ack / server.pong / other
        p = m.get("params")
        if not isinstance(p, list) or len(p) < 3:
            return None
        if p[0] is False:   # clean=false would be an incremental diff (never seen live); never apply as a snapshot
            return None
        res, sym = p[1], p[2]
        if not isinstance(res, dict) or not sym:
            return None
        canon = self.normalize_symbol(sym)
        L = self.depth_level
        bids = _topn([l for l in (res.get("bids") or [])], L, reverse=True)
        asks = _topn([l for l in (res.get("asks") or [])], L, reverse=False)
        if not bids or not asks:
            return None
        try:
            if float(bids[0][0]) >= float(asks[0][0]):
                return None
        except (ValueError, TypeError, IndexError):
            return None
        ts = res.get("update") or res.get("current")
        return [Book(symbol=canon, bids=[[x[0], x[1]] for x in bids], asks=[[x[0], x[1]] for x in asks],
                     event_ts_ms=int(float(ts) * 1000) if _isnum(ts) else None)]


class GateioFuturesConnector(_GateioBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("futures", worker_id=worker_id, num_workers=num_workers)
        self._mult: Dict[str, float] = {}   # canonical -> quanto_multiplier (base per contract)

    def _cache_extra(self, canon: str, md: dict) -> None:
        qm = md.get("quanto_multiplier")
        try:
            if qm is not None and float(qm) > 0:
                self._mult[canon] = float(qm)
        except (ValueError, TypeError):
            pass

    async def subscribe(self, ws, symbols: List[str]) -> None:
        await self._load_spec(symbols)
        t = int(time.time())
        n = 0
        for s in symbols:
            tk = self._tick.get(s)
            if tk is None:
                continue
            await ws.send(_json.dumps({"channel": "futures.order_book", "event": "subscribe",
                                       "payload": [self._wire(s), str(self.depth_level), tk],
                                       "id": next(self._req), "time": t}))
            n += 1
            if self.sub_delay:
                await asyncio.sleep(self.sub_delay)
        self.logger.info("SUBSCRIBE %d/%d futures contracts", n, len(symbols))

    async def _ping_loop(self, ws):
        interval = max((self.ping_interval or 20000) / 1000.0, 5)
        while not self.shutdown.is_set():
            try:
                await ws.send(_json.dumps({"channel": "futures.ping", "time": int(time.time())}))
            except Exception:
                break
            await asyncio.sleep(interval)

    def _scale(self, canon: str, levels):
        mult = self._mult.get(canon, 1.0)
        if mult == 1.0:
            return [[p, s] for p, s in levels]   # mult unknown yet -> raw contracts briefly, self-corrects
        out = []
        for p, s in levels:
            try:
                out.append([p, float(s) * mult])
            except (ValueError, TypeError):
                out.append([p, s])
        return out

    def parse(self, raw) -> Optional[List[Book]]:
        try:
            m = _loads(raw)
        except (ValueError, TypeError):
            return None
        if not isinstance(m, dict) or m.get("channel") != "futures.order_book" or m.get("event") != "all":
            return None
        res = m.get("result")
        if not isinstance(res, dict):
            return None
        sym = res.get("contract")
        if not sym:
            return None
        canon = self.normalize_symbol(sym)
        L = self.depth_level
        bids = _topn([[x.get("p"), x.get("s")] for x in (res.get("bids") or [])
                      if isinstance(x, dict) and x.get("s") is not None], L, reverse=True)
        asks = _topn([[x.get("p"), x.get("s")] for x in (res.get("asks") or [])
                      if isinstance(x, dict) and x.get("s") is not None], L, reverse=False)
        bids = self._scale(canon, bids)
        asks = self._scale(canon, asks)
        if not bids or not asks:
            return None
        try:
            if float(bids[0][0]) >= float(asks[0][0]):
                return None
        except (ValueError, TypeError, IndexError):
            return None
        ts = res.get("t")
        return [Book(symbol=canon, bids=bids, asks=asks,
                     event_ts_ms=int(ts) if isinstance(ts, (int, float)) else None)]
