"""
OSR is needed only for v1 and v2 smart router.
"""

from src.engine.osr.smart_router import SmartRouter, SMART_ROUTER_ERROR_CODES
from src.engine.osr.math_smart_router import MathSmartRouter
from src.engine.osr.online_smart_router import OnlineSmartRouter, OnlineSmartRouterConfigScheme

__all__ = [
    'SmartRouter',
    'MathSmartRouter',
    'SMART_ROUTER_ERROR_CODES',
    'OnlineSmartRouter',
    'OnlineSmartRouterConfigScheme',
]
