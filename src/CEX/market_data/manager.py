#!/usr/bin/env python3
"""
Market Data Manager - Dynamic plugin loader and manager for market data handlers

Dynamically loads and manages market data handler plugins based on configuration.
Demonstrates the market data plugin architecture in action.
"""

# Fix Python path for imports
import sys
import os

import asyncio
import logging
import signal
import importlib
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.CEX.market_data.config import get_enabled_exchanges, get_exchange_config, MARKET_DATA_CONFIG
from src.LoggerHandler.logger import get_logger


@dataclass
class MarketDataPlugin:
    """Container for market data plugin information"""
    name: str
    handler: Any
    config: Dict[str, Any]
    thread: Optional[threading.Thread] = None


class MarketDataManager:
    """
    Manages all market data handler plugins dynamically based on configuration
    """

    def __init__(self):
        self.plugins: Dict[str, MarketDataPlugin] = {}
        self.shutdown_event = asyncio.Event()
        self.logger = get_logger("CEX-MarketData-Manager")

        # Signal handlers are installed by the supervisor wrapper. When run
        # standalone (run.py), install them here too — but only if we're on
        # the main thread (signal.signal raises ValueError otherwise).
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()

    async def load_plugins(self):
        """Dynamically load market data handler plugins based on configuration"""
        enabled_exchanges = get_enabled_exchanges()

        if not enabled_exchanges:
            self.logger.warning("No exchanges enabled in configuration")
            return

        self.logger.info(f"Loading plugins for {len(enabled_exchanges)} exchanges: {enabled_exchanges}")

        for exchange in enabled_exchanges:
            config = get_exchange_config(exchange)
            if not config:
                self.logger.warning(f"No configuration found for {exchange}")
                continue

            # Load enabled market types for this exchange
            for market_type in ['spot', 'futures']:
                market_config = config.get(market_type)
                if not market_config or not market_config.get('enabled', False):
                    continue

                try:
                    plugin_name = f"{exchange}_{market_type}"
                    handler = await self._load_handler_plugin(exchange, market_type)

                    if handler:
                        plugin = MarketDataPlugin(
                            name=plugin_name,
                            handler=handler,
                            config=market_config
                        )
                        self.plugins[plugin_name] = plugin
                        self.logger.info(f"✅ Loaded {plugin_name} handler")

                except Exception as e:
                    self.logger.error(f"❌ Failed to load {exchange} {market_type} handler: {e}")

        self.logger.info(f"Successfully loaded {len(self.plugins)} market data handler plugins")

    async def _load_handler_plugin(self, exchange: str, market_type: str):
        """Load a specific market data handler plugin"""
        try:
            # Import the handler module from the appropriate plugin folder (spot or futures)
            module_name = f"src.CEX.market_data.plugins_{market_type}.{exchange}_handler"
            module = importlib.import_module(module_name)

            # Get the handler class name with special cases for acronyms and multi-word names
            exchange_name_map = {
                'htx': 'HTX',
                'mexc': 'MEXC',
                'okx': 'Okx',
                'lbank': 'LBank',
                'gateio': 'Gateio',
                'coinex': 'CoinEx',
                'bitmart': 'BitMart'
            }
            exchange_title = exchange_name_map.get(exchange, exchange.title())
            class_name = f"{exchange_title}{market_type.title()}Handler"
            handler_class = getattr(module, class_name)

            # Create handler instance
            handler = handler_class()

            # Initialize Redis connection
            success = handler.initialize()
            if not success:
                self.logger.error(f"Failed to initialize Redis connection for {exchange} {market_type}")
                return None

            return handler

        except ImportError as e:
            self.logger.error(f"Could not import {exchange} handler module: {e}")
            return None
        except AttributeError as e:
            self.logger.error(f"Handler class not found in {exchange} module: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error loading {exchange} handler: {e}")
            return None

    async def start_all_plugins(self):
        """Start all loaded plugins in separate threads"""
        if not self.plugins:
            self.logger.warning("No plugins loaded to start")
            return

        self.logger.info(f"Starting {len(self.plugins)} market data handlers...")

        for name, plugin in self.plugins.items():
            try:
                # Start handler in separate thread since it's synchronous
                thread = threading.Thread(
                    target=plugin.handler.run,
                    name=f"MarketData-{name}",
                    daemon=True
                )
                thread.start()
                plugin.thread = thread

                self.logger.info(f"✅ Started {name} handler")

            except Exception as e:
                self.logger.error(f"❌ Failed to start {name} handler: {e}")

        self.logger.info("All market data handlers started successfully")

    async def monitor_plugins(self):
        """Monitor running plugins and handle shutdown"""
        try:
            self.logger.info("Market data monitoring started. Press Ctrl+C to stop.")

            # Wait for shutdown signal
            await self.shutdown_event.wait()

        except Exception as e:
            self.logger.error(f"Error in monitoring: {e}")
        finally:
            await self.stop_all_plugins()

    async def stop_all_plugins(self):
        """Stop all running plugins"""
        self.logger.info("Stopping all market data handlers...")

        for name, plugin in self.plugins.items():
            try:
                # Request handler shutdown
                plugin.handler.shutdown_requested = True

                # Wait for thread to finish (with timeout)
                if plugin.thread and plugin.thread.is_alive():
                    plugin.thread.join(timeout=5.0)

                    if plugin.thread.is_alive():
                        self.logger.warning(f"{name} handler did not stop gracefully")
                    else:
                        self.logger.info(f"✅ Stopped {name} handler")

                # Cleanup handler resources
                plugin.handler.cleanup()

            except Exception as e:
                self.logger.error(f"Error stopping {name} handler: {e}")

        self.plugins.clear()
        self.logger.info("All market data handlers stopped")

    async def run(self):
        """Main run method"""
        try:
            await self.load_plugins()
            await self.start_all_plugins()
            await self.monitor_plugins()

        except Exception as e:
            self.logger.error(f"Unexpected error in market data manager: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.stop_all_plugins()


async def main():
    """Standalone entry — used by run.py and the supervisor."""
    manager = MarketDataManager()
    await manager.run()


if __name__ == "__main__":
    asyncio.run(main())