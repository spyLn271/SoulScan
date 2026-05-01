from typing import TypedDict, Dict
from src.settings.basic_schemes import Tick

# Dependencies
class WhirlpoolDependencies(TypedDict):
    Address: str
    PDAs: list[str]
    BaseInfo: list[str]
    Oracle: list[str]
    start_indexes: list[int]
    tick_spacing: int

class WhirlpoolCacheDependencies(TypedDict):
    Address: str
    BaseInfo: list[str]
    Oracle: list[str] | list

# Whirlpool Data
class AdaptiveFeeConstants(TypedDict):
    filterPeriod: int
    decayPeriod: int
    reductionFactor: int
    adaptiveFeeControlFactor: int
    maxVolatilityAccumulator: int
    tickGroupSize: int
    majorSwapThresholdTicks: int

class AdaptiveFeeVariables(TypedDict):
    lastReferenceUpdateTimestamp: int
    lastMajorSwapTimestamp: int
    volatilityReference: int
    tickGroupIndexReference: int
    volatilityAccumulator: int

class Oracle(TypedDict):
    adaptiveFeeConstants: AdaptiveFeeConstants
    adaptiveFeeVariables: AdaptiveFeeVariables




class Whirlpool(TypedDict):
    tickSpacing: int
    feeRate: int
    liquidity: int
    sqrtPrice: int
    tickCurrentIndex: int
    rewardLastUpdatedTimestamp: int


class WhirlpoolClmm(TypedDict):
    base_info: Whirlpool
    oracle: Oracle | None
    ticks: Dict[str, Tick]

class WhirlpoolCacheClmm(TypedDict):
    base_info: Whirlpool
    oracle: Oracle | None
