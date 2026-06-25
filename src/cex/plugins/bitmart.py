import asyncio
import gzip
import json as _json
import time
import zlib
from typing import Dict, List, Optional

from src.cex.core.connector import OrderBookConnector, Book
from src.cex.config import get_market_data_key, MONITORING

try:
    import orjson

    def _loads(raw):
        return orjson.loads(raw)
except ImportError:
    def _loads(raw):
        return _json.loads(raw)


def _text(raw):
    if isinstance(raw, (bytes, bytearray)):
        for fn in (lambda b: zlib.decompress(b, -15), lambda b: gzip.decompress(b), lambda b: zlib.decompress(b)):
            try:
                return fn(raw).decode("utf-8", "replace")
            except Exception:
                pass
        return raw.decode("utf-8", "replace")
    return raw


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def _ts(v):
    if v is None:
        return None

    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def _vol(v) -> float:
    try:
        return float(_loads(v).get("24h_volume_usdt") or 0.0)
    except Exception:
        return 0.0


def _sorted_book(rb, ra, n):
    try:
        bids = sorted(([p, q] for p, q in rb if float(q) > 0), key=lambda x: float(x[0]), reverse=True)[:n]
        asks = sorted(([p, q] for p, q in ra if float(q) > 0), key=lambda x: float(x[0]))[:n]
    except (ValueError, TypeError):
        return None

    if not bids or not asks or float(bids[0][0]) >= float(asks[0][0]):
        return None

    return bids, asks


def _scale_levels(levels, mult):
    if mult == 1.0:
        return levels

    out = []
    for p, s in levels:
        try:
            out.append([p, float(s) * mult])
        except (ValueError, TypeError):
            out.append([p, s])

    return out


class _BitmartBase(OrderBookConnector):
    def __init__(
            self,
            market_type: str,
            worker_id: int = None,
            num_workers: int = None
    ):
        super().__init__("bitmart", market_type, worker_id=worker_id, num_workers=num_workers)
        self.depth_level = int(self.special_params.get("depth_level", 20))
        self.sub_chunk = int(self.special_params.get("sub_chunk", 20))
        self._live_pack = bool(self.special_params.get("live_pack", True))
        self._max_conns = int(self.special_params.get("max_connections", 20))
        self._conns: Dict[str, dict] = {}
        self._cid_seq = 0
        self._bg_tasks: set = set()

    async def ws_url(self) -> str:
        return self.market_config["ws_url"]

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.upper().replace("_", "")   # BTC_USDT -> BTCUSDT

    async def get_symbols(self) -> List[str]:
        try:
            data = await self.redis.hgetall(get_market_data_key(self.exchange, self.market_type))
        except Exception:
            data = {}

        pairs = [(s, _vol(v)) for s, v in (data or {}).items() if not s.startswith("_")]
        pairs.sort(key=lambda x: (-x[1], x[0]))

        return self._filter_for_worker([s for s, _ in pairs])

    def _batches(self, symbols: List[str]) -> List[List[str]]:
        n = self.symbols_per_connection
        batches = [list(symbols[i:i + n]) for i in range(0, len(symbols), n)]
        self._conns = {}
        for i, batch in enumerate(batches):
            self._conns[f"b{i}"] = {"symbols": batch, "ws": None}
        return batches

    async def subscribe(self, ws, symbols: List[str]) -> None:
        e = next((v for v in self._conns.values() if v["symbols"] is symbols), None)

        if e is not None:
            e["ws"] = ws
        else:
            self.logger.warning(
                "bitmart %s: subscribe got an unregistered symbol list (%d) — sending anyway",
                self.market_type,
                len(symbols)
            )

        await self._send_subscribe(ws, list(symbols))

    async def _send_subscribe(self, ws, syms: List[str], live: bool = False) -> None:
        raise NotImplementedError

    async def _pack_new(self, new_syms: List[str]) -> None:
        n = self.symbols_per_connection
        added = 0

        for sym in new_syms:
            cands = [e for e in self._conns.values() if len(e["symbols"]) < n]
            target = next((e for e in reversed(cands) if e["ws"] is not None), cands[-1] if cands else None)

            if target is not None:
                target["symbols"].append(sym)

                if target["ws"] is not None:
                    try:
                        await self._send_subscribe(target["ws"], [sym], live=True)
                    except Exception as ex:
                        self.logger.debug("bitmart live-add send failed (resubscribe on reconnect): %s", ex)
            else:
                if len(self._conns) >= self._max_conns:
                    self.logger.warning(
                        "bitmart %s: at %d connections (host cap ~21) — raise "
                        "symbols_per_connection",
                        self.market_type,
                        len(self._conns)
                    )

                self._cid_seq += 1
                cid = f"g{self._cid_seq}"
                newlist = [sym]
                self._conns[cid] = {"symbols": newlist, "ws": None}
                self._conn_tasks[cid] = asyncio.create_task(self._connection_loop(cid, newlist))

            added += 1

        if added:
            self.logger.info(
                "bitmart %s: packed %d new symbols across %d conns",
                self.market_type,
                added,
                len(self._conns)
            )

    def _prune_from_registry(self, evicted) -> None:
        ev = set(evicted)

        for e in self._conns.values():
            if any(s in ev for s in e["symbols"]):
                e["symbols"][:] = [s for s in e["symbols"] if s not in ev]

        for s in ev:
            self._on_evict_symbol(s)

    def _on_evict_symbol(self, sym) -> None:
        pass

    async def _monitor_loop(self):
        evict_after = MONITORING.get("evict_after_scans", 3)

        while not self.shutdown.is_set():
            await asyncio.sleep(MONITORING["symbol_refresh_interval"])

            try:
                current = set(await self.get_symbols())
                if not current:
                    continue

                new = current - self.monitored
                if new and self._live_pack:
                    self.monitored |= new
                    await self._pack_new(sorted(new))

                if not self.is_distributed:
                    now = time.time()
                    for s in current:
                        self._absent_scans.pop(s, None)

                    evict = []
                    for s in (self.monitored - current):
                        if now - self.last_update_wall.get(s, 0) < self.stale_symbol_age:
                            self._absent_scans.pop(s, None)
                            continue

                        self._absent_scans[s] = self._absent_scans.get(s, 0) + 1
                        if self._absent_scans[s] >= evict_after:
                            evict.append(s)

                    if evict:
                        await self._evict(evict)
                        self._prune_from_registry(evict)
            except Exception as e:
                self.logger.error("monitor error: %s", e)


class BitmartSpotConnector(_BitmartBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("spot", worker_id=worker_id, num_workers=num_workers)

    def _ws_symbol(self, canon: str) -> str:
        return canon[:-4] + "_" + canon[-4:]   # BTCUSDT -> BTC_USDT

    async def _send_subscribe(self, ws, syms: List[str], live: bool = False) -> None:
        args = [f"spot/depth{self.depth_level}:{self._ws_symbol(self.normalize_symbol(s))}" for s in syms]
        for chunk in _chunks(args, self.sub_chunk):
            await ws.send(_json.dumps({"op": "subscribe", "args": chunk}))

        self.logger.info("SUBSCRIBE %d symbols (spot/depth%d)", len(args), self.depth_level)

    async def ping_message(self) -> Optional[str]:
        return "ping"   # BitMart spot: text ping -> "pong"

    def parse(self, raw) -> Optional[List[Book]]:
        raw = _text(raw)
        if raw.strip() in ("pong", "ping"):
            return None

        try:
            m = _loads(raw)
        except (ValueError, TypeError):
            return None

        if not isinstance(m, dict):
            return None

        if not str(m.get("table", "")).startswith("spot/depth"):
            if m.get("errorMessage") or m.get("error_message"):
                self.logger.warning("bitmart spot sub error: %s", str(m)[:140])

            return None

        data = m.get("data")
        if not data:
            return None

        d = data[0] if isinstance(data, list) else data
        sym = self.normalize_symbol(d.get("symbol", ""))
        rb, ra = d.get("bids"), d.get("asks")
        if not sym or not rb or not ra:
            return None

        bk = _sorted_book([(x[0], x[1]) for x in rb], [(x[0], x[1]) for x in ra], self.depth_level)
        if not bk:
            return None

        return [Book(symbol=sym, bids=bk[0], asks=bk[1], event_ts_ms=_ts(d.get("ms_t")))]


class BitmartFuturesConnector(_BitmartBase):
    def __init__(self, worker_id: int = None, num_workers: int = None):
        super().__init__("futures", worker_id=worker_id, num_workers=num_workers)
        self._book: Dict[str, dict] = {}
        self._mult: Dict[str, float] = {}
        self._mult_failed: set = set()

    async def _load_mult(self, canon_syms) -> None:
        key = get_market_data_key("bitmart", "futures")
        todo = [s for s in canon_syms if s not in self._mult and s not in self._mult_failed]
        for _ in range(8):
            if not todo:
                return

            try:
                vals = await self.redis.hmget(key, *todo)
            except Exception:
                vals = [None] * len(todo)

            for s, v in zip(todo, vals):
                if v:
                    try:
                        cs = _loads(v).get("contract_size")
                        if cs is not None and float(cs) > 0:   # >0: a 0/None would zero every size
                            self._mult[s] = float(cs)
                    except (ValueError, TypeError, AttributeError):
                        pass

            todo = [s for s in todo if s not in self._mult]
            if not todo:
                return

            await asyncio.sleep(1.0)
        self._mult_failed.update(todo)
        self.logger.warning(
            "bitmart futures: %d symbols missing/invalid contract_size (sizes raw): %s",
            len(todo),
            todo[:5]
        )

    async def _send_subscribe(self, ws, syms: List[str], live: bool = False) -> None:
        args, canon = [], []
        for s in syms:
            sym = self.normalize_symbol(s)
            canon.append(sym)
            self._book[sym] = {"b": None, "a": None}
            args.append(f"futures/depth{self.depth_level}:{sym}")

        if live:
            t = asyncio.create_task(self._load_mult(canon))
            self._bg_tasks.add(t)
            t.add_done_callback(self._bg_tasks.discard)
        else:
            await self._load_mult(canon)

        for chunk in _chunks(args, self.sub_chunk):
            await ws.send(_json.dumps({"action": "subscribe", "args": chunk}))

        self.logger.info("SUBSCRIBE %d symbols (futures/depth%d)", len(args), self.depth_level)

    def _on_evict_symbol(self, sym) -> None:
        self._book.pop(sym, None)
        self._mult.pop(sym, None)

    async def ping_message(self) -> Optional[str]:
        return _json.dumps({"action": "ping"})   # BitMart futures: JSON ping -> {"group":"System","data":"pong"}

    def parse(self, raw) -> Optional[List[Book]]:
        raw = _text(raw)

        try:
            m = _loads(raw)
        except (ValueError, TypeError):
            return None

        if not isinstance(m, dict):
            return None

        if m.get("group") == "System":
            return None

        if m.get("success") is False:
            self.logger.warning("bitmart futures sub error: %s", str(m)[:140])
            return None

        if "data" not in m:
            return None

        data = m.get("data")
        d = data[0] if isinstance(data, list) else data
        if not isinstance(d, dict):
            return None

        sym = self.normalize_symbol(d.get("symbol", ""))
        way = d.get("way")
        if not sym or way not in (1, 2, "1", "2"):
            return None

        levels = [
            [x.get("price"), x.get("vol")] for x in (d.get("depths") or [])
            if isinstance(x, dict) and x.get("price") is not None and x.get("vol") is not None
        ]
        st = self._book.setdefault(sym, {"b": None, "a": None})
        st["b" if way in (1, "1") else "a"] = levels
        if st["b"] is None or st["a"] is None:
            return None

        bk = _sorted_book([(p, q) for p, q in st["b"]], [(p, q) for p, q in st["a"]], self.depth_level)
        if not bk:
            return None

        mult = self._mult.get(sym, 1.0)

        return [
            Book(
                symbol=sym,
                bids=_scale_levels(bk[0], mult),
                asks=_scale_levels(bk[1], mult),
                event_ts_ms=_ts(d.get("ms_t"))
            )
        ]
