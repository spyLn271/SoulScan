from typing import TypedDict
from src.Config.BasicSchemeAndTypeDict import Tick

# RaydiumCLMM
class RaydiumCLMMDependencies(TypedDict):
    Address: str
    PDAs: list[str]
    PoolState: list[str]
    start_indexes: list[int]
    tick_spacing: int

class RaydiumCacheCLMMDependencies(TypedDict):
    Address: str
    PoolState: str

class RaydiumPoolState(TypedDict):
    tick_spacing: int
    liquidity: int
    sqrt_price_x64: int
    tick_current: int


class RaydiumClmm(TypedDict):
    PoolState: RaydiumPoolState
    ticks: dict[str, Tick]

class RaydiumCacheClmm(TypedDict):
    pass

# RaydiumHybridAMM

class RaydiumBigBoxVaultAddress(TypedDict):
    baseVault: str
    quoteVault: str


class Vault(TypedDict):
    mint: str
    amount: int

class RaydiumClmmBaseInfo(TypedDict):
    status: int
    baseVault: str
    quoteVault: str
    baseNeedTakePnl: int
    quoteNeedTakePnl: int

class RaydiumHybridAmm(TypedDict):
    baseVault: Vault
    quoteVault: Vault
    BaseInfo: RaydiumClmmBaseInfo

class RaydiumHybridAmmCache(RaydiumClmmBaseInfo):
    pass