import pydantic

class BaseMetadataScheme(pydantic.BaseModel):
    token0: str
    token1: str
    mint0: str
    mint1: str
    decimals0: int
    decimals1: int
    volume24h: float
    dex: str
    version: str