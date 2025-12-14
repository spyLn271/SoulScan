#!/usr/bin/env python3
"""
Runner script for the CEX updater service.
Handles Python path setup so it works with venv in parent folder. lol

Usage: python3 run_updater.py
"""
import sys
import os

# Add parent directory (contract_address_cex_checker) to Python path so 'service' is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from service.updater import UpdaterService


if __name__ == "__main__":
    service = UpdaterService()
    asyncio.run(service.run_forever())
