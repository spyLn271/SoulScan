#!/usr/bin/env python3
"""
cex_v2 config — the Redis key CONTRACT the Rust engine depends on (copied verbatim from the
running system; do not change these formats), plus redis/monitoring/proxy constants and the
registry of exchanges migrated onto cex_v2 (one at a time). Self-contained: only the unified
settings layer (src.settings.cex_config) is imported for env-sourced values.
"""
from typing import Any, Dict, Optional

from src.cex_v2.settings import settings as _cexv2_settings
from src.settings import cex_config as _ss

# --- symbol filtering ---
ACCEPTABLE_QUOTE_ASSETS = ["USDT", "USDC"]

# --- Redis key contract (MUST match the engine + legacy producer) ---
HEALTH_PREFIX = "health"
SCHEMA_VERSION = 1
ORDERBOOK_MAXLEN = 10           # keep last N entries per stream (consumers read latest)
ERROR_QUEUE_MAX_ENTRIES = 5000  # LTRIM cap on every error-queue push


def get_redis_config() -> Dict[str, Any]:
    return {
        "host": _ss.REDIS_HOST, "port": _ss.REDIS_PORT, "db": _ss.REDIS_DB,
        "password": _ss.REDIS_PASSWORD, "decode_responses": True,
    }


def get_stream_key(exchange: str, market_type: str, symbol: str) -> str:
    return f"stream:orderbook:{exchange.lower()}:{market_type.lower()}:{symbol.upper()}"


def get_active_symbols_key(exchange: str, market_type: str) -> str:
    return f"symbols_status:{exchange.lower()}:{market_type.lower()}:active_symbols"


def get_inactive_symbols_key(exchange: str, market_type: str) -> str:
    return f"symbols_status:{exchange.lower()}:{market_type.lower()}:inactive_symbols"


def get_heartbeat_key(exchange: str, market_type: str, worker_id) -> str:
    wid = "none" if worker_id is None else worker_id
    return f"{HEALTH_PREFIX}:{exchange.lower()}:{market_type.lower()}:{wid}"


def get_error_queue_key(exchange: str) -> str:
    return f"watchdog:{exchange.lower()}:error_queue"


def get_market_data_key(exchange: str, market_type: str) -> str:
    return f"{market_type.lower()}-market-data:{exchange.lower()}"


# --- worker / monitoring constants ---
MONITORING = {
    "connection_timeout": 30,        # ws open timeout
    "stale_stream_timeout": 60,      # reconnect if no frame for this long (silence detector)
    "recv_poll_timeout": 10,         # per-recv timeout so staleness is checked periodically
    "heartbeat_interval": 15,        # how often a worker writes its heartbeat
    "heartbeat_ttl": 60,             # TTL on the heartbeat key; supervisor treats expiry as hung
    "hung_worker_timeout": 120,      # supervisor: no fresh heartbeat/progress this long => restart
    "startup_grace": 120,            # supervisor: warmup before hung-detection
    "symbol_refresh_interval": 30,   # re-scan market-data for new/removed symbols
    "stale_symbol_age": 120,         # active symbol with no write in this long counts as stale (obs)
    "cleanup_after_failures": 3,     # mark inactive + delete stream only after N sustained failures
    "evict_after_scans": 20,         # delist-evict only after a symbol is BOTH gone from the feeder AND
                                     # not streaming for N consecutive scans (~10min) — long enough that a
                                     # trading halt (feeder drops a 0-priced pair) never looks like a delist
    "reconcile_min_fraction": 0.5,   # startup reconcile SKIPS if the feeder universe < this * (active+inactive)
                                     # already in redis (degraded/cold feeder) — never mass-evict live symbols
    "flush_interval": 0.05,          # default: pipeline latest->Redis every 50ms
    "check_interval": 5,             # supervisor poll interval
}


# --- centralized logging (one dir for ALL cex_v2 logs; structured JSON + rotation + perf log) ---
# Sourced from the typed pydantic Cexv2Settings (CEX_V2_* env / .env) — no raw os.environ here.
# Each process writes its own dedicated file in LOGGING["dir"]:
#   supervisor.log | orderbook_<ex>_<mt>[_w<n>].log | marketdata.log  (+ perf_<same>.log)
_s = _cexv2_settings()
LOGGING: Dict[str, Any] = {
    "dir": str(_s.log_dir),
    "level": _s.log_level,
    "json": _s.log_json,
    "console": _s.console_log,
    "max_bytes": _s.log_max_bytes,
    "backup_count": _s.log_backups,
    "perf_interval": _s.perf_interval,
}

# --- prometheus metrics (one /metrics http endpoint per process) ---
# OB workers bind port_base+1.. (assigned by the supervisor); the market-data process binds md_port.
# The 500 gap keeps the two bands from ever colliding as exchanges are onboarded.
METRICS: Dict[str, Any] = {
    "enabled": _s.metrics_enabled,
    "port_base": _s.metrics_port_base,
    "bind_host": _s.metrics_bind_host,
    "md_base": _s.metrics_port_base + 500,   # market-data band (per-exchange offset added at runtime)
}


def metrics_offset(exchange: str) -> int:
    """Stable per-exchange index (EXCHANGES registration order). Lets order-book + market-data ports be
    deterministic regardless of how supervisors are split, so two per-exchange runs never collide."""
    try:
        return list(EXCHANGES).index(exchange)
    except ValueError:
        return 0

# --- SOCKS5 proxies (danted; egress IPs in comments) ---
PROXIES = [
    {"host": "157.180.8.159", "port": 1080, "exit_ip": "157.180.8.162"},
    {"host": "157.180.8.159", "port": 1081, "exit_ip": "157.180.8.163"},
]

# --- exchanges migrated onto cex_v2 (add one at a time) ---
EXCHANGES: Dict[str, Dict[str, Any]] = {
    "binance": {
        "enabled": True,
        "name": "Binance",
        "spot": {
            "enabled": True,
            "ws_url": "wss://stream.binance.com:9443/stream",  # combined-stream endpoint
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.05,
            "ping_interval": None,    # server pings us; websockets auto-pongs
            "workers": 1,
            "special_params": {"depth_level": 20, "update_speed": "100ms"},
        },
        "futures": {
            "enabled": True,
            "ws_url": "wss://fstream.binance.com/stream",  # USDT-M futures combined stream
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.05,
            "ping_interval": None,
            "workers": 1,
            "special_params": {"depth_level": 20, "update_speed": "100ms"},
        },
        "proxy": {"use_proxy": False},
    },
    "bybit": {
        "enabled": True,
        "name": "Bybit",
        # bybit v5 unified API (snapshot+delta orderbook). depth=subscribe level, emit_levels=truncate
        # at emit (full book kept internally), sub_chunk=args per subscribe frame (v5 limit ~10).
        "spot": {
            "enabled": True,
            # mergedDepth = the feed the bybit WEBSITE renders: levels grouped to a per-symbol dumpScale
            # with SUMMED sizes. v5's raw per-tick sizes read "off" vs the website, so spot uses ws2.
            "ws_url": "wss://ws2.bybit.com/spot/ws/quote/v2",
            "connection_type": "batched",
            "symbols_per_connection": 20,
            "flush_interval": 0.05,
            "ping_interval": 20000,   # ws2 ping {"ping": ts} every ~20s
            "workers": 1,
            "special_params": {"limit": 40, "default_dump_scale": 4},
        },
        "futures": {
            "enabled": True,
            # realtime_w = the website's AGGREGATED derivatives book (gzip frames; topic
            # orderBook_20@m1.H.<SYM>). Covers USDT + USDC perps. The v5 raw book has ungrouped
            # (smaller) sizes that read "off" vs the website — same reason spot uses ws2.
            "ws_url": "wss://ws2.bybit.com/realtime_w",
            "connection_type": "batched",
            "symbols_per_connection": 20,
            "flush_interval": 0.05,
            "ping_interval": 20000,
            "workers": 1,
            "special_params": {"depth": 20, "merge": "m1", "tier": "H", "emit_levels": 20, "sub_chunk": 10},
        },
        "proxy": {"use_proxy": False},  # reachable direct from this host
    },
    "okx": {
        "enabled": True,
        "name": "OKX",
        # Documented public `books` channel (wss://ws.okx.com:8443/ws/v5/public). VERIFIED 2026-06-15 to
        # be byte-for-byte identical to the website's books-grouped(tickSz) feed (100% on stable levels,
        # 7 symbols incl perps) while being more robust: documented/stable endpoint, 400 levels, CRC32
        # `checksum` per message for gap detection, no per-symbol grouping. SNAPSHOT+UPDATE incremental.
        "spot": {
            "enabled": True,
            "ws_url": "wss://ws.okx.com:8443/ws/v5/public",
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.05,
            "ping_interval": 20000,   # OKX text "ping" within 30s idle; we ping every 20s
            "workers": 1,
            "special_params": {"emit_levels": 20, "sub_chunk": 50},
        },
        "futures": {   # OKX SWAP = perpetuals (LINEAR / USDT+USDC-settled only; inverse excluded)
            "enabled": True,
            "ws_url": "wss://ws.okx.com:8443/ws/v5/public",
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.05,
            "ping_interval": 20000,
            "workers": 1,
            "special_params": {"emit_levels": 20, "sub_chunk": 50},
        },
        "proxy": {"use_proxy": False},  # OKX REST + WS reachable direct from this host
    },
    "bitget": {
        "enabled": True,
        "name": "Bitget",
        # Documented v2 public `books` channel (wss://ws.bitget.com/v2/ws/public). VERIFIED 2026-06-16 to
        # be byte-for-byte identical (numerically) to the website's v1 depth(scale=tick) feed — 100.0000%
        # on stable levels, 8 symbols/both markets — while being more robust: documented/current (no v1
        # deprecation), deeper (200 spot / 500 futures), plain text, seq/pseq gap-detection integrity.
        # SNAPSHOT+UPDATE incremental; plain symbols; text "ping" keepalive.
        "spot": {
            "enabled": True,
            "ws_url": "wss://ws.bitget.com/v2/ws/public",
            "connection_type": "batched",
            "symbols_per_connection": 50,
            "flush_interval": 0.05,
            "ping_interval": 20000,   # Bitget v2 text "ping" within 30s idle; we ping every 20s
            "workers": 1,
            "special_params": {"emit_levels": 20, "sub_chunk": 50},
        },
        "futures": {   # linear perps: USDT-FUTURES + USDC-FUTURES (per-symbol instType from market-data)
            "enabled": True,
            "ws_url": "wss://ws.bitget.com/v2/ws/public",
            "connection_type": "batched",
            "symbols_per_connection": 50,
            "flush_interval": 0.05,
            "ping_interval": 20000,
            "workers": 1,
            "special_params": {"emit_levels": 20, "sub_chunk": 50, "default_inst_type": "USDT-FUTURES"},
        },
        "proxy": {"use_proxy": False},  # Bitget REST + WS reachable direct from this host
    },
    "mexc": {
        "enabled": True,
        "name": "MEXC",
        # SPOT only (futures is a separate API — see below). PROTOBUF v3 WS (wss://wbs-api.mexc.com/ws):
        # channel spot@public.limit.depth.v3.api.pb@<SYM>@<level> = full top-N snapshot per frame
        # (stateless), decoded via the vendored mexc_proto schema. MEXC removed the JSON depth channels.
        "spot": {
            "enabled": True,
            "ws_url": "wss://wbs-api.mexc.com/ws",
            "connection_type": "batched",
            "symbols_per_connection": 30,   # MEXC HARD cap: 30 subscriptions/connection
            "flush_interval": 0.05,
            "ping_interval": 20000,         # MEXC text {"method":"PING"} within 60s
            "workers": 1,
            "special_params": {"depth_level": 20, "sub_chunk": 10},
        },
        "futures": {
            # MEXC futures protobuf is the SAME wbs-api.mexc.com/ws endpoint, channel
            # futures@public.limit.depth.v3.api.pb@<SYM>@<lvl> — but GEO-RESTRICTED from this datacenter:
            # "Blocked!" from our direct IP AND via the danted proxies (all Hetzner/Germany). Spot on the
            # same endpoint works. REST contract.mexc.com IS reachable. Disabled until a region-allowed
            # egress is available (verified 2026-06-16).
            "enabled": False,
        },
        "proxy": {"use_proxy": False},
    },
    "bingx": {
        "enabled": True,
        "name": "BingX",
        # Documented WS depth (GZIP frames, full top-N snapshot -> stateless). Spot asks come DESCENDING
        # so the plugin sorts both sides. Keepalive: server Ping / client Pong -> ping_message()="Pong"
        # (connector clamps the ping loop to >=5s). Dashed symbols (BTC-USDT) -> canonical BTCUSDT.
        "spot": {
            "enabled": True,
            "ws_url": "wss://open-api-ws.bingx.com/market",
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.05,
            "ping_interval": 5000,
            "workers": 1,
            "special_params": {"depth_level": 20},
        },
        "futures": {   # USDT + USDC perps
            "enabled": True,
            "ws_url": "wss://open-api-swap.bingx.com/swap-market",
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.05,
            "ping_interval": 5000,
            "workers": 1,
            "special_params": {"depth_level": 20},
        },
        "proxy": {"use_proxy": False},
    },
    "bitmart": {
        "enabled": True,
        "name": "BitMart",
        # Spot + futures are DIFFERENT endpoints/protocols (see plugins/bitmart.py): spot stateless
        # (op:subscribe, spot/depth20, text "ping"); futures stateful split-by-side (action:subscribe,
        # futures/depth20, {action:ping}). Both full-snapshot. Symbols: spot BTC_USDT -> BTCUSDT.
        "spot": {
            "enabled": True,
            "ws_url": "wss://ws-manager-compress.bitmart.com/api?protocol=1.1",
            "connection_type": "batched",
            # BitMart caps WS connections PER HOST (~21 on the spot host ws-manager-compress); 1079 spot
            # symbols / 100 = ~11 conns (under the cap). Futures is a DIFFERENT host (openapi-ws-v2) with
            # its own pool, so spot's ~11 + futures' ~16 coexist (27 total, verified live, no churn).
            # Per-connection sub limit is high (>=115 verified), so pack many per connection.
            "symbols_per_connection": 100,
            "flush_interval": 0.05,
            "ping_interval": 10000,
            "workers": 1,
            "special_params": {"depth_level": 20, "sub_chunk": 20, "live_pack": True, "max_connections": 20},
        },
        "futures": {   # USDT + USDC perps (all product_type=1; USD inverse excluded)
            "enabled": True,
            "ws_url": "wss://openapi-ws-v2.bitmart.com/api?protocol=1.1",
            "connection_type": "batched",
            "symbols_per_connection": 50,
            "flush_interval": 0.05,
            "ping_interval": 10000,
            "workers": 1,
            "special_params": {"depth_level": 20, "sub_chunk": 20, "live_pack": True, "max_connections": 20},
        },
        "proxy": {"use_proxy": False},
    },
    "coinex": {
        "enabled": True,
        "name": "CoinEx",
        # Uses the v1 WS the WEBSITE renders (see plugins/coinex.py) — NOT the documented v2, whose depth
        # is a thinner book missing large resting liquidity v1 carries. GZIP frames; one
        # depth.subscribe_multi per connection (REPLACES -> all the connection's markets in one call,
        # ~200/call ok); clean snapshot then PURE diffs (amount 0 = remove) -> stateful + crc32-checksum
        # resync. Symbols already canonical (BTCUSDT). Futures linear, base-asset depth (NO conversion).
        "spot": {
            "enabled": True,
            "ws_url": "wss://ws.coinex.com/",
            "connection_type": "batched",
            "symbols_per_connection": 200,   # subscribe_multi REPLACES -> one call/conn; 200/call verified
            "flush_interval": 0.05,
            "ping_interval": 10000,
            "workers": 1,
            "special_params": {"depth_level": 50, "merge": "0"},   # merge "0" = raw/finest price granularity
        },
        "futures": {   # USDT + USDC LINEAR perps (inverse + USD-margined excluded)
            "enabled": True,
            "ws_url": "wss://perpetual.coinex.com/",
            "connection_type": "batched",
            "symbols_per_connection": 200,
            "flush_interval": 0.05,
            "ping_interval": 10000,
            "workers": 1,
            "special_params": {"depth_level": 50, "merge": "0"},
        },
        "proxy": {"use_proxy": False},
    },
}


def get_exchange_config(exchange: str) -> Optional[Dict[str, Any]]:
    return EXCHANGES.get(exchange)


# --- market-data feeder registry (REST ticker pollers; one handler per enabled pair) ---
# redis_key is derived via get_market_data_key(); fields written must include full-precision
# string best_bid/best_ask/lastPrice + 24h_volume_usdt + any exchange subscribe-metadata.
MARKET_DATA: Dict[str, Dict[str, Any]] = {
    "binance": {
        "spot": {"enabled": True, "api_endpoint": "https://api.binance.com/api/v3/ticker/24hr",
                 "update_interval": 3},
        "futures": {"enabled": True, "update_interval": 3,
                    # USDT-M futures need 3 merged endpoints (24hr ticker + book + premium index)
                    "endpoints": {
                        "ticker": "https://fapi.binance.com/fapi/v1/ticker/24hr",
                        "book": "https://fapi.binance.com/fapi/v1/ticker/bookTicker",
                        "premium": "https://fapi.binance.com/fapi/v1/premiumIndex",
                    }},
    },
    "bybit": {
        # bybit v5 /market/tickers carries bid/ask/last/volume (+ futures index/mark/funding) in ONE
        # response per category, so both markets are single-endpoint (no merge like binance futures).
        "spot": {"enabled": True, "update_interval": 3,
                 "api_endpoint": "https://api.bybit.com/v5/market/tickers?category=spot"},
        "futures": {"enabled": True, "update_interval": 3,
                    "api_endpoint": "https://api.bybit.com/v5/market/tickers?category=linear"},
    },
    "okx": {
        # OKX handlers do a multi-endpoint merge internally (instruments + tickers [+ mark-price for
        # futures]); endpoints are defined in the handler. Spot keyed by baseCcy+quoteCcy, futures by
        # instFamily (BTC-USDT -> BTCUSDT); the OKX instId is stored as a field for the OB subscribe.
        "spot": {"enabled": True, "update_interval": 3,
                 "api_endpoint": "https://www.okx.com/api/v5/market/tickers?instType=SPOT"},
        "futures": {"enabled": True, "update_interval": 3,
                    "api_endpoint": "https://www.okx.com/api/v5/market/tickers?instType=SWAP"},
    },
    "bitget": {
        # Bitget handlers do a multi-endpoint v2 merge internally (symbols/contracts + tickers; futures
        # spans USDT-FUTURES + USDC-FUTURES). Keyed by the plain symbol; futures stores `instType` (the
        # product line) as a field for the order-book subscribe.
        # Spot handler drops Bitget's tokenized stocks/ETFs (areaSymbol=="yes", e.g. rNVDA/rQQQ): they
        # report a ticker + volume but have NO L2 order book (RFQ-quoted), so they'd pollute the universe
        # with ~497 symbols that never produce an order-book snapshot. Filtering them => universe == the
        # real crypto spot set (~581), all of which stream.
        "spot": {"enabled": True, "update_interval": 3,
                 "api_endpoint": "https://api.bitget.com/api/v2/spot/market/tickers"},
        "futures": {"enabled": True, "update_interval": 3,
                    "api_endpoint": "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES"},
    },
    "mexc": {
        # SPOT: merge /exchangeInfo (filter) + /ticker/24hr (bid/ask/last + quoteVolume). Plain symbols.
        "spot": {"enabled": True, "update_interval": 3,
                 "api_endpoint": "https://api.mexc.com/api/v3/ticker/24hr"},
        "futures": {"enabled": False},   # futures WS geo-blocked from this DC (see EXCHANGES.mexc.futures)
    },
    "bingx": {
        # Spot: common/symbols + ticker/24hr. Futures: swap contracts + ticker + premiumIndex (funding/
        # mark). Dash symbols -> canonical; BingX returns prices as numbers (handler stringifies them).
        "spot": {"enabled": True, "update_interval": 3,
                 "api_endpoint": "https://open-api.bingx.com/openApi/spot/v1/ticker/24hr"},
        "futures": {"enabled": True, "update_interval": 3,
                    "api_endpoint": "https://open-api.bingx.com/openApi/swap/v2/quote/ticker"},
    },
    "bitmart": {
        # Spot: symbols/details + v3 tickers (positional arrays). Futures: v2 contract/details alone
        # (has last/index/funding/OI but no bid/ask -> last-priced md). Symbols -> canonical.
        "spot": {"enabled": True, "update_interval": 3,
                 "api_endpoint": "https://api-cloud.bitmart.com/spot/quotation/v3/tickers"},
        "futures": {"enabled": True, "update_interval": 3,
                    "api_endpoint": "https://api-cloud-v2.bitmart.com/contract/public/details"},
    },
    "coinex": {
        # Spot: market + ticker (last + `value` quote-volume; NO bid/ask -> last-priced). Futures: market +
        # ticker (last/index/mark/OI) + funding-rate. Symbols already canonical (BASE+QUOTE). Linear only.
        "spot": {"enabled": True, "update_interval": 3,
                 "api_endpoint": "https://api.coinex.com/v2/spot/ticker"},
        "futures": {"enabled": True, "update_interval": 3,
                    "api_endpoint": "https://api.coinex.com/v2/futures/ticker"},
    },
}


def get_market_data_config(exchange: str, market_type: str = "spot") -> Optional[Dict[str, Any]]:
    return MARKET_DATA.get(exchange, {}).get(market_type)
