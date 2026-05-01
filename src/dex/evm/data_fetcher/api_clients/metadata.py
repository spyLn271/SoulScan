from pydantic import BaseModel
from typing import TypedDict

class Metadata(BaseModel):
    token0: str
    token1: str
    addr0: str
    addr1: str
    decimals0: int
    decimals1: int
    volume24h: float
    tvl: float
    dex: str
    version: str

class MetadataDict(TypedDict):
    token0: str
    token1: str
    addr0: str
    addr1: str
    decimals0: int
    decimals1: int
    volume24h: float
    tvl: float
    dex: str
    version: str