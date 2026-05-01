#!/usr/bin/env python3
"""
WebSocket Client with Native SOCKS5 Proxy Support

This module provides WebSocket connections through SOCKS5 proxies using the native
websockets library support. Much simpler and more reliable than custom implementations!
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import websockets
from websockets.client import WebSocketClientProtocol


logger = logging.getLogger(__name__)


async def connect_with_proxy_config(uri: str, proxy_config: Optional[Dict[str, Any]] = None, **kwargs) -> WebSocketClientProtocol:
    """
    Connect to WebSocket with proxy configuration from proxy manager

    Uses native websockets library support for SOCKS5 proxies when python-socks is installed.
    This is much more reliable than custom socket implementations!

    Args:
        uri: WebSocket URI to connect to
        proxy_config: Proxy configuration dict from ProxyManager
        **kwargs: Additional websocket connection arguments

    Returns:
        WebSocketClientProtocol: Connected WebSocket

    Example proxy_config formats:
        SOCKS5: {
            'proxy_type': 'socks5',
            'proxy_host': '157.180.8.159',
            'proxy_port': 1080,
            'proxy_username': None,
            'proxy_password': None,
            'exit_ip': '157.180.8.162'
        }

        HTTP: {
            'proxy': 'http://proxy:8080',
            'proxy_basic_auth': ('user', 'pass')  # optional
        }
    """

    # Remove proxy-specific kwargs that websockets doesn't understand
    clean_kwargs = {k: v for k, v in kwargs.items()
                   if k not in ['proxy_type', 'proxy_host', 'proxy_port',
                              'proxy_username', 'proxy_password', 'exit_ip']}

    if not proxy_config:
        # No proxy, direct connection
        logger.debug(f"Direct connection to {uri}")
        return await websockets.connect(uri, **clean_kwargs)

    if proxy_config.get('proxy_type') == 'socks5':
        # Build SOCKS5 proxy URL for native websockets support
        proxy_url = _build_socks5_proxy_url(proxy_config)

        logger.debug(f"SOCKS5 connection to {uri} via {proxy_url}")

        # Use native websockets SOCKS5 support - just pass proxy URL!
        return await websockets.connect(uri, proxy=proxy_url, **clean_kwargs)

    elif 'proxy' in proxy_config:
        # HTTP proxy configuration
        proxy_url = proxy_config['proxy']
        proxy_auth = proxy_config.get('proxy_basic_auth')

        logger.debug(f"HTTP proxy connection to {uri} via {proxy_url}")

        connect_kwargs = clean_kwargs.copy()
        connect_kwargs['proxy'] = proxy_url
        if proxy_auth:
            connect_kwargs['proxy_basic_auth'] = proxy_auth

        return await websockets.connect(uri, **connect_kwargs)

    else:
        # Fallback to direct connection if proxy config is invalid
        logger.warning(f"Invalid proxy config, using direct connection: {proxy_config}")
        return await websockets.connect(uri, **clean_kwargs)


def _build_socks5_proxy_url(proxy_config: Dict[str, Any]) -> str:
    """
    Build SOCKS5 proxy URL from proxy configuration

    Args:
        proxy_config: Dictionary with proxy configuration

    Returns:
        str: SOCKS5 proxy URL in format expected by websockets library

    Examples:
        socks5://proxy:1080
        socks5://user:pass@proxy:1080
    """
    host = proxy_config['proxy_host']
    port = proxy_config['proxy_port']
    username = proxy_config.get('proxy_username')
    password = proxy_config.get('proxy_password')

    if username and password:
        # With authentication
        proxy_url = f"socks5://{username}:{password}@{host}:{port}"
    else:
        # Without authentication
        proxy_url = f"socks5://{host}:{port}"

    return proxy_url


async def test_socks5_connection(proxy_host: str, proxy_port: int,
                                proxy_username: Optional[str] = None,
                                proxy_password: Optional[str] = None,
                                test_uri: str = "wss://ws.postman-echo.com/raw") -> bool:
    """
    Test SOCKS5 proxy connectivity with a WebSocket endpoint

    Args:
        proxy_host: SOCKS5 proxy hostname
        proxy_port: SOCKS5 proxy port
        proxy_username: Optional SOCKS5 username
        proxy_password: Optional SOCKS5 password
        test_uri: WebSocket URI to test connection to

    Returns:
        bool: True if connection successful, False otherwise
    """

    # Build proxy config
    proxy_config = {
        'proxy_type': 'socks5',
        'proxy_host': proxy_host,
        'proxy_port': proxy_port,
        'proxy_username': proxy_username,
        'proxy_password': proxy_password
    }

    try:
        # Test connection - connect_with_proxy_config returns a websocket directly
        websocket = await connect_with_proxy_config(test_uri, proxy_config, open_timeout=10)

        try:
            # Send test message
            await websocket.send("SOCKS5 test message")

            # Try to receive response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.info(f"SOCKS5 test successful, received: {response[:50]}...")
                return True
            except asyncio.TimeoutError:
                # Connection works even if no echo response
                logger.info("SOCKS5 test successful (no echo response)")
                return True
        finally:
            # Always close the websocket
            await websocket.close()

    except Exception as e:
        logger.error(f"SOCKS5 test failed: {e}")
        return False


# Legacy function for backwards compatibility
async def connect_socks5(uri: str, proxy_host: str, proxy_port: int,
                        proxy_username: Optional[str] = None,
                        proxy_password: Optional[str] = None,
                        **kwargs) -> WebSocketClientProtocol:
    """
    Legacy function for backwards compatibility

    Use connect_with_proxy_config() instead for new code.
    """
    proxy_config = {
        'proxy_type': 'socks5',
        'proxy_host': proxy_host,
        'proxy_port': proxy_port,
        'proxy_username': proxy_username,
        'proxy_password': proxy_password
    }

    return await connect_with_proxy_config(uri, proxy_config, **kwargs)