#!/usr/bin/env python3
"""
Proxy Manager - Smart proxy handling for exchange connections

Supports multiple proxy modes:
1. Failover mode: Switch to proxy only when direct connection fails
2. Load balance mode: Distribute connections across proxies
3. Dynamic proxy health monitoring and rotation
"""

import asyncio
import random
import time
import logging
import httpx
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from src.cex.producer.config import PROXY_CONFIG, PROXY_MODES


class ProxyStatus(Enum):
    HEALTHY = "healthy"
    FAILED = "failed"
    REMOVED = "removed"


@dataclass
class ProxyInfo:
    host: str
    port: int
    protocol: str = 'http'  # Options: 'http', 'socks5'
    username: Optional[str] = None
    password: Optional[str] = None
    exit_ip: Optional[str] = None  # For tracking which IP this proxy exits through
    status: ProxyStatus = ProxyStatus.HEALTHY
    failure_count: int = 0
    last_failure_time: float = 0
    last_success_time: float = 0
    connection_count: int = 0


class ProxyManager:
    """
    Manages proxy connections with failover, load balancing, and health monitoring
    """

    def __init__(self, exchange_name: str, proxy_config: Dict[str, Any], proxy_list: Optional[List[Dict[str, Any]]] = None,
                 worker_id: int = None):
        self.exchange_name = exchange_name
        self.proxy_config = proxy_config
        self.mode = proxy_config.get('mode', 'none')
        self.proxy_list_override = proxy_list  # Optional filtered proxy list
        self.worker_id = worker_id  # Worker ID for distributed proxy offset

        # Setup logging
        self.logger = logging.getLogger(f"proxy_manager_{exchange_name}")

        # Proxy state management
        self.proxies: List[ProxyInfo] = []
        self.current_proxy_index = 0  # Will be offset by worker_id after proxy init
        self.symbol_proxy_mapping: Dict[str, int] = {}  # For sticky sessions
        self.direct_connection_blocked = False
        self.direct_connection_retry_time = 0

        # Statistics
        self.connection_stats = {
            'direct_connections': 0,
            'proxy_connections': 0,
            'failover_switches': 0,
            'proxy_failures': 0
        }

        # Track direct connection usage for load balancing
        self.direct_connection_count = 0

        # Flex mode state management
        self.current_route_index = 0  # Global route pointer for flex mode
        self.flex_routes = []  # Ordered list of routes: ['direct', 'proxy1', 'proxy2']
        self.symbol_route_mapping_flex = {}  # Track which route index each symbol is using

        # Initialize proxies
        self._initialize_proxies()

        # Offset starting proxy index by worker_id to distribute load across workers
        if self.worker_id is not None and len(self.proxies) > 0:
            self.current_proxy_index = self.worker_id % len(self.proxies)
            self.logger.info(f"Worker {self.worker_id}: starting at proxy index {self.current_proxy_index}")

        # Initialize flex routes if flex mode
        if self.mode == 'flex':
            self._initialize_flex_routes()

        self.logger.info(f"Initialized proxy manager for {exchange_name} with mode: {self.mode}")

    def _initialize_proxies(self):
        """Initialize proxy list from configuration or override list"""
        # Use override list if provided (for manual proxy selection)
        proxy_list_source = self.proxy_list_override if self.proxy_list_override is not None else PROXY_CONFIG.get('proxies', [])

        for proxy_config in proxy_list_source:
            proxy = ProxyInfo(
                host=proxy_config['host'],
                port=proxy_config['port'],
                protocol=proxy_config.get('protocol', 'http'),
                username=proxy_config.get('username'),
                password=proxy_config.get('password'),
                exit_ip=proxy_config.get('exit_ip')
            )
            self.proxies.append(proxy)

        if self.proxies:
            proxy_summary = []
            for proxy in self.proxies:
                exit_info = f" -> {proxy.exit_ip}" if proxy.exit_ip else ""
                proxy_summary.append(f"{proxy.protocol}://{proxy.host}:{proxy.port}{exit_info}")
            if self.proxy_list_override is not None:
                self.logger.info(f"Loaded {len(self.proxies)} manually selected proxies: {', '.join(proxy_summary)}")
            else:
                self.logger.info(f"Loaded {len(self.proxies)} proxies: {', '.join(proxy_summary)}")
        else:
            self.logger.warning("No proxies configured")

    def _initialize_flex_routes(self):
        """Initialize flex mode routes from configuration"""
        routes_order = PROXY_MODES['flex'].get('routes_order', ['direct', 'proxy1', 'proxy2'])

        # Build flex_routes list based on what's available
        for route in routes_order:
            if route == 'direct':
                self.flex_routes.append('direct')
            elif route == 'proxy1' and len(self.proxies) >= 1:
                self.flex_routes.append('proxy1')
            elif route == 'proxy2' and len(self.proxies) >= 2:
                self.flex_routes.append('proxy2')

        if not self.flex_routes:
            self.logger.warning("No flex routes configured, defaulting to direct only")
            self.flex_routes = ['direct']

        self.logger.info(f"Flex mode initialized with routes: {self.flex_routes}, starting with: {self.flex_routes[0]}")

    async def get_connection_params(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """
        Get connection parameters based on proxy mode and current state

        Args:
            symbol: Symbol for sticky sessions in load balance mode

        Returns:
            Dict with proxy configuration or None for direct connection
        """
        if self.mode == 'none' or not self.proxies:
            return None

        elif self.mode == 'failover':
            return await self._get_failover_params(symbol)

        elif self.mode == 'load_balance':
            return await self._get_load_balance_params(symbol)

        elif self.mode == 'flex':
            return await self._get_flex_params(symbol)

        else:
            self.logger.warning(f"Unknown proxy mode: {self.mode}")
            return None

    async def _get_failover_params(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """Get connection parameters for failover mode"""
        # Check if direct connection is still blocked
        if self.direct_connection_blocked:
            current_time = time.time()
            retry_after = PROXY_MODES['failover'].get('retry_direct_after', 300)

            if current_time - self.direct_connection_retry_time > retry_after:
                # Time to retry direct connection
                self.direct_connection_blocked = False
                self.logger.info("Retrying direct connection after timeout")
                return None

            # Still blocked, use proxy
            return await self._get_next_available_proxy()

        # Direct connection not blocked, use direct connection
        return None

    async def _get_load_balance_params(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """Get connection parameters for load balance mode"""
        # Check if we should include direct connections in load balancing
        include_direct = PROXY_MODES['load_balance'].get('include_direct', False)

        # If no proxies and direct is not included, return None
        if not self.proxies and not include_direct:
            return None

        # Check for sticky sessions
        if symbol and PROXY_MODES['load_balance'].get('sticky_sessions', True):
            if symbol in self.symbol_proxy_mapping:
                proxy_index = self.symbol_proxy_mapping[symbol]
                # proxy_index can be -1 to represent direct connection
                if proxy_index == -1:
                    # Direct connection is sticky for this symbol
                    return None
                elif 0 <= proxy_index < len(self.proxies):
                    proxy = self.proxies[proxy_index]
                    if proxy.status == ProxyStatus.HEALTHY:
                        return self._build_proxy_params(proxy)

        # Get next proxy/connection based on distribution strategy
        distribution = PROXY_MODES['load_balance'].get('distribution', 'even')

        if distribution == 'even':
            proxy = await self._get_next_proxy_round_robin()
        elif distribution == 'random':
            proxy = await self._get_random_healthy_proxy()
        elif distribution == 'weighted':
            proxy = await self._get_least_used_proxy()
        else:
            proxy = await self._get_next_proxy_round_robin()

        # Remember this mapping for sticky sessions
        if symbol:
            if proxy is None:
                # Direct connection - use -1 as a special marker
                self.symbol_proxy_mapping[symbol] = -1
            else:
                proxy_index = self.proxies.index(proxy)
                self.symbol_proxy_mapping[symbol] = proxy_index

        return self._build_proxy_params(proxy) if proxy else None

    async def _get_flex_params(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """Get connection parameters for flex mode - global route strategy"""
        if not self.flex_routes:
            self.logger.warning("No flex routes configured")
            return None

        # Get current global route
        current_route = self.flex_routes[self.current_route_index]

        # Track which route this symbol is using (for retry on non-403 errors)
        if symbol:
            self.symbol_route_mapping_flex[symbol] = self.current_route_index

        # Return proxy params based on current global route
        if current_route == 'direct':
            self.direct_connection_count += 1
            self.connection_stats['direct_connections'] += 1
            self.logger.debug(f"Flex mode: Using DIRECT connection (global route: {current_route})")
            return None
        elif current_route == 'proxy1' and len(self.proxies) >= 1:
            proxy = self.proxies[0]
            self.connection_stats['proxy_connections'] += 1
            exit_info = f" (exit IP: {proxy.exit_ip})" if proxy.exit_ip else ""
            self.logger.debug(f"Flex mode: Using PROXY1 {proxy.host}:{proxy.port}{exit_info} (global route: {current_route})")
            return self._build_proxy_params(proxy)
        elif current_route == 'proxy2' and len(self.proxies) >= 2:
            proxy = self.proxies[1]
            self.connection_stats['proxy_connections'] += 1
            exit_info = f" (exit IP: {proxy.exit_ip})" if proxy.exit_ip else ""
            self.logger.debug(f"Flex mode: Using PROXY2 {proxy.host}:{proxy.port}{exit_info} (global route: {current_route})")
            return self._build_proxy_params(proxy)
        else:
            # Fallback to direct if route not available
            self.logger.warning(f"Flex route {current_route} not available, using direct")
            return None

    async def _get_next_available_proxy(self) -> Optional[Dict[str, Any]]:
        """Get next available healthy proxy"""
        healthy_proxies = [p for p in self.proxies if p.status == ProxyStatus.HEALTHY]

        if not healthy_proxies:
            self.logger.error("No healthy proxies available")
            return None

        # Try to get the next proxy in rotation
        proxy = healthy_proxies[self.current_proxy_index % len(healthy_proxies)]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(healthy_proxies)

        return self._build_proxy_params(proxy)

    async def _get_next_proxy_round_robin(self) -> Optional[ProxyInfo]:
        """Get next proxy using round-robin strategy"""
        include_direct = PROXY_MODES['load_balance'].get('include_direct', False)
        healthy_proxies = [p for p in self.proxies if p.status == ProxyStatus.HEALTHY]

        if not healthy_proxies and not include_direct:
            return None

        # Build rotation pool: proxies + direct (represented as None)
        rotation_pool = list(healthy_proxies)
        if include_direct:
            rotation_pool.append(None)  # None represents direct connection

        if not rotation_pool:
            return None

        # Get next item from rotation pool
        selected = rotation_pool[self.current_proxy_index % len(rotation_pool)]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(rotation_pool)

        return selected

    async def _get_random_healthy_proxy(self) -> Optional[ProxyInfo]:
        """Get random healthy proxy"""
        include_direct = PROXY_MODES['load_balance'].get('include_direct', False)
        healthy_proxies = [p for p in self.proxies if p.status == ProxyStatus.HEALTHY]

        # Build selection pool: proxies + direct (represented as None)
        selection_pool = list(healthy_proxies)
        if include_direct:
            selection_pool.append(None)  # None represents direct connection

        if not selection_pool:
            return None

        return random.choice(selection_pool)

    async def _get_least_used_proxy(self) -> Optional[ProxyInfo]:
        """Get proxy with least connections (weighted distribution)"""
        include_direct = PROXY_MODES['load_balance'].get('include_direct', False)
        healthy_proxies = [p for p in self.proxies if p.status == ProxyStatus.HEALTHY]

        if not healthy_proxies and not include_direct:
            return None

        # Find minimum usage count among proxies
        min_proxy_count = min([p.connection_count for p in healthy_proxies]) if healthy_proxies else float('inf')

        # Compare with direct connection usage
        if include_direct:
            # If direct connection has fewer or equal connections, use it
            if self.direct_connection_count <= min_proxy_count:
                return None  # None represents direct connection

        # Otherwise, use the least-used proxy
        if healthy_proxies:
            healthy_proxies.sort(key=lambda p: p.connection_count)
            return healthy_proxies[0]

        return None

    def _build_proxy_params(self, proxy: ProxyInfo) -> Dict[str, Any]:
        """Build websockets connection parameters for proxy"""
        if not proxy:
            # None means direct connection - track usage and return None
            self.direct_connection_count += 1
            self.connection_stats['direct_connections'] += 1
            self.logger.info("→ Using DIRECT connection (no proxy)")
            return None

        # Increment connection count
        proxy.connection_count += 1
        self.connection_stats['proxy_connections'] += 1

        exit_info = f" (exit IP: {proxy.exit_ip})" if proxy.exit_ip else ""
        self.logger.info(f"→ Using {proxy.protocol.upper()} proxy: {proxy.host}:{proxy.port}{exit_info}")

        if proxy.protocol == 'socks5':
            # Return SOCKS5 proxy configuration
            return {
                'proxy_type': 'socks5',
                'proxy_host': proxy.host,
                'proxy_port': proxy.port,
                'proxy_username': proxy.username,
                'proxy_password': proxy.password,
                'exit_ip': proxy.exit_ip
            }
        else:
            # HTTP proxy configuration (original logic)
            if proxy.username and proxy.password:
                proxy_url = f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
            else:
                proxy_url = f"http://{proxy.host}:{proxy.port}"

            return {
                'proxy': proxy_url,
                'proxy_basic_auth': (proxy.username, proxy.password) if proxy.username else None
            }

    async def handle_connection_failure(self, error_type: str, proxy_used: Optional[ProxyInfo]):
        """
        Handle connection failure and update proxy/connection strategy

        Args:
            error_type: Type of error that occurred
            proxy_used: Proxy that was used (None for direct connection)
        """
        self.logger.warning(f"Connection failure: {error_type}, proxy_used: {proxy_used is not None}")

        if self.mode == 'failover':
            await self._handle_failover_failure(error_type, proxy_used)
        elif self.mode == 'load_balance':
            await self._handle_load_balance_failure(error_type, proxy_used)
        elif self.mode == 'flex':
            await self._handle_flex_failure(error_type, proxy_used)

    async def _handle_failover_failure(self, error_type: str, proxy_used: Optional[ProxyInfo]):
        """Handle connection failure in failover mode"""
        failover_triggers = PROXY_MODES['failover'].get('triggers', [])

        # Check if this error should trigger proxy failover
        should_failover = any(trigger in error_type.lower() for trigger in failover_triggers)

        if not proxy_used and should_failover:
            # Direct connection failed with trigger error, switch to proxy
            self.direct_connection_blocked = True
            self.direct_connection_retry_time = time.time()
            self.connection_stats['failover_switches'] += 1

            self.logger.warning(f"Direct connection failed ({error_type}), switching to proxy")

        elif proxy_used:
            # Proxy connection failed
            await self._mark_proxy_failed(proxy_used)

    async def _handle_load_balance_failure(self, error_type: str, proxy_used: Optional[ProxyInfo]):
        """Handle connection failure in load balance mode"""
        if proxy_used:
            await self._mark_proxy_failed(proxy_used)
        else:
            # Direct connection failed (if included in load balancing)
            self.logger.debug(f"Direct connection failed: {error_type}")

    async def _send_telegram_notification(self, message: str):
        """Send Telegram notification (non-blocking, for testing purposes only)"""
        bot_token = "7861139807:AAGTxeSWX0d6iVXX9kkp9cL4n1ikY2LJJVo"
        chat_id = "-1007554570"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                await client.post(url, json={
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                })
        except Exception as e:
            self.logger.debug(f"Failed to send Telegram notification: {e}")

    async def _handle_flex_failure(self, error_type: str, proxy_used: Optional[ProxyInfo]):
        """Handle connection failure in flex mode"""
        # Check if this is a 403 error (the only trigger for flex rotation)
        is_403 = '403' in error_type or 'forbidden' in error_type.lower()

        if is_403:
            # TRIGGER: Rotate global route to next in circular list
            old_route = self.flex_routes[self.current_route_index]
            self.current_route_index = (self.current_route_index + 1) % len(self.flex_routes)
            new_route = self.flex_routes[self.current_route_index]

            self.connection_stats['failover_switches'] += 1
            self.logger.warning(f"⚠️  HTTP 403 detected! Rotating ALL connections: {old_route} → {new_route}")
            self.logger.info(f"Flex mode: Global route switched to {new_route} (index {self.current_route_index}/{len(self.flex_routes)-1})")

            # Send Telegram notification
            notification = (
                f"🔄 <b>Flex Mode Rotation</b>\n\n"
                f"Exchange: <code>{self.exchange_name}</code>\n"
                f"Trigger: HTTP 403 Forbidden\n"
                f"Route: <code>{old_route}</code> → <code>{new_route}</code>"
            )
            await self._send_telegram_notification(notification)
        else:
            # NON-TRIGGER: Keep same route, don't rotate
            current_route = self.flex_routes[self.current_route_index]
            self.logger.debug(f"Flex mode: Non-403 error ({error_type}), keeping global route: {current_route}")

    async def _mark_proxy_failed(self, proxy: ProxyInfo):
        """Mark proxy as failed and potentially remove it"""
        proxy.failure_count += 1
        proxy.last_failure_time = time.time()
        self.connection_stats['proxy_failures'] += 1

        max_failures = PROXY_CONFIG.get('max_failures_before_removal', 3)

        if proxy.failure_count >= max_failures:
            proxy.status = ProxyStatus.REMOVED
            self.logger.warning(f"Removed proxy {proxy.host}:{proxy.port} after {proxy.failure_count} failures")

            # Remove symbol mappings for this proxy
            proxy_index = self.proxies.index(proxy)
            symbols_to_remove = [s for s, idx in self.symbol_proxy_mapping.items() if idx == proxy_index]
            for symbol in symbols_to_remove:
                del self.symbol_proxy_mapping[symbol]

        else:
            proxy.status = ProxyStatus.FAILED
            self.logger.warning(f"Marked proxy {proxy.host}:{proxy.port} as failed ({proxy.failure_count}/{max_failures})")

    async def handle_connection_success(self, proxy_used: Optional[ProxyInfo]):
        """Handle successful connection"""
        if proxy_used:
            proxy_used.failure_count = max(0, proxy_used.failure_count - 1)
            proxy_used.last_success_time = time.time()
            proxy_used.status = ProxyStatus.HEALTHY

            self.logger.debug(f"Successful proxy connection: {proxy_used.host}:{proxy_used.port}")
        else:
            self.connection_stats['direct_connections'] += 1
            self.logger.debug("Successful direct connection")

    async def start_health_monitor(self):
        """Start background task to monitor proxy health"""
        health_check_interval = PROXY_CONFIG.get('health_check_interval', 60)

        while True:
            try:
                await self._check_proxy_health()
                await asyncio.sleep(health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in proxy health monitor: {e}")
                await asyncio.sleep(health_check_interval)

    async def _check_proxy_health(self):
        """Check health of failed/removed proxies and potentially restore them"""
        current_time = time.time()
        retry_after = PROXY_CONFIG.get('retry_removed_proxy_after', 300)

        for proxy in self.proxies:
            if proxy.status == ProxyStatus.REMOVED:
                # Check if enough time has passed to retry
                if current_time - proxy.last_failure_time > retry_after:
                    proxy.status = ProxyStatus.HEALTHY
                    proxy.failure_count = 0
                    self.logger.info(f"Restored proxy {proxy.host}:{proxy.port} for retry")

            elif proxy.status == ProxyStatus.FAILED:
                # Reset failed proxies after some time
                if current_time - proxy.last_failure_time > (retry_after // 2):
                    proxy.status = ProxyStatus.HEALTHY
                    proxy.failure_count = max(0, proxy.failure_count - 1)
                    self.logger.debug(f"Reset failed proxy {proxy.host}:{proxy.port}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get proxy usage statistics"""
        healthy_proxies = len([p for p in self.proxies if p.status == ProxyStatus.HEALTHY])
        failed_proxies = len([p for p in self.proxies if p.status == ProxyStatus.FAILED])
        removed_proxies = len([p for p in self.proxies if p.status == ProxyStatus.REMOVED])

        return {
            'mode': self.mode,
            'total_proxies': len(self.proxies),
            'healthy_proxies': healthy_proxies,
            'failed_proxies': failed_proxies,
            'removed_proxies': removed_proxies,
            'direct_connection_blocked': self.direct_connection_blocked,
            'direct_connection_count': self.direct_connection_count,  # Track direct connection usage
            'include_direct': PROXY_MODES.get(self.mode, {}).get('include_direct', False),
            'active_symbol_mappings': len(self.symbol_proxy_mapping),
            'connection_stats': self.connection_stats.copy(),
            'proxy_details': [
                {
                    'host': p.host,
                    'port': p.port,
                    'status': p.status.value,
                    'failure_count': p.failure_count,
                    'connection_count': p.connection_count
                }
                for p in self.proxies
            ]
        }

    def __str__(self):
        stats = self.get_statistics()
        return (f"ProxyManager({self.exchange_name}): mode={stats['mode']}, "
                f"healthy={stats['healthy_proxies']}/{stats['total_proxies']}, "
                f"direct_blocked={stats['direct_connection_blocked']}")