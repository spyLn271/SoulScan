#!/usr/bin/env python3
"""
Manual Proxy Configuration Manager

Allows manual selection of which proxies (or direct connection) to use per exchange.
Stores configuration in Redis and applies it to exchange connectors on startup.
"""

import json
import logging
from typing import Dict, List, Optional, Any
import redis.asyncio as redis

logger = logging.getLogger(__name__)


async def get_manual_proxy_config(redis_client: redis.Redis, exchange: str, market: str) -> Optional[Dict[str, Any]]:
    """
    Get manual proxy configuration from Redis for a specific exchange/market

    Args:
        redis_client: Async Redis client
        exchange: Exchange name (e.g., 'bybit', 'okx')
        market: Market type ('spot' or 'futures')

    Returns:
        Dict with 'enabled' and 'selection' keys, or None if not configured
        Example: {'enabled': True, 'selection': ['direct', 'proxy1', 'proxy2']}
    """
    try:
        redis_key = f"manual_proxy:{exchange}:{market}"
        config_json = await redis_client.get(redis_key)

        if not config_json:
            return None

        config = json.loads(config_json)
        logger.debug(f"Loaded manual proxy config for {exchange}_{market}: {config}")
        return config

    except Exception as e:
        logger.error(f"Error loading manual proxy config for {exchange}_{market}: {e}")
        return None


async def set_manual_proxy_config(redis_client: redis.Redis, exchange: str, market: str, selection: List[str]) -> bool:
    """
    Save manual proxy configuration to Redis

    Args:
        redis_client: Async Redis client
        exchange: Exchange name
        market: Market type
        selection: List of selected options, e.g., ['direct', 'proxy1', 'proxy2']
                  Valid values: 'direct', 'proxy1', 'proxy2'

    Returns:
        True if successful, False otherwise
    """
    try:
        if not selection:
            logger.error("Cannot save manual proxy config with empty selection")
            return False

        # Validate selection values
        valid_options = {'direct', 'proxy1', 'proxy2'}
        if not all(opt in valid_options for opt in selection):
            logger.error(f"Invalid proxy options in selection: {selection}")
            return False

        config = {
            'enabled': True,
            'selection': selection
        }

        redis_key = f"manual_proxy:{exchange}:{market}"
        await redis_client.set(redis_key, json.dumps(config))

        logger.info(f"Saved manual proxy config for {exchange}_{market}: {selection}")
        return True

    except Exception as e:
        logger.error(f"Error saving manual proxy config for {exchange}_{market}: {e}")
        return False


async def clear_manual_proxy_config(redis_client: redis.Redis, exchange: str, market: str) -> bool:
    """
    Clear manual proxy configuration from Redis

    Args:
        redis_client: Async Redis client
        exchange: Exchange name
        market: Market type

    Returns:
        True if successful, False otherwise
    """
    try:
        redis_key = f"manual_proxy:{exchange}:{market}"
        await redis_client.delete(redis_key)

        logger.info(f"Cleared manual proxy config for {exchange}_{market}")
        return True

    except Exception as e:
        logger.error(f"Error clearing manual proxy config for {exchange}_{market}: {e}")
        return False


def apply_manual_proxy_to_config(manual_config: Dict[str, Any], exchange_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply manual proxy configuration to exchange configuration

    Modifies the exchange config's proxy settings based on manual selection:
    - Filters PROXY_CONFIG to only include selected proxies
    - Sets appropriate proxy mode (none or load_balance)
    - Sets include_direct flag if direct connection is selected

    Args:
        manual_config: Manual proxy config from Redis
                      Example: {'enabled': True, 'selection': ['direct', 'proxy1']}
        exchange_config: Exchange configuration dict (will be modified in place)

    Returns:
        Modified exchange_config
    """
    if not manual_config or not manual_config.get('enabled'):
        logger.debug("Manual proxy config not enabled, using default config")
        return exchange_config

    selection = manual_config.get('selection', [])
    if not selection:
        logger.warning("Manual proxy config enabled but selection is empty")
        return exchange_config

    logger.info(f"Applying manual proxy config: {selection}")

    # Determine if direct connection is selected
    use_direct = 'direct' in selection
    selected_proxies = [opt for opt in selection if opt != 'direct']

    # Case 1: Only direct connection selected
    if use_direct and not selected_proxies:
        logger.info("Manual config: Direct connection only (no proxies)")
        exchange_config['proxy']['use_proxy'] = False
        exchange_config['proxy']['mode'] = 'none'
        return exchange_config

    # Case 2: Only proxies selected (no direct)
    if selected_proxies and not use_direct:
        exchange_config['proxy']['use_proxy'] = True
        exchange_config['proxy']['mode'] = 'load_balance'

        # Filter PROXY_CONFIG to only include selected proxies
        from src.CEX.producer.config import PROXY_CONFIG
        filtered_proxies = []

        for proxy_id in selected_proxies:
            # Map proxy1, proxy2 to actual proxy configs
            if proxy_id == 'proxy1' and len(PROXY_CONFIG['proxies']) > 0:
                filtered_proxies.append(PROXY_CONFIG['proxies'][0])
            elif proxy_id == 'proxy2' and len(PROXY_CONFIG['proxies']) > 1:
                filtered_proxies.append(PROXY_CONFIG['proxies'][1])

        # Log actual proxy details
        proxy_ips = [f"{p.get('exit_ip', p['host'])}" for p in filtered_proxies]
        logger.info(f"✓ Admin panel: Proxies ONLY (no direct) - Using proxy IPs: {', '.join(proxy_ips)}")

        # Replace PROXY_CONFIG with filtered list
        exchange_config['_filtered_proxy_config'] = filtered_proxies

        # Ensure include_direct is False
        from src.CEX.producer.config import PROXY_MODES
        PROXY_MODES['load_balance']['include_direct'] = False

        return exchange_config

    # Case 3: Mix of direct and proxies
    if use_direct and selected_proxies:
        exchange_config['proxy']['use_proxy'] = True
        exchange_config['proxy']['mode'] = 'load_balance'

        # Filter PROXY_CONFIG to only include selected proxies
        from src.CEX.producer.config import PROXY_CONFIG
        filtered_proxies = []

        for proxy_id in selected_proxies:
            if proxy_id == 'proxy1' and len(PROXY_CONFIG['proxies']) > 0:
                filtered_proxies.append(PROXY_CONFIG['proxies'][0])
            elif proxy_id == 'proxy2' and len(PROXY_CONFIG['proxies']) > 1:
                filtered_proxies.append(PROXY_CONFIG['proxies'][1])

        # Log actual proxy details
        proxy_ips = [f"{p.get('exit_ip', p['host'])}" for p in filtered_proxies]
        logger.info(f"✓ Admin panel: MIXED mode - Direct + Proxy IPs: {', '.join(proxy_ips)}")

        exchange_config['_filtered_proxy_config'] = filtered_proxies

        # Enable include_direct for load balancing
        from src.CEX.producer.config import PROXY_MODES
        PROXY_MODES['load_balance']['include_direct'] = True

        return exchange_config

    logger.warning(f"Unexpected manual proxy config state: {selection}")
    return exchange_config
