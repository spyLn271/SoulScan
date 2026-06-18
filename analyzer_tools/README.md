# analyzer_tools

Hand tools for inspecting the **cex_v2** pipeline live. These are operator/diagnostic utilities
(read-only against Redis), not part of the producer/feeder runtime. Run them from the repo root
with the project venv.

## ob_view.py — live order-book viewer + symbol lister

Reads the cex_v2 Redis key contract (`stream:orderbook:{exchange}:{market}:{SYMBOL}` and the feeder's
`{market}-market-data:{exchange}` hash). Dependency-free (just `redis` + stdlib + raw ANSI).

**Browse what's available:**
```bash
.venv/bin/python analyzer_tools/ob_view.py --market spot    --list --top 20      # top 20 spot by 24h volume
.venv/bin/python analyzer_tools/ob_view.py --market futures --list --top 20      # top 20 futures
.venv/bin/python analyzer_tools/ob_view.py --market spot    --list --filter PEPE # substring search
.venv/bin/python analyzer_tools/ob_view.py --market futures --list               # full list
```
Sorted by 24h volume; shows feeder bid/ask + stream freshness (green <5s, `—` = no stream yet).
`--list` is the default when `--symbol` is omitted.

**Watch one symbol live** (a `watch`-style ladder that redraws in place — asks/red on top, spread,
bids/green below; qty bars scaled to depth; header shows recv-age, mid, spread in bps):
```bash
.venv/bin/python analyzer_tools/ob_view.py --market spot    --symbol BTCUSDT
.venv/bin/python analyzer_tools/ob_view.py --market futures --symbol BTCUSDT --depth 20 --interval 0.2
```

Flags: `--exchange` (default `binance`), `--market` `spot|futures`, `--symbol`, `--depth` (default 15),
`--interval` seconds (default 0.3), `--list`, `--filter`, `--top`. `Ctrl-C` to quit.

## Logs

All cex_v2 processes write to one central dir — **`logs/cex_v2/`** (override with `CEX_V2_LOG_DIR`) —
as structured **JSON lines** with rotation (100MB × 10). One dedicated file per process:

```
logs/cex_v2/supervisor.log
logs/cex_v2/orderbook_<exchange>_<market>[_w<n>].log
logs/cex_v2/marketdata.log
logs/cex_v2/perf_<same>.log          # periodic performance snapshots (throughput + latency)
```

Read them with `jq`:
```bash
tail -f logs/cex_v2/orderbook_binance_spot.log | jq .                 # live operational stream
tail -f logs/cex_v2/perf_orderbook_binance_spot.log | jq '{ts,msgs_per_s,flush_p99_ms,active,reconnects}'
jq -r 'select(.level=="ERROR") | .ts+" "+.logger+" "+.msg' logs/cex_v2/*.log   # all errors
```

Perf records (`kind:"perf"`, every `CEX_V2_PERF_INTERVAL`=30s): order-book carries `msgs_per_s`,
`flush_p50/p99/max_ms`, `active`, `reconnects`, `conn_errors`, `backpressured`; market-data carries
`fetch_p50/p99_ms`, `store_p50/max_ms`, `updates/ok/fail`, `last_count`.

Env knobs: `CEX_V2_LOG_DIR`, `CEX_V2_LOG_LEVEL` (INFO), `CEX_V2_CONSOLE_LOG=1` (echo to stderr; off by
default to avoid tmux flooding), `CEX_V2_LOG_JSON=0` (human text instead of JSON), `CEX_V2_PERF_INTERVAL`.
