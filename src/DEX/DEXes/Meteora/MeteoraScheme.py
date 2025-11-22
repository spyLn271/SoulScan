import pydantic
from src.Config.BasicSchemeAndTypeDict import BinScheme

# DLMM V2 Schemes
class LbPairDependenciesScheme(pydantic.BaseModel):
    Address: str
    PDA: list[str]
    LbPair: list[str]
    start_indexes: list[int]

class MeteoraParametersScheme(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')

    base_factor: int
    filter_period: int
    decay_period: int
    reduction_factor: int
    variable_fee_control: int
    max_volatility_accumulator: int
    min_bin_id: int
    max_bin_id: int
    protocol_share: int
    base_fee_power_factor: int

class MeteoraVParametersScheme(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')

    volatility_accumulator: int
    volatility_reference: int
    index_reference: int
    last_update_timestamp: int


class MeteoraLbPairScheme(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')

    parameters: MeteoraParametersScheme
    v_parameters: MeteoraVParametersScheme
    active_id: int
    bin_step: int
    oracle: str

class MeteoraDlmmScheme(pydantic.BaseModel):
    LbPair: MeteoraLbPairScheme
    bins: dict[str, BinScheme]

class MeteoraDlmmCacheScheme(MeteoraLbPairScheme):
    pass


# DAMM V2 Scheme

class MeteoraBaseFeeScheme(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')

    cliff_fee_numerator: int
    fee_scheduler_mode: int
    number_of_period: int
    period_frequency: int
    reduction_factor: int

class MeteoraDynamicFeeScheme(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')

    initialized: int
    max_volatility_accumulator: int
    variable_fee_control: int
    bin_step: int
    filter_period: int
    decay_period: int
    reduction_factor: int
    last_update_timestamp: int
    bin_step_u128: int
    sqrt_price_reference: int
    volatility_accumulator: int
    volatility_reference: int

class MeteoraDammV2Scheme(pydantic.BaseModel):
    base_fee: MeteoraBaseFeeScheme
    dynamic_fee: MeteoraDynamicFeeScheme
    liquidity: int
    sqrt_min_price: int
    sqrt_max_price: int
    sqrt_price: int
