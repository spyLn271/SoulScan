import pydantic
from typing import Dict
from src.Config.BasicSchemeAndTypeDict import TickScheme


"""
Orca CLMM
"""
# Dependencies Scheme
class WhirlpoolDependenciesScheme(pydantic.BaseModel):
    Address: str
    PDAs: list[str]
    BaseInfo: list[str]
    Oracle: list[str]
    start_indexes: list[int]
    tick_spacing: int
    af: bool

class WhirlpoolCacheDependenciesScheme(pydantic.BaseModel):
    Address: str
    BaseInfo: list[str]
    Oracle: list[str] | list

# Whirlpool Data Scheme
class AdaptiveFeeConstantsScheme(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')

    filterPeriod: int
    decayPeriod: int
    reductionFactor: int
    adaptiveFeeControlFactor: int
    maxVolatilityAccumulator: int
    tickGroupSize: int
    majorSwapThresholdTicks: int

class AdaptiveFeeVariablesScheme(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')

    lastReferenceUpdateTimestamp: int
    lastMajorSwapTimestamp: int
    volatilityReference: int
    tickGroupIndexReference: int
    volatilityAccumulator: int

class OracleScheme(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')

    adaptiveFeeConstants: AdaptiveFeeConstantsScheme
    adaptiveFeeVariables: AdaptiveFeeVariablesScheme




class WhirlpoolScheme(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')

    tickSpacing: int
    feeRate: int
    liquidity: int
    sqrtPrice: int
    tickCurrentIndex: int
    rewardLastUpdatedTimestamp: int


class WhirlpoolClmmScheme(pydantic.BaseModel):
    base_info: WhirlpoolScheme
    oracle: OracleScheme | None = None
    ticks: Dict[str, TickScheme]

class WhirlpoolCacheClmmScheme(pydantic.BaseModel):
    base_info: WhirlpoolScheme
    oracle: OracleScheme | None