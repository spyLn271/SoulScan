# Supervisor entrypoints.
#
# The CEX supervisors are always available. The DEX data-fetcher and engine
# supervisors are optional: on a CEX-only checkout their modules (and the
# src/dex, src/engine packages they import) may be absent. We import those
# lazily-tolerantly so that `python -m src.main cex_*` runs without the DEX/engine
# code present, while a full checkout still exports every name unchanged.

try:
    from src.supervisors.data_fetcher_supervisor import (
        RUN_METADATA_FETCHERS,
        RUN_STATE_FETCHERS,
    )
except ImportError:  # CEX-only checkout: src/dex not present
    RUN_METADATA_FETCHERS = None
    RUN_STATE_FETCHERS = None

try:
    from src.supervisors.engine_supervisor import (
        EthereumOSRSupervisor,
        BaseOSRSupervisor,
        ArbitrumOSRSupervisor,
        SolanaOSRSupervisor,
        BinanceOSRSupervisor,
    )
except ImportError:  # CEX-only checkout: src/engine not present
    EthereumOSRSupervisor = None
    BaseOSRSupervisor = None
    ArbitrumOSRSupervisor = None
    SolanaOSRSupervisor = None
    BinanceOSRSupervisor = None

from src.supervisors.cex_contracts_supervisor import RUN_CEX_CONTRACTS

__all__ = [
    # DATA FETCHER SUPERVISORS
    "RUN_METADATA_FETCHERS",
    "RUN_STATE_FETCHERS",

    # SOUL ENGINE SUPERVISORS
    "EthereumOSRSupervisor",
    "BaseOSRSupervisor",
    "ArbitrumOSRSupervisor",
    "SolanaOSRSupervisor",
    "BinanceOSRSupervisor",

    # cex SUPERVISORS
    "RUN_CEX_CONTRACTS",
]
