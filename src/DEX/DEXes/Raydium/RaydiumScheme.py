import pydantic
from src.Config.BasicSchemeAndTypeDict import TickScheme

# RaydiumCLMM Scheme
class RaydiumCLMMDependenciesScheme(pydantic.BaseModel):
    Address: str
    PDAs: list[str]
    PoolState: list[str]
    start_indexes: list[int]
    tick_spacing: int

class RaydiumCacheCLMMDependenciesScheme(pydantic.BaseModel):
    Address: str
    PoolState: str

class RaydiumPoolStateScheme(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')

    tick_spacing: int
    liquidity: int
    sqrt_price_x64: int
    tick_current: int
    amm_config: str
    tick_array_bitmap: list[int]


class RaydiumClmmScheme(pydantic.BaseModel):
    PoolState: RaydiumPoolStateScheme
    ticks: dict[str, TickScheme]

class RaydiumCacheClmmScheme(RaydiumPoolStateScheme):
    pass

# RaydiumHybridAMM scheme

class RaydiumBigBoxVaultAddressScheme(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')

    baseVault: str
    quoteVault: str


class VaultScheme(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')

    mint: str
    amount: int

class RaydiumClmmBaseInfo(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')

    status: int
    baseVault: str
    quoteVault: str
    baseNeedTakePnl: int
    quoteNeedTakePnl: int

class RaydiumHybridAmmScheme(pydantic.BaseModel):
    baseVault: VaultScheme
    quoteVault: VaultScheme
    BaseInfo: RaydiumClmmBaseInfo

class RaydiumHybridAmmCacheScheme(RaydiumClmmBaseInfo):
    pass