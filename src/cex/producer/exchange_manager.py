#!/usr/bin/env python3
"""
Exchange Manager - Dynamic plugin loader and manager

Dynamically loads and manages exchange plugins based on configuration.
Demonstrates the plugin architecture in action.
"""

import sys
import os

import asyncio
import logging
import signal
import importlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.cex.producer.config import get_enabled_exchanges, get_exchange_config, EXCHANGES


@dataclass
class ExchangePlugin:
    """Container for exchange plugin information"""
    name: str
    connector: Any
    config: Dict[str, Any]
    task: Optional[asyncio.Task] = None


class ExchangeManager:
    """
    Manages all exchange plugins dynamically based on configuration
    """

    def __init__(self):
        self.plugins: Dict[str, ExchangePlugin] = {}
        self.shutdown_event = asyncio.Event()
        self.logger = logging.getLogger("exchange_manager")

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()

    async def discover_and_load_plugins(self):
        """Discover and load enabled exchange plugins"""
        enabled_exchanges = get_enabled_exchanges()
        self.logger.info(f"Discovering plugins for exchanges: {enabled_exchanges}")

        for exchange_name in enabled_exchanges:
            try:
                await self._load_exchange_plugin(exchange_name)
            except Exception as e:
                self.logger.error(f"Failed to load {exchange_name} plugin: {e}")

        self.logger.info(f"Successfully loaded {len(self.plugins)} exchange plugins")

    async def _load_exchange_plugin(self, exchange_name: str):
        """Load a specific exchange plugin"""
        from src.cex.producer.core.logging_setup import setup_exchange_logger

        config = get_exchange_config(exchange_name)
        if not config:
            raise ValueError(f"No configuration found for {exchange_name}")

        module_name = f"src.cex.producer.plugins.{exchange_name}_plugin"

        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            self.logger.warning(f"Plugin module {module_name} not found: {e}")
            return

        for market_type in ['spot', 'futures']:
            if not config.get(market_type, {}).get('enabled', False):
                continue
            class_name = f"{exchange_name.title()}{market_type.title()}Connector"
            connector_class = getattr(module, class_name, None)
            if not connector_class:
                continue

            setup_exchange_logger(exchange_name, market_type, file_level='INFO')
            connector = connector_class()
            plugin = ExchangePlugin(
                name=f"{exchange_name}_{market_type}",
                connector=connector,
                config=config,
            )
            self.plugins[f"{exchange_name}_{market_type}"] = plugin
            self.logger.info(f"Loaded {exchange_name} {market_type} plugin")

        if not any(self.plugins.get(f"{exchange_name}_{mt}") for mt in ['spot', 'futures']):
            raise ValueError(f"No connector classes found for {exchange_name}")

    async def start_all_plugins(self):
        """Start all loaded plugins"""
        self.logger.info(f"Starting {len(self.plugins)} exchange plugins...")

        for plugin_name, plugin in self.plugins.items():
            try:
                self.logger.info(f"Starting {plugin_name}...")
                task = asyncio.create_task(
                    self._run_plugin_with_restart(plugin),
                    name=plugin_name
                )
                plugin.task = task

                # Small delay between starts to avoid overwhelming connections
                await asyncio.sleep(1)

            except Exception as e:
                self.logger.error(f"Failed to start {plugin_name}: {e}")

        self.logger.info("All plugins started successfully")

    async def _run_plugin_with_restart(self, plugin: ExchangePlugin):
        """Run plugin with automatic restart on failure"""
        restart_count = 0
        max_restarts = 5
        restart_delay = 30

        while not self.shutdown_event.is_set() and restart_count < max_restarts:
            try:
                self.logger.info(f"Running {plugin.name} (restart #{restart_count})")
                await plugin.connector.start()

                # If we get here, the plugin exited normally
                break

            except Exception as e:
                restart_count += 1
                self.logger.error(f"{plugin.name} failed (attempt {restart_count}/{max_restarts}): {e}")

                if restart_count < max_restarts and not self.shutdown_event.is_set():
                    self.logger.info(f"Restarting {plugin.name} in {restart_delay} seconds...")
                    await asyncio.sleep(restart_delay)
                else:
                    self.logger.error(f"{plugin.name} exceeded max restarts, giving up")
                    break

    async def stop_all_plugins(self):
        """Stop all running plugins"""
        self.logger.info("Stopping all exchange plugins...")

        # Set shutdown event for all plugins
        self.shutdown_event.set()

        # Cancel all tasks
        for plugin_name, plugin in self.plugins.items():
            if plugin.task and not plugin.task.done():
                self.logger.info(f"Stopping {plugin_name}...")
                plugin.task.cancel()

        # Wait for all tasks to complete
        tasks = [plugin.task for plugin in self.plugins.values() if plugin.task]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Cleanup connectors
        for plugin in self.plugins.values():
            try:
                await plugin.connector.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up {plugin.name}: {e}")

        # Close shared Redis connection pool
        try:
            from src.cex.producer.core.redis_manager import RedisManager
            await RedisManager.close_pool()
            self.logger.info("Closed shared Redis connection pool")
        except Exception as e:
            self.logger.error(f"Error closing Redis pool: {e}")

        self.logger.info("All plugins stopped successfully")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics from all running plugins"""
        stats = {
            "total_plugins": len(self.plugins),
            "running_plugins": 0,
            "plugins": {}
        }

        for plugin_name, plugin in self.plugins.items():
            plugin_stats = {
                "name": plugin_name,
                "running": plugin.task and not plugin.task.done(),
                "config": {
                    "connection_type": plugin.connector.connection_type,
                    "symbols_per_connection": plugin.connector.symbols_per_connection,
                    "proxy_enabled": plugin.config.get('proxy', {}).get('use_proxy', False),
                    "proxy_mode": plugin.config.get('proxy', {}).get('mode', 'none')
                }
            }

            if plugin_stats["running"]:
                stats["running_plugins"] += 1

            # Get proxy statistics if available
            if hasattr(plugin.connector, '_proxy_manager') and plugin.connector._proxy_manager:
                plugin_stats["proxy_stats"] = plugin.connector._proxy_manager.get_statistics()

            stats["plugins"][plugin_name] = plugin_stats

        return stats

    async def run(self):
        """Main run method"""
        try:
            self.logger.info("Starting Exchange Manager...")

            await self.discover_and_load_plugins()

            if not self.plugins:
                self.logger.warning("No plugins loaded, exiting...")
                return

            # Start all plugins
            await self.start_all_plugins()

            # Wait for shutdown signal
            await self.shutdown_event.wait()

        except Exception as e:
            self.logger.error(f"Error in exchange manager: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.stop_all_plugins()


async def main():
    """Dev-only standalone launcher. Production startup goes through CEXSupervisor."""
    from src.cex.producer.core.logging_setup import setup_manager_logger
    manager_logger = setup_manager_logger('exchange_manager', file_level='INFO')
    manager_logger.info(f"Configured exchanges: {len(EXCHANGES)} | Enabled: {get_enabled_exchanges()}")
    manager = ExchangeManager()
    await manager.run()


if __name__ == "__main__":
    asyncio.run(main())