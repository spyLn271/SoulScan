#!/usr/bin/env python3
"""
KuCoin order books on the cex_v2 core — spot AND futures (USDT-M perps) — via the DOCUMENTED public WS
(bullet-public token flow). The kucoin.com website wraps this same feed in socket.io over ws-web-*; the
documented raw-JSON API carries the IDENTICAL `level2Depth50` topic (verified: documented WS == REST 48/50
exact; HAR structure-matched), so we use the cleaner official transport.

  spot    -> POST https://api.kucoin.com/api/v1/bullet-public         -> wss://ws-api-spot.kucoin.com/?token=..
  futures -> POST https://api-futures.kucoin.com/api/v1/bullet-public -> wss://ws-api-futures.kucoin.com/?token=..

Order-book topic `/spotMarket/level2Depth50:<SYM>` / `/contractMarket/level2Depth50:<SYM>` pushes a FULL
top-50 snapshot EVERY frame (subject "level2", data {asks,bids,timestamp}) -> STATELESS, collapse-to-latest.
Symbols batch comma-separated, <=100 per topic. Keepalive = client {"type":"ping"} (server {"type":"pong"}).

Spot depth sizes are BASE-ASSET ([[price, size]] strings). Futures sizes are in CONTRACTS (integer lots) ->
x multiplier (base per contract; XBTUSDTM = 0.001) to keep the stream uniform base-asset (okx/gate pattern).
multiplier + the exchange wire symbol are published per-symbol in the futures/spot md hash and read at
subscribe (the OB needs the wire to subscribe: spot BTC-USDT, futures XBTUSDTM where XBT=BTC).
"""
import asyncio
import heapq
import itertools
import json as _json
import time
import uuid
from typing import Dict, List, Optional

import httpx

from src.cex_v2.core.connector import OrderBookConnector, Book
from src.cex_v2.config import get_market_data_key

try:
    import orjson

    def _loads(raw):
        return orjson.loads(raw)
except ImportError:
    def _loads(raw):
        return _json.loads(raw)


def _isnum(v) -> bool:
    try:
        float(v)
        return True
    except (ValueError, TypeError):
        return False


def _topn(levels, n, reverse):
    good = [l for l in levels if isinstance(l, (list, tuple)) and len(l) >= 2 and _isnum(l[0])]
    return (heapq.nlargest(n, good, key=lambda l: float(l[0])) if reverse
            else heapq.nsmallest(n, good, key=lambda l: float(l[0])))


class _KucoinBase(OrderBookConnector):
    _rest_base = None       # api.kucoin.com / api-futures.kucoin.com
    _topic_prefix = None    # /spotMarket/level2Depth50 : / /contractMarket/level2Depth50 :

    def __init__(self, market_type: str, worker_id: int = None, num_workers: int = None):
        super().__init__("kucoin", market_type, worker_id=worker_id, num_workers=num_workers)
        self.depth_level = int(self.special_params.get("depth_level", 50))
        self.topic_chunk = int(self.special_params.get("topic_chunk", 100))   # kucoin: <=100 symbols/topic
        self._req = itertools.count(1)
        self._wire: Dict[str, str] = {}   # canonical -> exchange wire symbol (BTC-USDT / XBTUSDTM)
        self._conn_pending: Dict[int, list] = {}   # id(ws) -> symbols still awaiting a wire (retry in _ping_loop)
        self._server_ping_ms = None

    def _bullet(self):
        r = httpx.post(self._rest_base + "/api/v1/bullet-public", timeout=10)
        r.raise_for_status()
        d = r.json()["data"]
        srv = d["instanceServers"][0]
        return d["token"], srv["endpoint"], srv.get("pingInterval")

    async def ws_url(self) -> str:
        # fresh bullet token + unique connectId per (re)connection
        token, endpoint, ping_ms = await asyncio.to_thread(self._bullet)
        if ping_ms:
            self._server_ping_ms = ping_ms   # let keepalive self-adjust to the assigned server's pingInterval
        return f"{endpoint}?token={token}&connectId={uuid.uuid4().hex}"

    async def _load_spec(self, symbols: List[str]) -> None:
        """Cache the exchange wire symbol (+ futures multiplier) from the md hash. Re-run each (re)subscribe."""
        try:
            vals = await self.redis.hmget(get_market_data_key("kucoin", self.market_type), *symbols)
        except Exception:
            return
        for s, v in zip(symbols, vals):
            if not v:
                continue
            try:
                d = _loads(v)
                w = d.get("wire")
                if w:
                    self._wire[s] = w
                self._cache_extra(s, d)
            except Exception:
                pass

    def _cache_extra(self, canon: str, md: dict) -> None:
        pass   # futures overrides to cache multiplier

    async def _send_new(self, ws, symbols: List[str]) -> list:
        """Subscribe the symbols whose wire is now known (comma-batched, <=topic_chunk/topic). KuCoin
        subscribe is ADDITIVE, so this only ever sends not-yet-sent wires. Returns symbols still awaiting a wire."""
        wires = [self._wire[s] for s in symbols if s in self._wire]
        pending = [s for s in symbols if s not in self._wire]
        for i in range(0, len(wires), self.topic_chunk):
            chunk = wires[i:i + self.topic_chunk]
            await ws.send(_json.dumps({"id": str(next(self._req)), "type": "subscribe",
                                       "topic": self._topic_prefix + ",".join(chunk), "response": True}))
        if pending:
            (self.logger.warning if not wires else self.logger.info)(
                "SUBSCRIBE %d symbols, %d awaiting wire", len(wires), len(pending))
        return pending

    async def subscribe(self, ws, symbols: List[str]) -> None:
        await self._load_spec(symbols)
        self._conn_pending[id(ws)] = await self._send_new(ws, symbols)

    async def _ping_loop(self, ws):
        # keepalive + the ONLY retry path for symbols whose wire wasn't in the md hash at subscribe (a
        # connection never reconnects while co-located symbols keep streaming, so subscribe() isn't re-run).
        srv = (self._server_ping_ms or 0) * 0.6 / 1000.0
        cfg = (self.ping_interval or 15000) / 1000.0
        interval = max(min(cfg, srv) if srv else cfg, 5)
        key = id(ws)
        try:
            while not self.shutdown.is_set():
                try:
                    await ws.send(_json.dumps({"id": str(next(self._req)), "type": "ping"}))
                except Exception:
                    break
                pending = self._conn_pending.get(key)
                if pending:
                    await self._load_spec(pending)
                    self._conn_pending[key] = await self._send_new(ws, pending)
                await asyncio.sleep(interval)
        finally:
            self._conn_pending.pop(key, None)

    def _scale(self, canon: str, levels):
        return [[l[0], l[1]] for l in (levels or []) if isinstance(l, (list, tuple)) and len(l) >= 2]

    def parse(self, raw) -> Optional[List[Book]]:
        try:
            m = _loads(raw)
        except (ValueError, TypeError):
            return None
        if not isinstance(m, dict) or m.get("type") != "message" or m.get("subject") != "level2":
            return None   # welcome / pong / ack / non-depth
        data = m.get("data")
        topic = m.get("topic", "")
        if not isinstance(data, dict) or ":" not in topic:
            return None
        wire = topic.rsplit(":", 1)[-1]
        if not wire or "," in wire:
            return None
        canon = self.normalize_symbol(wire)
        L = self.depth_level
        bids = _topn(self._scale(canon, data.get("bids")), L, reverse=True)
        asks = _topn(self._scale(canon, data.get("asks")), L, reverse=False)
        if not bids or not asks:
            return None
        try:
            if float(bids[0][0]) >= float(asks[0][0]):
                return None
        except (ValueError, TypeError, IndexError):
            return None
        ts = data.get("timestamp")
        return [Book(symbol=canon, bids=bids, asks=asks,
                     event_ts_ms=int(ts) if isinstance(ts, (int, float)) else None)]


class KucoinSpotConnector(_KucoinBase):
    _rest_base = "https://api.kucoin.com"
    _topic_prefix = "/spotMarket/level2Depth50:"

    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("spot", worker_id=worker_id, num_workers=num_workers)

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.replace("-", "").upper()   # BTC-USDT -> BTCUSDT


class KucoinFuturesConnector(_KucoinBase):
    _rest_base = "https://api-futures.kucoin.com"
    _topic_prefix = "/contractMarket/level2Depth50:"

    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("futures", worker_id=worker_id, num_workers=num_workers)
        self._mult: Dict[str, float] = {}   # canonical -> contract multiplier (base per contract)

    def normalize_symbol(self, symbol: str) -> str:
        s = symbol.upper()
        if s.endswith("M"):
            s = s[:-1]                       # XBTUSDTM -> XBTUSDT (strip the perpetual marker)
        if s.startswith("XBTUSDT") or s.startswith("XBTUSDC"):
            s = "BTC" + s[3:]                # bitcoin only: XBTUSDT -> BTCUSDT (don't mangle an XBT*-named base)
        return s

    def _cache_extra(self, canon: str, md: dict) -> None:
        mu = md.get("multiplier")
        try:
            if mu is not None and float(mu) > 0:
                self._mult[canon] = float(mu)
        except (ValueError, TypeError):
            pass

    def _scale(self, canon: str, levels):
        mult = self._mult.get(canon, 1.0)
        out = []
        for l in (levels or []):
            if not (isinstance(l, (list, tuple)) and len(l) >= 2):
                continue
            if mult == 1.0:
                out.append([l[0], l[1]])
            else:
                try:
                    out.append([l[0], float(l[1]) * mult])
                except (ValueError, TypeError):
                    out.append([l[0], l[1]])
        return out
