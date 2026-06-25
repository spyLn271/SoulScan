from typing import Any, Dict, Optional

from src.cex.settings import settings as _cexv2_settings
from src.settings import config as _ss

ACCEPTABLE_QUOTE_ASSETS = ["USDT", "USDC"]


HEALTH_PREFIX = "health"
SCHEMA_VERSION = 1
ORDERBOOK_MAXLEN = 10
ERROR_QUEUE_MAX_ENTRIES = 5000


def get_redis_config() -> Dict[str, Any]:
    return {
        "host": _ss.REDIS_HOST,
        "port": _ss.REDIS_PORT,
        "db": _ss.REDIS_DB,
        "password": _ss.REDIS_PASSWORD,
        "decode_responses": True,
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
    "flush_interval": 0.02,          # default: pipeline latest->Redis every 20ms
    "check_interval": 5,             # supervisor poll interval
}


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

METRICS: Dict[str, Any] = {
    "enabled": _s.metrics_enabled,
    "port_base": _s.metrics_port_base,
    "bind_host": _s.metrics_bind_host,
    "md_base": _s.metrics_port_base + 500,   # market-data band (per-exchange offset added at runtime)
}


def metrics_offset(exchange: str) -> int:
    try:
        return list(EXCHANGES).index(exchange)
    except ValueError:
        return 0

PROXIES = [
    {"host": "157.180.8.159", "port": 1080, "exit_ip": "157.180.8.162"},
    {"host": "157.180.8.159", "port": 1081, "exit_ip": "157.180.8.163"},
]

EXCHANGES: Dict[str, Dict[str, Any]] = {
    "binance": {
        "enabled": True,
        "name": "Binance",
        "spot": {
            "enabled": True,
            "ws_url": "wss://stream.binance.com:9443/stream",  # combined-stream endpoint
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.02,
            "ping_interval": None,    # server pings us; websockets auto-pongs
            "workers": 1,
            "special_params": {"depth_level": 20, "update_speed": "100ms"},
        },
        "futures": {
            "enabled": True,
            "ws_url": "wss://fstream.binance.com/stream",  # USDT-M futures combined stream
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.02,
            "ping_interval": None,
            "workers": 1,
            "special_params": {"depth_level": 20, "update_speed": "100ms"},
        },
        "proxy": {"use_proxy": False},
    },
    "bybit": {
        "enabled": True,
        "name": "Bybit",
        "spot": {
            "enabled": True,
            "ws_url": "wss://ws2.bybit.com/spot/ws/quote/v2",
            "connection_type": "batched",
            "symbols_per_connection": 20,
            "flush_interval": 0.02,
            "ping_interval": 20000,
            "workers": 1,
            "special_params": {"limit": 40, "default_dump_scale": 4},
        },
        "futures": {
            "enabled": True,
            "ws_url": "wss://ws2.bybit.com/realtime_w",
            "connection_type": "batched",
            "symbols_per_connection": 20,
            "flush_interval": 0.02,
            "ping_interval": 20000,
            "workers": 1,
            "special_params": {"depth": 20, "merge": "m1", "tier": "H", "emit_levels": 20, "sub_chunk": 10},
        },
        "proxy": {"use_proxy": False},  # reachable direct from this host
    },
    "okx": {
        "enabled": True,
        "name": "OKX",
        "spot": {
            "enabled": True,
            "ws_url": "wss://ws.okx.com:8443/ws/v5/public",
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.02,
            "ping_interval": 20000,   # OKX text "ping" within 30s idle; we ping every 20s
            "workers": 1,
            "special_params": {"emit_levels": 20, "sub_chunk": 50},
        },
        "futures": {   # OKX SWAP = perpetuals (LINEAR / USDT+USDC-settled only; inverse excluded)
            "enabled": True,
            "ws_url": "wss://ws.okx.com:8443/ws/v5/public",
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.02,
            "ping_interval": 20000,
            "workers": 1,
            "special_params": {"emit_levels": 20, "sub_chunk": 50},
        },
        "proxy": {"use_proxy": False},  # OKX REST + WS reachable direct from this host
    },
    "bitget": {
        "enabled": True,
        "name": "Bitget",
        "spot": {
            "enabled": True,
            "ws_url": "wss://ws.bitget.com/v2/ws/public",
            "connection_type": "batched",
            "symbols_per_connection": 50,
            "flush_interval": 0.02,
            "ping_interval": 20000,   # Bitget v2 text "ping" within 30s idle; we ping every 20s
            "workers": 1,
            "special_params": {"emit_levels": 20, "sub_chunk": 50},
        },
        "futures": {   # linear perps: USDT-FUTURES + USDC-FUTURES (per-symbol instType from market-data)
            "enabled": True,
            "ws_url": "wss://ws.bitget.com/v2/ws/public",
            "connection_type": "batched",
            "symbols_per_connection": 50,
            "flush_interval": 0.02,
            "ping_interval": 20000,
            "workers": 1,
            "special_params": {"emit_levels": 20, "sub_chunk": 50, "default_inst_type": "USDT-FUTURES"},
        },
        "proxy": {"use_proxy": False},  # Bitget REST + WS reachable direct from this host
    },
    "mexc": {
        "enabled": True,
        "name": "MEXC",
        "spot": {
            "enabled": True,
            "ws_url": "wss://wbs-api.mexc.com/ws",
            "connection_type": "batched",
            "symbols_per_connection": 30,   # MEXC HARD cap: 30 subscriptions/connection
            "flush_interval": 0.02,
            "ping_interval": 20000,         # MEXC text {"method":"PING"} within 60s
            "workers": 1,
            "special_params": {"depth_level": 20, "sub_chunk": 10},
        },
        "futures": {
            "enabled": False,
        },
        "proxy": {"use_proxy": False},
    },
    "bingx": {
        "enabled": True,
        "name": "BingX",
        "spot": {
            "enabled": True,
            "ws_url": "wss://open-api-ws.bingx.com/market",
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.02,
            "ping_interval": 5000,
            "workers": 1,
            "special_params": {"depth_level": 20},
        },
        "futures": {   # USDT + USDC perps
            "enabled": True,
            "ws_url": "wss://open-api-swap.bingx.com/swap-market",
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.02,
            "ping_interval": 5000,
            "workers": 1,
            "special_params": {"depth_level": 20},
        },
        "proxy": {"use_proxy": False},
    },
    "bitmart": {
        "enabled": True,
        "name": "BitMart",
        "spot": {
            "enabled": True,
            "ws_url": "wss://ws-manager-compress.bitmart.com/api?protocol=1.1",
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.02,
            "ping_interval": 10000,
            "workers": 1,
            "special_params": {"depth_level": 20, "sub_chunk": 20, "live_pack": True, "max_connections": 20},
        },
        "futures": {   # USDT + USDC perps (all product_type=1; USD inverse excluded)
            "enabled": True,
            "ws_url": "wss://openapi-ws-v2.bitmart.com/api?protocol=1.1",
            "connection_type": "batched",
            "symbols_per_connection": 50,
            "flush_interval": 0.02,
            "ping_interval": 10000,
            "workers": 1,
            "special_params": {"depth_level": 20, "sub_chunk": 20, "live_pack": True, "max_connections": 20},
        },
        "proxy": {"use_proxy": False},
    },
    "coinex": {
        "enabled": True,
        "name": "CoinEx",
        "spot": {
            "enabled": True,
            "ws_url": "wss://ws.coinex.com/",
            "connection_type": "batched",
            "symbols_per_connection": 200,   # subscribe_multi REPLACES -> one call/conn; 200/call verified
            "flush_interval": 0.02,
            "ping_interval": 10000,
            "workers": 1,
            "special_params": {"depth_level": 50, "merge": "0"},   # merge "0" = raw/finest price granularity
        },
        "futures": {   # USDT + USDC LINEAR perps (inverse + USD-margined excluded)
            "enabled": True,
            "ws_url": "wss://perpetual.coinex.com/",
            "connection_type": "batched",
            "symbols_per_connection": 200,
            "flush_interval": 0.02,
            "ping_interval": 10000,
            "workers": 1,
            "special_params": {"depth_level": 50, "merge": "0"},
        },
        "proxy": {"use_proxy": False},
    },
    "htx": {
        "enabled": True,
        "name": "HTX",
        "spot": {
            "enabled": True,
            "ws_url": "wss://www.htx.com/-/s/pro/ws",
            "connection_type": "batched",
            "symbols_per_connection": 50,
            "flush_interval": 0.02,
            "workers": 1,
            "special_params": {"depth_level": 50},
        },
        "futures": {   # USDT-M LINEAR swaps
            "enabled": True,
            "ws_url": "wss://www.htx.com/futures/api/linear-swap-ws",
            "connection_type": "batched",
            "symbols_per_connection": 50,
            "flush_interval": 0.02,
            "workers": 1,
            "special_params": {"depth_level": 50},
        },
        "proxy": {"use_proxy": False},
    },
    "lbank": {
        "enabled": True,
        "name": "LBank",
        "spot": {
            "enabled": True,
            "ws_url": "wss://www.lbank.com/old-wss/ccws/ws/V3/",
            "connection_type": "batched",
            "symbols_per_connection": 50,
            "flush_interval": 0.02,
            "workers": 1,
            "special_params": {"depth_level": 50, "sub_delay": 0.05},
        },
        "futures": {"enabled": False},
        "proxy": {"use_proxy": False},
    },
    "gateio": {
        "enabled": True,
        "name": "Gate.io",
        "spot": {
            "enabled": True,
            "ws_url": "wss://spot-webws.wsbridge.com/v3?device_type=0",
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.02,
            "ping_interval": 20000,
            "workers": 1,
            "special_params": {"depth_level": 30},
        },
        "futures": {   # USDT-M perps — SKIPPED (spot-only ship, revisit later)
            "enabled": False,
            "ws_url": "wss://fx-webws.wsbridge.com/v4/ws/usdt?device_type=0",
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.02,
            "ping_interval": 20000,
            "workers": 1,
            "special_params": {"depth_level": 30, "sub_delay": 0.01},
        },
        "proxy": {"use_proxy": False},
    },
    "kucoin": {
        "enabled": True,
        "name": "KuCoin",
        "spot": {
            "enabled": True,
            "ws_url": "wss://ws-api-spot.kucoin.com/",   # informational; real endpoint+token from bullet-public
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.02,
            "ping_interval": 15000,
            "workers": 1,
            "special_params": {"depth_level": 50, "topic_chunk": 100},
        },
        "futures": {   # USDT-M perps
            "enabled": True,
            "ws_url": "wss://ws-api-futures.kucoin.com/",
            "connection_type": "batched",
            "symbols_per_connection": 100,
            "flush_interval": 0.02,
            "ping_interval": 15000,
            "workers": 4,
            "special_params": {"depth_level": 50, "topic_chunk": 100},
        },
        "proxy": {"use_proxy": False},
    },
}


def get_exchange_config(exchange: str) -> Optional[Dict[str, Any]]:
    return EXCHANGES.get(exchange)


MARKET_DATA: Dict[str, Dict[str, Any]] = {
    "binance": {
        "spot": {
            "enabled": True,
            "api_endpoint": "https://api.binance.com/api/v3/ticker/24hr",
            "update_interval": 3
        },
        "futures": {"enabled": True, "update_interval": 3,
                    # USDT-M futures need 3 merged endpoints (24hr ticker + book + premium index)
                    "endpoints": {
                        "ticker": "https://fapi.binance.com/fapi/v1/ticker/24hr",
                        "book": "https://fapi.binance.com/fapi/v1/ticker/bookTicker",
                        "premium": "https://fapi.binance.com/fapi/v1/premiumIndex",
                    }},
    },
    "bybit": {
        "spot": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://api.bybit.com/v5/market/tickers?category=spot"
        },
        "futures": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://api.bybit.com/v5/market/tickers?category=linear"
        },
    },
    "okx": {
        "spot": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://www.okx.com/api/v5/market/tickers?instType=SPOT"
        },
        "futures": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://www.okx.com/api/v5/market/tickers?instType=SWAP"
        },
    },
    "bitget": {
        "spot": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://api.bitget.com/api/v2/spot/market/tickers"
        },
        "futures": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES"
        },
    },
    "mexc": {
        "spot": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://api.mexc.com/api/v3/ticker/24hr"
        },
        "futures": {
            "enabled": False
        },
    },
    "bingx": {
        "spot": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://open-api.bingx.com/openApi/spot/v1/ticker/24hr"
        },
        "futures": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://open-api.bingx.com/openApi/swap/v2/quote/ticker"
        },
    },
    "bitmart": {
        "spot": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://api-cloud.bitmart.com/spot/quotation/v3/tickers"
        },
        "futures": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://api-cloud-v2.bitmart.com/contract/public/details"
        },
    },
    "coinex": {
        "spot": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://api.coinex.com/v2/spot/ticker"
        },
        "futures": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://api.coinex.com/v2/futures/ticker"
        },
    },
    "htx": {
        "spot": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://api.htx.com/market/tickers"
        },
        "futures": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://api.hbdm.com/linear-swap-ex/market/detail/batch_merged"
        },
    },
    "lbank": {
        "spot": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://api.lbkex.com/v2/ticker.do?symbol=all"
        },
    },
    "gateio": {
        "spot": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://api.gateio.ws/api/v4/spot/tickers"
        },
        "futures": {
            "enabled": False,
            "update_interval": 3,
            "api_endpoint": "https://fx-api.gateio.ws/api/v4/futures/usdt/tickers"
        },
    },
    "kucoin": {
        "spot": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://api.kucoin.com/api/v1/market/allTickers"
        },
        "futures": {
            "enabled": True,
            "update_interval": 3,
            "api_endpoint": "https://api-futures.kucoin.com/api/v1/contracts/active"
        },
    },
}


def get_market_data_config(exchange: str, market_type: str = "spot") -> Optional[Dict[str, Any]]:
    return MARKET_DATA.get(exchange, {}).get(market_type)
