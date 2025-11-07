import pydantic


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

class RaydiumTickScheme(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')

    liquidity_net: int
    liquidity_gross: int

class RaydiumClmmScheme(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')

    PoolState: RaydiumPoolStateScheme
    ticks: dict[str, RaydiumTickScheme] | None = None