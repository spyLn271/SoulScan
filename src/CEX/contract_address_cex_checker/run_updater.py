#!/usr/bin/env python3
"""Dev-only entry point for the CEX contract-address updater service.

Production runs through the supervisor:
    python -m scripts.run_supervisor cex_contracts
"""
import asyncio
import os

from src.Config import config as _sscfg
from src.LoggerHandler.logger import setup_logger
from src.CEX.contract_address_cex_checker.service.updater import UpdaterService


if __name__ == "__main__":
    os.makedirs(_sscfg.CEX_CONTRACTS_LOG_FOLDER, exist_ok=True)
    setup_logger(
        logger_name="",  # root: catches all child getLogger() calls
        log_file=os.path.join(_sscfg.CEX_CONTRACTS_LOG_FOLDER, "CEX-Contracts.log"),
    )
    service = UpdaterService()
    asyncio.run(service.run_forever())
