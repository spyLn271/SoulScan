"""Plugin contract tests after the _handle_messages unification."""
import asyncio
import importlib
import glob
import os
import re
import pytest

from src.cex.producer.core.base_connector import BaseExchangeConnector

PLUGINS = [
    ("bybit", "BybitSpotConnector", False),
    ("bitget", "BitgetSpotConnector", False),
    ("coinex", "CoinexSpotConnector", False),
    ("okx", "OkxSpotConnector", False),
    ("mexc", "MexcSpotConnector", True),
    ("bitmart", "BitmartSpotConnector", False),  # parse_message(self, raw_message) — no symbols param
    ("gateio", "GateioSpotConnector", True),
    ("htx", "HtxSpotConnector", True),
]


@pytest.mark.parametrize("mod,cls,expected", PLUGINS)
def test_parse_takes_symbols_flag(mod, cls, expected):
    m = importlib.import_module(f"src.cex.producer.plugins.{mod}_plugin")
    inst = getattr(m, cls)()
    assert inst._parse_takes_symbols is expected


def test_overriders_are_known_set():
    """Only plugins with genuinely exchange-specific ping/pong keep a bespoke
    _handle_messages; everyone else uses the hardened base loop."""
    root = os.path.dirname(importlib.import_module("src.cex.producer.plugins").__file__)
    overriders = set()
    for path in glob.glob(os.path.join(root, "*_plugin.py")):
        if re.search(r"async def _handle_messages", open(path).read()):
            overriders.add(os.path.basename(path).replace("_plugin.py", ""))
    assert overriders == {"bingx", "lbank", "htx"}, f"unexpected: {sorted(overriders)}"


class _SymbolRecorder(BaseExchangeConnector):
    def __init__(self):
        super().__init__("okx", "spot")
        self.received_symbols = "UNSET"

    async def get_websocket_url(self, symbol=None):
        return "wss://example.invalid"

    async def subscribe_to_symbols(self, websocket, symbols):
        return None

    async def parse_message(self, message, symbols=None):
        self.received_symbols = symbols
        raise asyncio.CancelledError()


async def test_base_loop_passes_symbols_when_supported(fake_redis):
    c = _SymbolRecorder()
    c.redis_client = fake_redis
    c.stale_stream_timeout = 0

    class _WS:
        async def recv(self):
            return "DATA"

    with pytest.raises(asyncio.CancelledError):
        await c._handle_messages(_WS(), ["BTCUSDT", "ETHUSDT"])
    assert c.received_symbols == ["BTCUSDT", "ETHUSDT"]
