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