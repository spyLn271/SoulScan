#!/usr/bin/env python3
"""Dev-only entry point for the cex contract-address updater service.

Production runs through the supervisor:
    python -m src.main cex_contracts
"""
import asyncio
import os

from src.settings import config as _sscfg
from src.logger_handler.logger import setup_logger
from src.cex.contract_address_cex_checker.service.updater import UpdaterService


if __name__ == "__main__":
    os.makedirs(_sscfg.CEX_CONTRACTS_LOG_FOLDER, exist_ok=True)
    setup_logger(
        logger_name="",  # root: catches all child getLogger() calls
        log_file=os.path.join(_sscfg.CEX_CONTRACTS_LOG_FOLDER, "cex-Contracts.log"),
    )
    service = UpdaterService()
    asyncio.run(service.run_forever())
