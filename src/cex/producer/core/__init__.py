"""
Core infrastructure for the cryptocurrency exchange orderbook monitoring system.

This package contains the base classes and utilities that eliminate code duplication
across exchange implementations and provide common functionality.
"""

from .base_connector import BaseExchangeConnector
from .proxy_manager import ProxyManager, ProxyStatus, ProxyInfo
from .error_reporter import ErrorReporter

__all__ = [
    'BaseExchangeConnector',
    'ProxyManager',
    'ProxyStatus',
    'ProxyInfo',
    'ErrorReporter',
]