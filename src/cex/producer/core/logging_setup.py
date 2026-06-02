"""Thin shim routing producer logging through SoulScan's central logger.

Preserves the call surface of the original per-exchange logging_setup.py so
plugins and exchange_manager need no edits, but internally delegates to
src.logger_handler.logger and writes into config.CEX_LOG_FOLDER. The
Redis-stream log handler is no longer supported — the Flask admin panel
that consumed it was dropped during the SoulScan merge.
"""

import logging
import os
from typing import Optional

from src.settings import cex_config as sscfg
from src.logger_handler.logger import setup_logger, get_logger


def ensure_log_directories() -> None:
    os.makedirs(sscfg.CEX_LOG_FOLDER, exist_ok=True)


def _log_path(name: str) -> str:
    ensure_log_directories()
    return os.path.join(sscfg.CEX_LOG_FOLDER, f"{name}.log")


def _resolve_level(name: str) -> int:
    return getattr(logging, name.upper(), logging.INFO)


def setup_root_logger(console_level: str = 'WARNING') -> logging.Logger:
    return logging.getLogger()


def setup_exchange_logger(
    exchange_name: str,
    market_type: str,
    file_level: str = 'INFO',
    console_level: Optional[str] = None,
) -> logging.Logger:
    logger_name = f"{exchange_name}_{market_type}"
    return setup_logger(
        level=_resolve_level(file_level),
        log_file=_log_path(logger_name),
        logger_name=logger_name,
    )


def setup_manager_logger(
    manager_name: str = 'exchange_manager',
    file_level: str = 'INFO',
    console_level: str = 'INFO',
) -> logging.Logger:
    return setup_logger(
        level=_resolve_level(file_level),
        log_file=_log_path(manager_name),
        logger_name=manager_name,
    )


def get_logger_for_connector(exchange_name: str, market_type: str) -> logging.Logger:
    logger_name = f"{exchange_name}_{market_type}"
    logger = get_logger(logger_name)
    if not logger.handlers:
        return setup_logger(
            level=logging.INFO,
            log_file=_log_path(logger_name),
            logger_name=logger_name,
        )
    return logger


class _NoopStreamer:
    """Stand-in for the old RedisLogStreamer so legacy call sites don't break."""

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    def add_handler(self, _handler) -> None:
        return None


def setup_redis_log_streaming(redis_client) -> _NoopStreamer:
    return _NoopStreamer()


def add_redis_handler_to_logger(
    logger: logging.Logger,
    exchange_name: str,
    market_type: str,
    streamer,
    log_level: str = 'INFO',
):
    return None


async def setup_standalone_logging(exchange_name: str, market_type: str):
    logger = setup_exchange_logger(exchange_name, market_type, file_level='INFO')
    return logger, _NoopStreamer()
