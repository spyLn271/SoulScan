#!/usr/bin/env python3
"""
Live order-book viewer for cex_v2 Redis streams — a `watch`-style ladder that REDRAWS IN PLACE
(cursor-home + clear-to-end), no scrolling/spam. Compare it side-by-side with the exchange website.

  .venv/bin/python analyzer_tools/ob_view.py --exchange binance --market spot --symbol BTCUSDT
  .venv/bin/python analyzer_tools/ob_view.py --exchange binance --market futures --symbol BTCUSDT --depth 20
  .venv/bin/python analyzer_tools/ob_view.py --market spot --list --top 20   # browse + latency

Reads stream:orderbook:{exchange}:{market}:{SYMBOL} (the cex_v2 key contract) + the feeder's
best bid/ask from {market}-market-data:{exchange} as a cross-check. --list also shows per-symbol
transport lag (recv_ts - exchange event_ts, median over recent entries; "—" if the feed carries no
event ts) and stream freshness (now - recv_ts), with an aggregate lag p50/p99 + freshness-bucket footer.
"""
import argparse
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import redis
from src.cex.config import get_redis_config, get_stream_key, get_market_data_key

RED = "\033[91m"; GREEN = "\033[92m"; DIM = "\033[2m"; BOLD = "\033[1m"; CYAN = "\033[96m"; RESET = "\033[0m"
HOME = "\033[H"; CLR_DOWN = "\033[0J"; CLR_ALL = "\033[2J"; HIDE = "\033[?25l"; SHOW = "\033[?25h"


def _fnum(x, w=14):
    return f"{x:>{w}.8g}"


def _bar(qty, maxq, width=22):
    n = int(round((qty / maxq) * width)) if maxq > 0 else 0
    return "█" * n


def render(r, exchange, market, symbol, depth):
    key = get_stream_key(exchange, market, symbol)
    e = r.xrevrange(key, count=1)
    out = [f"{BOLD}{CYAN} {exchange.upper()} {market} {symbol}{RESET}   {DIM}{key}{RESET}"]
    if not e:
        out.append(f"\n  {DIM}(no stream yet — waiting for data){RESET}")
        sample = [k.split(":")[-1] for k in r.scan_iter(match=f"stream:orderbook:{exchange}:{market}:*", count=50)][:12]
        if sample:
            out.append(f"  {DIM}available {exchange}/{market}: {', '.join(sample)} ...{RESET}")
        return "\n".join(out)

    eid, f = e[0]
    now = time.time() * 1000
    recv = f.get("recv_ts_ms"); ev = f.get("timestamp_ms")
    recv_age = (now - float(recv)) / 1000 if recv else None
    insert_age = (now - float(eid.split("-")[0])) / 1000
    bids = json.loads(f.get("bids", "[]"))
    asks = json.loads(f.get("asks", "[]"))
    bids = sorted(bids, key=lambda x: -float(x[0]))[:depth]
    asks = sorted(asks, key=lambda x: float(x[0]))[:depth]

    best_bid = float(bids[0][0]) if bids else 0.0
    best_ask = float(asks[0][0]) if asks else 0.0
    mid = (best_bid + best_ask) / 2 if (best_bid and best_ask) else 0.0
    spread = best_ask - best_bid if (best_bid and best_ask) else 0.0
    spread_bps = (spread / mid * 1e4) if mid else 0.0
    maxq = max([float(q) for _, q in (bids + asks)] + [1e-12])

    age_color = GREEN if (recv_age is not None and recv_age < 2) else (RED if recv_age is not None else DIM)
    out.append(f" recv age {age_color}{recv_age:.1f}s{RESET}  (insert {insert_age:.1f}s)   "
               f"mid {BOLD}{mid:.8g}{RESET}   spread {spread:.8g} ({spread_bps:.2f} bps)   "
               f"{DIM}{time.strftime('%H:%M:%S')}{RESET}")
    out.append(f"{DIM} {'price':>14} {'qty':>14}{RESET}")
    # asks: highest at top, best ask just above the spread line
    for p, q in reversed(asks):
        p, q = float(p), float(q)
        out.append(f"{RED} {_fnum(p)} {_fnum(q)} {DIM}{_bar(q, maxq)}{RESET}")
    out.append(f"{DIM} {'─' * 30}  spread {spread:.6g}{RESET}")
    for p, q in bids:
        p, q = float(p), float(q)
        out.append(f"{GREEN} {_fnum(p)} {_fnum(q)} {DIM}{_bar(q, maxq)}{RESET}")

    md = r.hget(get_market_data_key(exchange, market), symbol)
    if md:
        try:
            d = json.loads(md)
            out.append(f"{DIM} feeder: bid {d.get('best_bid')} ask {d.get('best_ask')} "
                       f"last {d.get('lastPrice')} vol {d.get('24h_volume_usdt')}{RESET}")
        except Exception:
            pass
    return "\n".join(out)


def _human(n):
    n = float(n or 0)
    for u in ("", "K", "M", "B"):
        if abs(n) < 1000:
            return f"{n:.1f}{u}"
        n /= 1000
    return f"{n:.1f}T"


def _stream_latency(entries, now):
    """From a stream's recent entries -> (freshness_s, transport_lag_ms_median).
    freshness = now - newest recv_ts. transport lag = median(recv_ts - event_ts) over entries that
    carry a REAL exchange event ts (timestamp_ms != recv_ts_ms -> the feed supplied one); None if the
    feed has no event ts (e.g. binance spot, which falls back to recv). Median tames per-entry skew."""
    if not entries:
        return None, None
    newest = entries[0][1]
    fresh = (now - float(newest["recv_ts_ms"])) / 1000 if newest.get("recv_ts_ms") else None
    lags = []
    for _id, f in entries:
        recv, ev = f.get("recv_ts_ms"), f.get("timestamp_ms")
        if recv and ev and ev != recv:          # ev==recv => feed has no event ts (fallback)
            lags.append(float(recv) - float(ev))
    lag = statistics.median(lags) if lags else None
    return fresh, lag


def list_symbols(r, exchange, market, filt, top):
    md = r.hgetall(get_market_data_key(exchange, market))
    md.pop("_version", None)
    now = time.time() * 1000
    sel = []
    for sym, v in md.items():
        if filt and filt.upper() not in sym:
            continue
        try:
            d = json.loads(v)
        except Exception:
            continue
        sel.append((sym, float(d.get("24h_volume_usdt") or 0), d.get("best_bid"), d.get("best_ask")))
    sel.sort(key=lambda x: -x[1])
    if top:
        sel = sel[:top]
    # one pipeline for all streams (last 10 entries each) -> fast even across hundreds of symbols
    pipe = r.pipeline(transaction=False)
    for sym, *_ in sel:
        pipe.xrevrange(get_stream_key(exchange, market, sym), count=10)
    streams = pipe.execute()

    rows = []
    for (sym, vol, bid, ask), entries in zip(sel, streams):
        fresh, lag = _stream_latency(entries, now)
        rows.append((sym, vol, bid, ask, fresh, lag))

    live = sum(1 for x in rows if x[4] is not None)
    lagvals = [x[5] for x in rows if x[5] is not None]
    print(f"{BOLD}{CYAN}{exchange} {market}{RESET}: {len(rows)} symbols, {live} with a live stream"
          f"{f'  (filter={filt})' if filt else ''}")
    print(f"{DIM}{'#':>4}  {'symbol':<16}{'24h vol':>11}  {'bid':>14} {'ask':>14}  {'lag':>8}  {'stream':>8}{RESET}")
    for i, (s, vol, bid, ask, fresh, lag) in enumerate(rows, 1):
        if fresh is None:
            fcol, fst = DIM, "—"
        else:
            fcol, fst = (GREEN if fresh < 5 else RED), f"{fresh:.1f}s"
        lst = "—" if lag is None else f"{lag:+.0f}ms"
        print(f"{i:>4}  {s:<16}{_human(vol):>11}  {str(bid):>14} {str(ask):>14}  "
              f"{DIM}{lst:>8}{RESET}  {fcol}{fst:>8}{RESET}")

    # aggregate footer: transport-lag p50/p99 (trustworthy in aggregate) + freshness buckets
    def _b(lo, hi):
        return sum(1 for x in rows if x[4] is not None and (lo is None or x[4] >= lo) and x[4] < hi)
    dead = sum(1 for x in rows if x[4] is None)
    if lagvals:
        sl = sorted(lagvals)
        p50 = sl[len(sl) // 2]; p99 = sl[min(len(sl) - 1, int(len(sl) * 0.99))]
        lagsum = f"transport lag (recv-event) p50 {p50:+.0f}ms p99 {p99:+.0f}ms over {len(lagvals)} feeds"
    else:
        lagsum = f"{DIM}transport lag: n/a (this feed has no exchange event ts){RESET}"
    print(f"{DIM}{'─'*64}{RESET}")
    print(f"  {lagsum}")
    print(f"  freshness: {GREEN}<1s {_b(None,1)}{RESET}  1-5s {_b(1,5)}  5-30s {_b(5,30)}  "
          f"{RED}>30s {_b(30,1e18)}{RESET}  {DIM}dead {dead}{RESET}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exchange", default="binance")
    ap.add_argument("--market", default="spot", choices=["spot", "futures"])
    ap.add_argument("--symbol", default=None, help="symbol to watch live; omit (or use --list) to list")
    ap.add_argument("--list", action="store_true", help="list available symbols for the market and exit")
    ap.add_argument("--filter", default=None, help="substring filter for --list (e.g. PEPE)")
    ap.add_argument("--top", type=int, default=0, help="limit --list to the top N by 24h volume")
    ap.add_argument("--depth", type=int, default=15)
    ap.add_argument("--interval", type=float, default=0.3)
    a = ap.parse_args()
    r = redis.Redis(**get_redis_config())
    if a.list or not a.symbol:
        list_symbols(r, a.exchange, a.market, a.filter, a.top)
        return
    sym = a.symbol.upper().replace("-", "").replace("_", "")

    sys.stdout.write(CLR_ALL + HIDE)
    try:
        while True:
            frame = render(r, a.exchange, a.market, sym, a.depth)
            sys.stdout.write(HOME + frame + CLR_DOWN)
            sys.stdout.flush()
            time.sleep(a.interval)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
