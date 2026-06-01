#!/usr/bin/env python3
"""
Centralized Configuration for Cryptocurrency Exchange Orderbook Monitor
Supports plugin architecture with proxy management and per-exchange settings
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import os

from src.settings import config as _sscfg

# --- Symbol Filtering ---
ACCEPTABLE_QUOTE_ASSETS = ['USDT', 'USDC']

# --- Proxy Configuration ---
PROXY_CONFIG = {
    'proxies': [
        # SOCKS5 proxies with different exit IPs
        {'host': '157.180.8.159', 'port': 1080, 'protocol': 'socks5', 'username': None, 'password': None, 'exit_ip': '157.180.8.162'},
        {'host': '157.180.8.159', 'port': 1081, 'protocol': 'socks5', 'username': None, 'password': None, 'exit_ip': '157.180.8.163'},
        # Add more proxies here as needed
    ],
    'rotation_strategy': 'round_robin',  # Options: 'round_robin', 'random', 'least_used'
    'health_check_interval': 60,  # Check proxy health every 60 seconds
    'max_failures_before_removal': 3,  # Remove proxy after 3 consecutive failures
    'retry_removed_proxy_after': 300,  # Retry removed proxy after 5 minutes
    'connection_timeout': 10,  # Proxy connection timeout in seconds
}

# --- Proxy Mode Definitions ---
PROXY_MODES = {
    'none': {
        'description': 'No proxy usage - direct connections only',
        'enabled': False
    },
    'failover': {
        'description': 'Switch to proxy only when direct connection fails',
        'enabled': True,
        'triggers': [
            'connection_closed',  # WebSocket connection closed unexpectedly
            'http_403',          # HTTP 403 Forbidden
            'http_429',          # HTTP 429 Rate Limited
            'rate_limit',        # Exchange-specific rate limiting
            'ip_blocked',        # IP address blocked
            'dns_error'          # DNS resolution failures
        ],
        'retry_direct_after': 300,  # Try direct connection again after 5 minutes
        'max_proxy_failures': 3,    # Switch to next proxy after 3 failures
    },
    'load_balance': {
        'description': 'Distribute connections evenly across all proxies',
        'enabled': True,
        'distribution': 'even',     # Options: 'even', 'weighted', 'random'
        'sticky_sessions': True,    # Keep symbol on same proxy for session
        'failover_on_error': True,  # Failover to next proxy on errors
        'include_direct': True,     # Include direct connection in load balancing
    },
    'flex': {
        'description': 'Global route rotation - switch all connections to next route on HTTP 403 only',
        'enabled': True,
        'trigger': 'http_403',      # Only HTTP 403 triggers global rotation
        'routes_order': ['direct', 'proxy1', 'proxy2'],  # Ordered route list (circular)
    }
}

# --- Exchange Configurations ---
EXCHANGES = {
    'bybit': {
        'enabled': True,
        'name': 'Bybit',
        'spot': {
            'enabled': True,
            'ws_url': 'wss://ws2.bybit.com/spot/ws/quote/v2',
            'connection_type': 'individual',  # Each symbol gets its own connection
            'symbols_per_connection': 1,
            'ping_interval': 20,
            'reconnect_delay_base': 1.0,
            'reconnect_delay_max': 60,
            'workers': 2,  # Number of worker processes for distributed mode
            'special_params': {
                'dumpScale': True,  # Bybit-specific DumpScale parameter
                'dumpScale_retry_range': list(range(24, -1, -1)),
                'binary': False,
                'limit': 40
            }
        },
        'futures': {
            'enabled': False,  # Disabled - spot only for now
            'ws_url': 'wss://stream.bybit.com/v5/public/linear',
            'connection_type': 'individual',
            'symbols_per_connection': 1,
            'ping_interval': 15,
            'reconnect_delay_base': 1.0,
            'reconnect_delay_max': 60
        },
        'proxy': {
            'use_proxy': True,
            'mode': 'flex',  # Switch to SOCKS5 proxy on connection errors
            'priority': 'direct_first',  # Try direct connection first
        },
        'rate_limits': {
            'connections_per_second': 10,
            'subscriptions_per_second': 20
        }
    },

    'okx': {
        'enabled': True,
        'name': 'OKX',
        'spot': {
            'enabled': True,
            'ws_url': 'wss://wspri.okx.com:8443/ws/v5/ipublic',
            'connection_type': 'batched',  # Multiple symbols per connection
            'symbols_per_connection': 20,  # OKX allows up to 20 topics per connection
            'ping_interval': 20,
            'reconnect_delay_base': 2.0,
            'reconnect_delay_max': 60,
            'workers': 2,  # Number of worker processes for distributed mode
            'special_params': {
                'channel': 'books5',  # OKX book depth channel
                'instType': 'SPOT'
            }
        },
        'futures': {
            'enabled': False,  # Only metadata fetcher for now
        },
        'proxy': {
            'use_proxy': False,
            'mode': 'none',
        },
        'rate_limits': {
            'connections_per_second': 5,
            'subscriptions_per_second': 10
        }
    },

    'kucoin': {
        'enabled': True,
        'name': 'KuCoin',
        'spot': {
            'enabled': True,
            'bullet_url': 'https://www.kucoin.com/_api/bullet-usercenter/v1/bullet-public',
            'connection_type': 'batched',
            'symbols_per_connection': 50,  # KuCoin can handle more symbols per connection
            'ping_interval': None,
            'reconnect_delay_base': 1.0,
            'reconnect_delay_max': 60,
            'special_params': {
                'uses_bullet_api': True,  # KuCoin requires bullet API for WebSocket endpoints
                'connect_id': 'connect_welcome',
                'topic_prefix': '/market/level2'
            }
        },
        'futures': {
            'enabled': False,  # Disabled - spot only for now
            'bullet_url': 'https://www.kucoin.com/_api/bullet-usercenter/v1/bullet-public',
            'connection_type': 'batched',
            'symbols_per_connection': 50,
        },
        'proxy': {
            'use_proxy': True,
            'mode': 'load_balance',  # Distribute load across SOCKS5 proxies
        },
        'rate_limits': {
            'connections_per_second': 5,
            'subscriptions_per_second': 15
        }
    },

    'mexc': {
        'enabled': True,
        'name': 'MEXC',
        'spot': {
            'enabled': True,
            'ws_url': 'wss://wbs-api.mexc.com/ws',
            'connection_type': 'batched',
            'symbols_per_connection': 30,  # MEXC official recommendation for stability
            'ping_interval': 25,
            'reconnect_delay_base': 5.0,
            'reconnect_delay_max': 60,
            'workers': 8,  # Number of worker processes for distributed mode
            'special_params': {
                'uses_protobuf': True,  # MEXC uses protobuf for data
                'depth_level': 20,
                'ping_method': {'method': 'PING'}
            }
        },
        'proxy': {
            'use_proxy': True,
            'mode': 'failover',  # SOCKS5 proxy on connection issues
        },
        'rate_limits': {
            'connections_per_second': 3,
            'subscriptions_per_second': 10
        }
    },

    'gateio': {
        'enabled': True,
        'name': 'Gate.io',
        'spot': {
            'enabled': True,
            'ws_url': 'wss://spot-webws.wsbridge.com/v3?device_type=0',
            'connection_type': 'individual',  # New endpoint allows 1 symbol per connection
            'symbols_per_connection': 1,
            'ping_interval': 25,
            'reconnect_delay_base': 2.0,
            'reconnect_delay_max': 60,
            'workers': 8,  # Number of worker processes for distributed mode
        },
        'proxy': {
            'use_proxy': False,  # Disabled - new endpoint works better with direct connection
            'mode': 'none',
        }
    },

    'bingx': {
        'enabled': True,
        'name': 'BingX',
        'spot': {
            'enabled': True,
            'ws_url': 'wss://open-api-ws.bingx.com/market',
            'connection_type': 'batched',
            'symbols_per_connection': 20,
            'ping_interval': 25,
            'reconnect_delay_base': 2.0,
            'reconnect_delay_max': 60,
            'workers': 4,  # Number of worker processes for distributed mode
        },
        'proxy': {
            'use_proxy': True,
            'mode': 'failover',  # SOCKS5 proxy on connection issues
        }
    },

    'bitget': {
        'enabled': True,
        'name': 'Bitget',
        'spot': {
            'enabled': True,
            'ws_url': 'wss://stream.bitget.com/public/v1/stream?compress=true&terminalType=1',
            'connection_type': 'batched',
            'symbols_per_connection': 20,
            'ping_interval': 15,
            'reconnect_delay_base': 2.0,
            'reconnect_delay_max': 60,
            'workers': 2,  # Number of worker processes for distributed mode
        },
        'proxy': {
            'use_proxy': False,
            'mode': 'none',
        }
    },

    'bitmart': {
        'enabled': True,
        'name': 'BitMart',
        'spot': {
            'enabled': True,
            'ws_url': 'wss://ws-manager-compress.bitmart.com/api?protocol=1.1',
            'connection_type': 'batched',
            'symbols_per_connection': 25,
            'ping_interval': 15,
            'reconnect_delay_base': 2.0,
            'reconnect_delay_max': 60,
            'workers': 4,  # Number of worker processes for distributed mode
            'initial_connection_delay': 0.2,  # Seconds between connections globally (across all workers)
        },
        'proxy': {
            'use_proxy': True,
            'mode': 'load_balance',
        }
    },

    'coinex': {
        'enabled': True,
        'name': 'CoinEx',
        'spot': {
            'enabled': True,
            'ws_url': 'wss://socket.coinex.com/v2/spot/',
            'connection_type': 'batched',
            'symbols_per_connection': 20,
            'ping_interval': 25,
            'reconnect_delay_base': 2.0,
            'reconnect_delay_max': 60,
            'workers': 6,  # Number of worker processes for distributed mode
            'special_params': {
                'uses_class_pattern': True,  # CoinEx uses class-based architecture
            }
        },
        'proxy': {
            'use_proxy': False,
            'mode': 'none',
        }
    },

    'htx': {
        'enabled': True,
        'name': 'HTX (Huobi)',
        'spot': {
            'enabled': True,
            'ws_url': 'wss://api.huobi.pro/ws',
            'connection_type': 'batched',
            'symbols_per_connection': 20,
            'ping_interval': None,
            'reconnect_delay_base': 2.0,
            'reconnect_delay_max': 60,
            'workers': 2,  # Number of worker processes for distributed mode
            'special_params': {
                'uses_gzip': True,  # HTX uses gzip compression
            }
        },
        'proxy': {
            'use_proxy': False,
            'mode': 'none',
        }
    },

    'lbank': {
        'enabled': True,
        'name': 'LBank',
        'spot': {
            'enabled': True,
            'ws_url': 'wss://www.lbkex.net/ws/V2/',
            'connection_type': 'batched',
            'symbols_per_connection': 20,
            'ping_interval': None,
            'reconnect_delay_base': 2.0,
            'reconnect_delay_max': 60,
            'workers': 2,  # Number of worker processes for distributed mode
        },
        'proxy': {
            'use_proxy': False,
            'mode': 'none',
        }
    },

    'hyperliquid': {
        'enabled': False,  # Disabled by default
        'name': 'Hyperliquid',
        'futures': {
            'enabled': False,
            'ws_url': 'wss://api.hyperliquid.xyz/ws',
            'connection_type': 'individual',
            'symbols_per_connection': 1,
        },
        'proxy': {
            'use_proxy': False,
            'mode': 'none',
        }
    }
}

# --- Stream Configuration ---
STREAM_CONFIG = {
    'key_template': 'stream:orderbook:{exchange}:{market_type}:{symbol}',
    'maxlen': 10000,  # Keep last 10k orderbook updates per symbol
    'error_queue_template': 'watchdog:{exchange}:error_queue',
    'active_symbols_template': 'symbols_status:{exchange}:{market_type}:active_symbols',
    'inactive_symbols_template': 'symbols_status:{exchange}:{market_type}:inactive_symbols',
    'market_data_template': '{market_type}-market-data:{exchange}',
    'log_stream_template': 'logs:{exchange}:{market_type}',  # Log stream for web panel
    'log_stream_maxlen': 1000,  # Keep last 1000 log entries per exchange
    'error_queue_max_size_bytes': 500 * 1024 * 1024,  # 500MB - rotate queue when exceeded
    'error_archive_dir': './error_archive',  # Directory for archived error logs
    'schema_version': 1,  # Bumped only on a breaking stream-payload change (additive field)
    'orderbook_maxlen': 10,  # Stream trim: keep last N entries per symbol (consumers read latest)
    'health_prefix': 'health',  # health:{exchange}:{market_type}:{worker_id}
    'backpressure_max_streams': 5000,  # Max distinct streams buffered during a Redis outage
}

# --- Monitoring Configuration ---
MONITORING_CONFIG = {
    'health_check_interval': 30,  # Check exchange health every 30 seconds
    'error_threshold': 5,  # Report to watchdog after 5 consecutive errors
    'symbol_refresh_interval': 300,  # Refresh symbol list every 5 minutes
    'connection_timeout': 30,  # WebSocket connection timeout
    'response_timeout': 10,  # WebSocket response timeout
    'max_reconnection_attempts': -1,  # Unlimited reconnection attempts
    'stale_stream_timeout': 60,  # Reconnect if no orderbook data for 60 seconds
    'max_consecutive_parse_errors': 10,  # Reconnect after this many back-to-back parse errors
    'recv_poll_timeout': 10,  # Per-recv timeout so staleness is checked periodically (s)
    'heartbeat_interval': 15,  # How often a worker writes its health heartbeat (s)
    'heartbeat_ttl': 60,  # TTL on the heartbeat key (s); supervisor treats expiry as hung
    'hung_worker_timeout': 120,  # Supervisor: alive worker, no heartbeat/progress this long => restart
}

# --- Utility Functions ---
def get_exchange_config(exchange_name: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific exchange"""
    return EXCHANGES.get(exchange_name.lower())

def get_enabled_exchanges() -> List[str]:
    """Get list of enabled exchanges"""
    return [name for name, config in EXCHANGES.items() if config.get('enabled', False)]

def get_proxy_enabled_exchanges() -> List[str]:
    """Get list of exchanges with proxy enabled"""
    return [name for name, config in EXCHANGES.items()
            if config.get('enabled', False) and config.get('proxy', {}).get('use_proxy', False)]

def validate_proxy_mode(mode: str) -> bool:
    """Validate proxy mode"""
    return mode in PROXY_MODES

def get_redis_config() -> Dict[str, Any]:
    """Redis connection kwargs, sourced from the unified SoulScan config."""
    return {
        'host': _sscfg.REDIS_HOST,
        'port': _sscfg.REDIS_PORT,
        'db': int(os.getenv('REDIS_DB', 0)),
        'password': os.getenv('REDIS_PASSWORD'),
        'decode_responses': True,
    }

def get_stream_key(exchange: str, market_type: str, symbol: str) -> str:
    """Generate Redis stream key for orderbook data"""
    return STREAM_CONFIG['key_template'].format(
        exchange=exchange.lower(),
        market_type=market_type.lower(),
        symbol=symbol.upper()
    )

def get_heartbeat_key(exchange: str, market_type: str, worker_id) -> str:
    """Health heartbeat key for one worker (additive observability keyspace)."""
    wid = 'none' if worker_id is None else worker_id
    prefix = STREAM_CONFIG.get('health_prefix', 'health')
    return f"{prefix}:{exchange}:{market_type}:{wid}"


def get_error_queue_key(exchange: str) -> str:
    """Generate Redis error queue key"""
    return STREAM_CONFIG['error_queue_template'].format(exchange=exchange.lower())

def get_active_symbols_key(exchange: str, market_type: str) -> str:
    """Generate Redis active symbols key"""
    return STREAM_CONFIG['active_symbols_template'].format(
        exchange=exchange.lower(),
        market_type=market_type.lower()
    )

def get_inactive_symbols_key(exchange: str, market_type: str) -> str:
    """Generate Redis inactive symbols key"""
    return STREAM_CONFIG['inactive_symbols_template'].format(
        exchange=exchange.lower(),
        market_type=market_type.lower()
    )

def get_log_stream_key(exchange: str, market_type: str) -> str:
    """Generate Redis log stream key"""
    return STREAM_CONFIG['log_stream_template'].format(
        exchange=exchange.lower(),
        market_type=market_type.lower()
    )

def get_manual_proxy_key(exchange: str, market_type: str) -> str:
    """Generate Redis manual proxy configuration key"""
    return f"manual_proxy:{exchange.lower()}:{market_type.lower()}"

# --- Configuration Validation ---
def validate_config():
    """Validate configuration settings"""
    errors = []

    # Validate exchanges
    for exchange_name, config in EXCHANGES.items():
        if config.get('enabled', False):
            # Check required fields
            if 'name' not in config:
                errors.append(f"Exchange {exchange_name}: missing 'name' field")

            # Check proxy configuration
            proxy_config = config.get('proxy', {})
            if proxy_config.get('use_proxy', False):
                mode = proxy_config.get('mode', 'none')
                if not validate_proxy_mode(mode):
                    errors.append(f"Exchange {exchange_name}: invalid proxy mode '{mode}'")

    # Validate proxy configuration
    if PROXY_CONFIG['proxies'] and any(ex['proxy']['use_proxy'] for ex in EXCHANGES.values() if ex.get('enabled')):
        for i, proxy in enumerate(PROXY_CONFIG['proxies']):
            if 'host' not in proxy or 'port' not in proxy:
                errors.append(f"Proxy {i}: missing 'host' or 'port'")

    if errors:
        raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))

    return True

# Validate configuration on import
validate_config()
