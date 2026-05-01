from decimal import Decimal, ROUND_CEILING
from typing import TypedDict

####################################
from src.dex.swap_python.math_.origin_math.uniswap_v3_math import UltimateUniswapV3Math
from src.dex.solana.orca.state.orca_typing_dict import Oracle
####################################



class OrcaClmmFeeParameters(TypedDict):
    fee_base: Decimal
    oracle: Oracle | None
    crossed_tick: int
    current_time: Decimal
    start_current_tick_group: Decimal | int


class OrcaClmmMath(UltimateUniswapV3Math):
    orca_fee_params = OrcaClmmFeeParameters
    ADAPTIVE_FEE_CONTROL_FACTOR_DENOMINATOR = Decimal("100_000")
    REDUCTION_FACTOR_DENOMINATOR = Decimal("10_000")
    VOLATILITY_ACCUMULATOR_SCALE_FACTOR = Decimal("10_000")
    FEE_DENOMINATOR = Decimal("1_000_000")
    MAX_FEE = Decimal("0.1")

    def get_fee(self, params: OrcaClmmFeeParameters) -> Decimal:
        fee_base = Decimal(str(params["fee_base"]))
        oracle = params["oracle"]

        if oracle is None:
            return fee_base / self.FEE_DENOMINATOR

        f_b = fee_base
        f_v = self.get_fee_variable(params)
        f_s = (f_b + f_v) / self.FEE_DENOMINATOR

        return min(f_s, self.MAX_FEE)


    def get_fee_variable(self, params: OrcaClmmFeeParameters) -> Decimal:
        v_a = self.get_volatility_accumulator(params)
        A = Decimal(str(params["oracle"]["adaptiveFeeConstants"]["adaptiveFeeControlFactor"]))
        s = Decimal(str(params["oracle"]["adaptiveFeeConstants"]["tickGroupSize"]))

        dividend = A * (v_a * s) ** 2
        divisor = (self.ADAPTIVE_FEE_CONTROL_FACTOR_DENOMINATOR * self.VOLATILITY_ACCUMULATOR_SCALE_FACTOR
                   * self.VOLATILITY_ACCUMULATOR_SCALE_FACTOR)

        f_v = (dividend / divisor).quantize(Decimal("1"), ROUND_CEILING)
        return f_v


    def get_volatility_accumulator(self, params: OrcaClmmFeeParameters) -> Decimal:
        t_f = params["oracle"]["adaptiveFeeConstants"]["filterPeriod"]
        t_d = params["oracle"]["adaptiveFeeConstants"]["decayPeriod"]
        delta_t = params["current_time"] - params['oracle']['adaptiveFeeVariables']['lastReferenceUpdateTimestamp']

        if delta_t < t_f:
            v_r = Decimal(str(params["oracle"]["adaptiveFeeVariables"]["volatilityReference"]))
            i_r = params["oracle"]["adaptiveFeeVariables"]["tickGroupIndexReference"]
        elif t_f <= delta_t < t_d:
            R = Decimal(str(params["oracle"]["adaptiveFeeConstants"]["reductionFactor"])) / self.REDUCTION_FACTOR_DENOMINATOR
            v_a = Decimal(str(params["oracle"]["adaptiveFeeVariables"]["volatilityAccumulator"]))

            v_r = R * v_a
            i_r = params["start_current_tick_group"]
        else:
            v_r = Decimal("0")
            i_r = params["start_current_tick_group"]


        index_delta = Decimal(str(abs(i_r - (params["start_current_tick_group"] + params["crossed_tick"]))))
        v_a_calc = v_r + index_delta * self.VOLATILITY_ACCUMULATOR_SCALE_FACTOR
        max_v_a = Decimal(str(params["oracle"]["adaptiveFeeConstants"]["maxVolatilityAccumulator"]))

        return min(v_a_calc, max_v_a)