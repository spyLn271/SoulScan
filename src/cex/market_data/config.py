#!/usr/bin/env python3
"""
Configuration for Market Data Handlers
"""


from src.settings import cex_config as _sscfg

# Redis connection — host/port sourced from the unified SoulScan config so a
# single source-of-truth governs all services. Auth and DB index remain env-
# overridable for parity with the original handler shipping.
REDIS_CONFIG = {
    'host': _sscfg.REDIS_HOST,
    'port': _sscfg.REDIS_PORT,
    'db': _sscfg.REDIS_DB,
    'password': _sscfg.REDIS_PASSWORD,
    'decode_responses': True,
}

# Exchange Market Data Configuration
MARKET_DATA_CONFIG = {
    'bybit': {
        'enabled': True,
        'spot': {
            'enabled': True,
            'api_endpoint': 'https://api.bybit.com/v5/market/tickers?category=spot',
            'redis_key': 'spot-market-data:bybit',
            'update_interval': 1
        },
        'futures': {
            'enabled': True,
            'api_endpoint': 'https://api.bybit.com/v5/market/tickers?category=linear',
            'redis_key': 'futures-market-data:bybit',
            'update_interval': 1
        }
    },
    'okx': {
        'enabled': True,
        'spot': {
            'enabled': True,
            'api_endpoint': 'https://www.okx.com/api/v5/market/tickers?instType=SPOT',
            'redis_key': 'spot-market-data:okx',
            'update_interval': 1
        },
        'futures': {
            'enabled': True,
            'api_endpoint': 'https://www.okx.com/api/v5/market/tickers?instType=SWAP',
            'redis_key': 'futures-market-data:okx',
            'update_interval': 1
        }
    },
    'bingx': {
        'enabled': True,
        'spot': {
            'enabled': True,
            'api_endpoint': 'https://open-api.bingx.com/openApi/spot/v1/ticker/24hr',
            'redis_key': 'spot-market-data:bingx',
            'update_interval': 1
        },
        'futures': {
            'enabled': True,
            'api_endpoint_premium': 'https://open-api.bingx.com/openApi/swap/v2/quote/premiumIndex',
            'api_endpoint_ticker': 'https://open-api.bingx.com/openApi/swap/v2/quote/ticker',
            'redis_key': 'futures-market-data:bingx',
            'update_interval': 1
        }
    },
    'bitget': {
        'enabled': True,
        'spot': {
            'enabled': True,
            'api_endpoint': 'https://api.bitget.com/api/v2/spot/market/tickers',
            'redis_key': 'spot-market-data:bitget',
            'update_interval': 1
        },
        'futures': {
            'enabled': True,
            'api_endpoint': 'https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES',
            'redis_key': 'futures-market-data:bitget',
            'update_interval': 1
        }
    },
    'bitmart': {
        'enabled': True,
        'spot': {
            'enabled': True,
            'api_endpoint': 'https://api-cloud.bitmart.com/spot/v1/ticker',
            'redis_key': 'spot-market-data:bitmart',
            'update_interval': 3
        },
        'futures': {
            'enabled': True,
            'api_endpoint': 'https://api-cloud-v2.bitmart.com/contract/public/details',
            'redis_key': 'futures-market-data:bitmart',
            'update_interval': 3
        }
    },
    'coinex': {
        'enabled': True,
        'spot': {
            'enabled': True,
            'api_endpoint': 'https://api.coinex.com/v2/spot/ticker',
            'redis_key': 'spot-market-data:coinex',
            'update_interval': 1
        },
        'futures': {
            'enabled': True,
            'api_endpoint': 'https://api.coinex.com/perpetual/v1/market/ticker/all',
            'redis_key': 'futures-market-data:coinex',
            'update_interval': 1
        }
    },
    'htx': {
        'enabled': True,
        'spot': {
            'enabled': True,
            'api_endpoint': 'https://api.huobi.pro/market/tickers',
            'redis_key': 'spot-market-data:htx',
            'update_interval': 1
        },
        'futures': {
            'enabled': True,
            'api_endpoint_ticker': 'https://api.hbdm.com/linear-swap-ex/market/detail/batch_merged',
            'api_endpoint_funding': 'https://api.hbdm.com/linear-swap-api/v1/swap_funding_rate',
            'redis_key': 'futures-market-data:htx',
            'update_interval': 1
        }
    },
    'mexc': {
        'enabled': True,
        'spot': {
            'enabled': True,
            'api_endpoint': 'https://api.mexc.com/api/v3/ticker/24hr',
            'redis_key': 'spot-market-data:mexc',
            'update_interval': 1
        },
        'futures': {
            'enabled': True,
            'api_endpoint_funding': 'https://contract.mexc.com/api/v1/contract/funding_rate',
            'api_endpoint_ticker': 'https://contract.mexc.com/api/v1/contract/ticker',
            'redis_key': 'futures-market-data:mexc',
            'update_interval': 1
        }
    },
    'lbank': {
        'enabled': True,
        'spot': {
            'enabled': True,
            'api_endpoint': 'https://api.lbank.info/v2/ticker.do?symbol=all',
            'redis_key': 'spot-market-data:lbank',
            'update_interval': 1
        }
    },
    'gateio': {
        'enabled': True,
        'spot': {
            'enabled': True,
            'api_endpoint': 'https://api.gateio.ws/api/v4/spot/tickers',
            'redis_key': 'spot-market-data:gateio',
            'update_interval': 1
        },
        'futures': {
            'enabled': True,
            'api_endpoint': 'https://fx-api.gateio.ws/api/v4/futures/usdt/tickers',
            'api_endpoint_contracts': 'https://fx-api.gateio.ws/api/v4/futures/usdt/contracts',
            'redis_key': 'futures-market-data:gateio',
            'update_interval': 1
        }
    },
    'kucoin': {
        'enabled': True,
        'spot': {
            'enabled': True,
            'api_endpoint': 'https://api.kucoin.com/api/v1/market/allTickers',
            'redis_key': 'spot-market-data:kucoin',
            'update_interval': 1
        },
        'futures': {
            'enabled': True,
            'api_endpoint': 'https://api-futures.kucoin.com/api/v1/contracts/active',
            'api_endpoint_tickers': 'https://api-futures.kucoin.com/api/v1/allTickers',
            'redis_key': 'futures-market-data:kucoin',
            'update_interval': 1
        }
    },
    'hyperliquid': {
        'enabled': True,
        'futures': {
            'enabled': True,
            'api_endpoint': 'https://api.hyperliquid.xyz/info',
            'redis_key': 'futures-market-data:hyperliquid',
            'update_interval': 1
        }
    },
    'asterdex': {
        'enabled': True,
        'futures': {
            'enabled': True,
            'api_endpoint_premium': 'https://www.asterdex.com/fapi/v1/premiumIndex?symbols',
            'api_endpoint_ticker': 'https://www.asterdex.com/bapi/future/v1/public/future/aster/ticker/pair',
            'api_endpoint_book': 'https://fapi.asterdex.com/fapi/v1/ticker/bookTicker',
            'redis_key': 'futures-market-data:asterdex',
            'update_interval': 1
        }
    },
    'dydx': {
        'enabled': False,
        'futures': {
            'enabled': True,
            'api_endpoint_markets': 'https://indexer.dydx.trade/v4/perpetualMarkets',
            'api_endpoint_orderbook': 'https://indexer.dydx.trade/v4/orderbooks/perpetualMarket/',
            'redis_key': 'futures-market-data:dydx',
            'update_interval': 1
        }
    },
    'binance': {
        'enabled': True,
        'spot': {
            'enabled': True,
            'api_endpoint': 'https://api.binance.com/api/v3/ticker/24hr',
            'redis_key': 'spot-market-data:binance',
            'update_interval': 3
        },
        'futures': {
            'enabled': True,
            'api_endpoint_24hr': 'https://fapi.binance.com/fapi/v1/ticker/24hr',
            'api_endpoint_premium': 'https://fapi.binance.com/fapi/v1/premiumIndex',
            'api_endpoint_book': 'https://fapi.binance.com/fapi/v1/ticker/bookTicker',
            'redis_key': 'futures-market-data:binance',
            'update_interval': 3
        }
    }
}

def get_enabled_exchanges():
    """Get list of enabled exchanges"""
    return [
        exchange for exchange, config in MARKET_DATA_CONFIG.items()
        if config.get('enabled', False)
    ]

def get_exchange_config(exchange_name):
    """Get configuration for specific exchange"""
    return MARKET_DATA_CONFIG.get(exchange_name)

def get_market_config(exchange_name, market_type):
    """Get configuration for specific exchange and market type"""
    exchange_config = get_exchange_config(exchange_name)
    if not exchange_config:
        return None
    return exchange_config.get(market_type)
