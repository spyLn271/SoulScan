#!/usr/bin/env python3
"""
Simple runner script for all market data handlers via Manager
This ensures all paths are set correctly
"""

# Fix Python path for imports
import sys
import os

import asyncio
from src.CEX.market_data.manager import main

if __name__ == "__main__":
    print("🚀 Starting ALL MARKET DATA HANDLERS with New Plugin Architecture")
    print("=" * 70)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 All market data handlers stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()