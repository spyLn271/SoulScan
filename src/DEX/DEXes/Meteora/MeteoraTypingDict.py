from typing import TypedDict

# DLMM V2
class LbPairDependencies(TypedDict):
    Address: str
    PDA: list[str]
    LbPair: list[str]
    start_indexes: list[int]

class MeteoraParameters(TypedDict):
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

class MeteoraVParameters(TypedDict):
    volatility_accumulator: int
    volatility_reference: int
    index_reference: int
    last_update_timestamp: int

class MeteoraBin(TypedDict):
    amount_x: int
    amount_y: int
    price: int
    liquidity_supply: int
    fee_amount_x_per_token_stored: int
    fee_amount_y_per_token_stored: int
    amount_x_in: int
    amount_y_in: int

class MeteoraLbPair(TypedDict):
    parameters: MeteoraParameters
    v_parameters: MeteoraVParameters
    active_id: int
    bin_step: int
    oracle: str

class MeteoraDlmm(TypedDict):
    LbPair: MeteoraLbPair
    bins: dict[str, MeteoraBin]

class MeteoraDlmmCache(MeteoraLbPair):
    pass


# DAMM V2

class MeteoraBaseFee(TypedDict):
    cliff_fee_numerator: int
    fee_scheduler_mode: int
    number_of_period: int
    period_frequency: int
    reduction_factor: int

class MeteoraDynamicFee(TypedDict):
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

class MeteoraDammV2(TypedDict):
    base_fee: MeteoraBaseFee
    dynamic_fee: MeteoraDynamicFee
    liquidity: int
    sqrt_min_price: int
    sqrt_max_price: int
    sqrt_price: int