#!/usr/bin/env python3
"""
OKX order books on the cex_v2 core — spot AND futures (SWAP perps) — via the DOCUMENTED public
`books` channel (wss://ws.okx.com:8443/ws/v5/public).

VERIFIED 2026-06-15 (live, 7 symbols incl perps, 100.0000% match on every stable level over 45s of
parallel book maintenance): this documented channel is byte-for-byte identical to the feed the OKX
WEBSITE renders (`books-grouped` at the symbol's tickSz on wspri/ipublic). `grouping` is only a
display-aggregation knob — a no-op at tickSz. The documented channel is preferred: stable/documented
endpoint, 400 levels, and a CRC32 `checksum` per message for gap detection (stronger than a
top-of-book check), with no per-symbol grouping to resolve.

SNAPSHOT+UPDATE incremental (size "0" = remove). After each update we recompute OKX's CRC32 over the
top-25 and compare to the message `checksum`; on mismatch we raise ResyncRequired -> the core
reconnects + resubscribes -> a fresh snapshot. The connector is collapse-to-latest / stateless, so
the plugin keeps per-symbol book state and emits a full top-N Book each frame.

OKX instIds are dashed (BTC-USDT, BTC-USDT-SWAP) while our canonical symbol is BTCUSDT. The
market-data handler publishes the universe keyed by the CANONICAL symbol with the OKX `instId` as a
field; this plugin resolves canonical->instId (hmget) to subscribe and maps instId->canonical on
parse, so the core only ever sees canonical symbols (active / stream / monitored all one space).
"""
import heapq
import json as _json
import zlib
from typing import Dict, List, Optional

from src.cex.core.connector import OrderBookConnector, Book, ResyncRequired
from src.cex.config import get_market_data_key
from src.cex.observability import metrics as _m

try:
    import orjson

    def _loads(raw):
        return orjson.loads(raw)
except ImportError:
    def _loads(raw):
        return _json.loads(raw)


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def _okx_checksum(bids_desc, asks_asc) -> int:
    """OKX books CRC32 over the interleaved top-25 (bidPx:bidSz:askPx:askSz:...), as a signed int32.
    Validated live 2026-06-15: 200/200 messages matched the exchange's checksum."""
    parts = []
    for i in range(25):
        if i < len(bids_desc):
            parts.append(f"{bids_desc[i][0]}:{bids_desc[i][1]}")
        if i < len(asks_asc):
            parts.append(f"{asks_asc[i][0]}:{asks_asc[i][1]}")
    crc = zlib.crc32(":".join(parts).encode())
    return crc - (1 << 32) if crc >= (1 << 31) else crc


def _scale_levels(levels, mult):
    """Convert CONTRACT sizes to BASE-ASSET (size*mult); price is NEVER touched. mult==1.0 -> unchanged.
    OKX SWAP book sizes are in CONTRACTS (mult = ctVal = base-asset per contract); the rest of the
    ecosystem stores base-asset sizes, so the stream stays uniform. coerce_levels floats it at flush."""
    if mult == 1.0:
        return levels
    out = []
    for p, s in levels:
        try:
            out.append([p, float(s) * mult])
        except (ValueError, TypeError):
            out.append([p, s])
    return out


def _apply(side: Dict[str, str], levels) -> None:
    for lvl in (levels or []):
        if not (isinstance(lvl, (list, tuple)) and len(lvl) >= 2):
            continue
        px, sz = lvl[0], lvl[1]
        try:
            remove = float(sz) <= 0
            float(px)       # validate price is numeric too: a corrupt px would otherwise persist and
                            # crash the heapq float() sort on every subsequent frame.
        except (ValueError, TypeError):
            remove = True   # unparseable price/size -> drop the level (never keep a corrupt entry)
        if remove:
            side.pop(px, None)
        else:
            side[px] = sz


class _OkxBase(OrderBookConnector):
    def __init__(self, market_type: str, worker_id: int = None, num_workers: int = None):
        super().__init__("okx", market_type, worker_id=worker_id, num_workers=num_workers)
        self.emit_levels = int(self.special_params.get("emit_levels", 20))
        self.sub_chunk = int(self.special_params.get("sub_chunk", 50))
        self._book: Dict[str, dict] = {}        # canonical -> {"b":{px:sz}, "a":{px:sz}, "synced":bool}
        self._inst2canon: Dict[str, str] = {}   # OKX instId -> canonical symbol
        self._mult: Dict[str, float] = {}       # canonical -> ctVal (SWAP contract->base; spot stays empty -> 1.0)

    async def ws_url(self) -> str:
        return self.market_config["ws_url"]

    async def _connection_kwargs(self, proxied: bool) -> dict:
        kw = await super()._connection_kwargs(proxied)
        kw["origin"] = "https://www.okx.com"
        kw["compression"] = "deflate"   # OKX negotiates permessage-deflate
        return kw

    def normalize_symbol(self, symbol: str) -> str:
        # canonical: drop the SWAP suffix + dashes (BTC-USDT-SWAP / BTC-USDT -> BTCUSDT). Idempotent on
        # an already-canonical symbol. Spot vs futures never collide (separate market_type redis keys).
        return symbol.upper().replace("-SWAP", "").replace("-", "")

    async def _inst_ids(self, canon_syms) -> Dict[str, str]:
        """canonical -> OKX instId, read from the market-data hash (published by the md handler). Also
        caches the per-symbol contract multiplier (SWAP ctVal = base-asset per contract) so parse() can
        convert book sizes (which OKX sends in CONTRACTS) to base-asset. Spot has no ctVal -> stays 1.0."""
        try:
            vals = await self.redis.hmget(get_market_data_key("okx", self.market_type), *canon_syms)
        except Exception:
            vals = [None] * len(canon_syms)
        out = {}
        for s, v in zip(canon_syms, vals):
            inst = None
            if v:
                try:
                    meta = _loads(v)
                    inst = meta.get("instId")
                    ctv = meta.get("ctVal")
                    if ctv is not None:
                        try:
                            cf = float(ctv)
                            if cf > 0:
                                self._mult[s] = cf
                        except (ValueError, TypeError):
                            pass
                except Exception:
                    pass
            out[s] = inst or s   # best-effort fallback (md not yet populated -> resubscribe fixes it)
        return out

    async def subscribe(self, ws, symbols: List[str]) -> None:
        instmap = await self._inst_ids(symbols)
        args = []
        for canon in symbols:
            inst = instmap[canon]
            self._inst2canon[inst] = canon
            self._book[canon] = {"b": {}, "a": {}, "synced": False}   # reset for a clean resync
            args.append({"channel": "books", "instId": inst})
        if not args:
            return
        for chunk in _chunks(args, self.sub_chunk):
            await ws.send(_json.dumps({"op": "subscribe", "args": chunk}))
        self.logger.info("SUBSCRIBE %d symbols (books)", len(args))

    async def ping_message(self) -> Optional[str]:
        return "ping"   # OKX literal-text ping; server replies "pong"

    def parse(self, raw) -> Optional[List[Book]]:
        if raw == "pong":
            return None
        try:
            m = _loads(raw)
        except (ValueError, TypeError):
            return None
        if not isinstance(m, dict):
            return None
        if m.get("event"):
            if m.get("event") == "error":
                self.logger.warning("okx sub error: %s", str(m.get("msg"))[:140])
            return None
        arg = m.get("arg") or {}
        if arg.get("channel") != "books":
            return None
        data = m.get("data")
        if not data:
            return None
        inst = arg.get("instId")
        canon = self._inst2canon.get(inst) or self.normalize_symbol(inst or "")
        if not canon:
            return None
        d = data[0]
        st = self._book.setdefault(canon, {"b": {}, "a": {}, "synced": False})
        act = m.get("action")
        if act == "snapshot":
            st["b"] = {p: s for p, s, *_ in d.get("bids", [])}
            st["a"] = {p: s for p, s, *_ in d.get("asks", [])}
            st["synced"] = True
        elif act == "update":
            if not st["synced"]:
                return None   # gated until the first snapshot
            _apply(st["b"], d.get("bids"))
            _apply(st["a"], d.get("asks"))
        else:
            return None
        # top-k by price WITHOUT a full 400-level sort: nlargest(bids)/nsmallest(asks) is O(n) for small k.
        k = max(self.emit_levels, 25)   # need >=25 for the checksum
        bids = heapq.nlargest(k, st["b"].items(), key=lambda kv: float(kv[0]))   # descending
        asks = heapq.nsmallest(k, st["a"].items(), key=lambda kv: float(kv[0]))  # ascending
        # integrity: OKX sends a CRC32 over the top-25; if our merged book disagrees we missed an update.
        cs = d.get("checksum")
        if act == "update" and cs is not None and _okx_checksum(bids[:25], asks[:25]) != cs:
            st["synced"] = False
            _m.OB_GAPS.labels(self.exchange, self.market_type).inc()
            self.logger.warning("checksum mismatch %s -> resync", canon)
            raise ResyncRequired(f"okx {canon} checksum mismatch")
        # checksum (above) is over OKX's RAW contract sizes; scale to base-asset only on the EMITTED levels.
        mult = self._mult.get(canon, 1.0)
        out_b = _scale_levels([[p, s] for p, s in bids[:self.emit_levels]], mult)
        out_a = _scale_levels([[p, s] for p, s in asks[:self.emit_levels]], mult)
        if not out_b or not out_a:
            return None   # never emit a one-sided/empty book
        ts = d.get("ts")
        return [Book(symbol=canon, bids=out_b, asks=out_a, event_ts_ms=int(ts) if ts else None)]


class OkxSpotConnector(_OkxBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("spot", worker_id=worker_id, num_workers=num_workers)


class OkxFuturesConnector(_OkxBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("futures", worker_id=worker_id, num_workers=num_workers)
