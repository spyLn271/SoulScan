try:
    from src.supervisors.data_fetcher_supervisor import (
        RUN_METADATA_FETCHERS,
        RUN_STATE_FETCHERS,
    )
except ModuleNotFoundError as e:
    _optional = ("src.supervisors.data_fetcher_supervisor", "src.dex", "src.engine")
    if e.name and any(e.name == p or e.name.startswith(p + ".") for p in _optional):
        RUN_METADATA_FETCHERS = None
        RUN_STATE_FETCHERS = None
    else:
        raise


from src.supervisors.cex_contracts_supervisor import RUN_CEX_CONTRACTS

__all__ = [
    # DATA FETCHER SUPERVISORS
    "RUN_METADATA_FETCHERS",
    "RUN_STATE_FETCHERS",

    # cex SUPERVISORS
    "RUN_CEX_CONTRACTS",
]
