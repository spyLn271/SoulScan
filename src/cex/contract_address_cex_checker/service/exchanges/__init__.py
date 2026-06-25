"""
Exchange fetchers package.
"""
from typing import Dict

from ..config import EXCHANGE_CONFIGS, ExchangeConfig
from .base import BaseExchange


def get_all_exchanges() -> Dict[str, BaseExchange]:
    """Create instances of all configured exchanges."""
    from .binance import BinanceExchange
    from .bybit import BybitExchange
    from .okx import OkxExchange
    from .mexc import MexcExchange
    from .bingx import BingxExchange
    from .coinex import CoinexExchange
    from .kucoin import KucoinExchange
    from .bitget import BitgetExchange
    from .htx import HtxExchange
    from .gateio import GateioExchange
    from .bitmart import BitmartExchange
    from .lbank import LbankExchange

    EXCHANGE_CLASSES = {
        "binance": BinanceExchange,
        "bybit": BybitExchange,
        "okx": OkxExchange,
        "mexc": MexcExchange,
        "bingx": BingxExchange,
        "coinex": CoinexExchange,
        "kucoin": KucoinExchange,
        "bitget": BitgetExchange,
        "htx": HtxExchange,
        "gateio": GateioExchange,
        "bitmart": BitmartExchange,
        "lbank": LbankExchange,
    }

    exchanges = {}
    for name, config in EXCHANGE_CONFIGS.items():
        exchange_class = EXCHANGE_CLASSES.get(name)
        if exchange_class:
            exchanges[name] = exchange_class(config)
    return exchanges
