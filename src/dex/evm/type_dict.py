from pydantic import BaseModel
from typing import TypedDict
from src.settings.config import Version, DEX, Network


# metadata
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
    dex: DEX
    version: Version

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
    dex: DEX
    version: Version


# Uniswap V3 Slot
class Slot(BaseModel):
    sqrt_price_x96: int
    tick_current: int
    liquidity: int

class SlotDict(TypedDict):
    sqrt_price_x96: int
    tick_current: int
    liquidity: int