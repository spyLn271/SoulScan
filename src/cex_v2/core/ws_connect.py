#!/usr/bin/env python3
"""
WebSocket connect with optional SOCKS5 proxy (carried over from the proven legacy helper, trimmed
to the one entry point we use). websockets 12.0 has no native proxy= (that's 15.0+), so for SOCKS5
we open the tunnel with python_socks and hand the connected socket to websockets via sock=.
proxy_config=None -> direct connection (used by binance and other direct exchanges).
"""
import logging
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

import websockets
from websockets.client import WebSocketClientProtocol
from python_socks.async_.asyncio import Proxy
from python_socks import ProxyType

logger = logging.getLogger(__name__)


def _parse_ws_target(uri: str) -> Tuple[str, int, str]:
    p = urlparse(uri)
    scheme = p.scheme.lower()
    return p.hostname, p.port or (443 if scheme == "wss" else 80), scheme


async def connect_with_proxy_config(uri: str, proxy_config: Optional[Dict[str, Any]] = None,
                                    **kwargs) -> WebSocketClientProtocol:
    """Connect to `uri`. If proxy_config is a SOCKS5 dict, tunnel through it; else direct."""
    clean = {k: v for k, v in kwargs.items()
             if k not in ("proxy_type", "proxy_host", "proxy_port",
                          "proxy_username", "proxy_password", "exit_ip")}

    if not proxy_config:
        return await websockets.connect(uri, **clean)

    if proxy_config.get("proxy_type") == "socks5":
        host, port, scheme = _parse_ws_target(uri)
        proxy = Proxy.create(
            proxy_type=ProxyType.SOCKS5,
            host=proxy_config["proxy_host"], port=int(proxy_config["proxy_port"]),
            username=proxy_config.get("proxy_username"), password=proxy_config.get("proxy_password"),
        )
        sock = await proxy.connect(dest_host=host, dest_port=port,
                                   timeout=clean.get("open_timeout", 30) or 30)
        sock_kwargs = dict(clean, sock=sock)
        if scheme == "wss":
            sock_kwargs.setdefault("server_hostname", host)
        return await websockets.connect(uri, **sock_kwargs)

    logger.warning("Unsupported proxy config, using direct: %s", proxy_config)
    return await websockets.connect(uri, **clean)
