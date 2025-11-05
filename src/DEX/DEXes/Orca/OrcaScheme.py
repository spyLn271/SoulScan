import pydantic
from typing import Dict


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

class WhirlpoolCacheDependenciesScheme(pydantic.BaseModel):
    Address: str
    BaseInfo: list[str]
    Oracle: list[str] | list

# Whirlpool Data Scheme
class TickScheme(pydantic.BaseModel):
    initialized: bool
    liquidityNet: int | None
    liquidityGross: int | None
    feeGrowthOutsideA: int | None
    feeGrowthOutsideB: int | None





class AdaptiveFeeConstantsScheme(pydantic.BaseModel):
    filterPeriod: int
    decayPeriod: int
    reductionFactor: int
    adaptiveFeeControlFactor: int
    maxVolatilityAccumulator: int
    tickGroupSize: int
    majorSwapThresholdTicks: int

class AdaptiveFeeVariablesScheme(pydantic.BaseModel):
    lastReferenceUpdateTimestamp: int
    lastMajorSwapTimestamp: int
    volatilityReference: int
    tickGroupIndexReference: int
    volatilityAccumulator: int

class OracleScheme(pydantic.BaseModel):
    adaptiveFeeConstants: AdaptiveFeeConstantsScheme
    adaptiveFeeVariables: AdaptiveFeeVariablesScheme




class WhirlpoolScheme(pydantic.BaseModel):
    tickSpacing: int
    feeRate: int
    liquidity: int
    sqrtPrice: int
    tickCurrentIndex: int
    rewardLastUpdatedTimestamp: int



class WhirlpoolCacheScheme(pydantic.BaseModel):
    baseInfo: WhirlpoolScheme
    oracle: OracleScheme | None

class WhirlpoolBigBoxScheme(pydantic.BaseModel):
    baseInfo: WhirlpoolScheme
    oracle: WhirlpoolScheme | None
    ticks: Dict[str, TickScheme]