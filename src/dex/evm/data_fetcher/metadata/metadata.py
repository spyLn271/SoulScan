from pydantic import BaseModel
from typing import TypedDict

class Metadata(BaseModel):
    token0: str
    token1: str
    mint0: str
    mint1: str
    decimals0: int
    decimals1: int
    fee_rate: int
    tick_spacing: int
    volume24h: float
    tvl: float
    dex: str
    version: str

class MetadataDict(TypedDict):
    token0: str
    token1: str
    mint0: str
    mint1: str
    decimals0: int
    decimals1: int
    fee_rate: int
    tick_spacing: int
    volume24h: float
    tvl: float
    dex: str
    version: str