from decimal import Decimal
from typing import TypedDict

####################################
from src.DEX.Swap.math_.OriginMath.UniswapV3Math import UltimateUniswapV3Math
from src.DEX.DEXes.Orca.OrcaTypingDict import Oracle
####################################



class OrcaClmmFeeParameters(TypedDict):
    fee_base: Decimal
    oracle: Oracle | None
    crossed_tick: int
    current_time: Decimal
    start_current_tick_group: Decimal | int


class OrcaClmmMath(UltimateUniswapV3Math):
    orca_fee_params = OrcaClmmFeeParameters

    def get_fee(self, params: OrcaClmmFeeParameters) -> Decimal:
        fee_base = Decimal(str(params["fee_base"])) / 1_000_000
        oracle = params["oracle"]

        if oracle is None:
            return fee_base

        f_b = fee_base
        f_v = self.get_fee_variable(params)

        return f_b + f_v


    def get_fee_variable(self, params: OrcaClmmFeeParameters) -> Decimal:
        v_a = self.get_volatility_accumulator(params)
        A = Decimal(str(params["oracle"]["adaptiveFeeConstants"]["adaptiveFeeControlFactor"])) / 10_000
        s = Decimal(str(params["oracle"]["adaptiveFeeConstants"]["tickGroupSize"])) / 10_000

        return A * (v_a * s) ** 2

    @staticmethod
    def get_volatility_accumulator(params: OrcaClmmFeeParameters) -> Decimal:
        t_f = params["oracle"]["adaptiveFeeConstants"]["filterPeriod"]
        t_d = params["oracle"]["adaptiveFeeConstants"]["decayPeriod"]

        if params["current_time"] < t_f:
            v_r = Decimal(str(params["oracle"]["adaptiveFeeVariables"]["volatilityReference"])) / 10_000
            i_r = params["oracle"]["adaptiveFeeVariables"]["tickGroupIndexReference"]
        elif t_f <= params["current_time"] < t_d:
            R = Decimal(str(params["oracle"]["adaptiveFeeConstants"]["reductionFactor"])) / 10_000
            v_a = Decimal(str(params["oracle"]["adaptiveFeeVariables"]["volatilityAccumulator"])) / 10_000

            v_r = R * v_a
            i_r = params["start_current_tick_group"]
        else:
            v_r = Decimal("0")
            i_r = params["start_current_tick_group"]

        return v_r + abs(i_r - (params["start_current_tick_group"] + params["crossed_tick"]))