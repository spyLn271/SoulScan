"""Back-compat shim.

`CexConfig` and its env-derived module values now live in `src/settings/config.py`, merged into ONE
config file alongside the DEX `Config` class. This module re-exports them so existing
`from src.settings import cex_config` / `from src.settings.cex_config import get_cex_config` imports keep
working unchanged. Prefer importing from `src.settings.config` directly; this shim can be removed at the
endgame (when the legacy src/cex importers are deleted).
"""
from src.settings.config import (  # noqa: F401  (re-export)
    CexConfig,
    get_cex_config,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_PASSWORD,
    CEX_LOG_FOLDER,
    CEX_MARKET_DATA_LOG_FOLDER,
    CEX_CONTRACTS_LOG_FOLDER,
    UPDATE_INTERVAL_SECONDS,
    BACKFILL_MIN_WITNESSES,
    PRICE_MATCH_ENABLED,
    PRICE_MATCH_MAX_DEVIATION,
    PRICE_MATCH_STREAM_MAX_AGE,
)
