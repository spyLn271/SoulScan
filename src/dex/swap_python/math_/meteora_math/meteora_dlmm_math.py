from decimal import Decimal
from typing import TypedDict


####################################
from src.dex.swap_python.math_.origin_math.trader_joe_math import UltimateTraderJoeMath
from src.dex.solana.meteora.state.meteora_typing_dict import MeteoraLbPair, MeteoraParameters, MeteoraVParameters
####################################

class MeteoraDlmmFeeParameters(TypedDict):
    LbPair: MeteoraLbPair
    start_active_id: Decimal
    crossed_bins: int
    current_time: Decimal



class MeteoraDlmmMath(UltimateTraderJoeMath):
    dlmm_fee_params = MeteoraDlmmFeeParameters

    MAX_FEE = Decimal("0.1")

    def get_fee(self, params: MeteoraDlmmFeeParameters) -> Decimal:
        LbPair = params["LbPair"]

        parameters = LbPair["parameters"]
        v_parameters = LbPair["v_parameters"]
        bin_step = LbPair["bin_step"]

        start_active_id = params["start_active_id"]
        crossed_bins = params["crossed_bins"]
        current_time = params["current_time"]

        f_b = self._get_f_base(parameters["base_factor"], parameters["base_fee_power_factor"], bin_step)
        f_v = self._get_f_variable(parameters, v_parameters, bin_step, current_time, start_active_id, crossed_bins)
        f_s = f_b + f_v

        return min(f_s, self.MAX_FEE)


    @staticmethod
    def _get_f_base(base_factor: int, base_fee_power_factor: int, bin_step: int) -> Decimal:
        base_factor_decimal = Decimal(str(base_factor)) / 10_000
        base_fee_power_factor_decimal = Decimal(str(base_fee_power_factor))
        bin_step_decimal = Decimal(str(bin_step)) / 10_000

        return base_factor_decimal * bin_step_decimal * 10 ** base_fee_power_factor_decimal

    def _get_f_variable(self, parameters: MeteoraParameters, v_parameters: MeteoraVParameters,
                        bin_step: int, current_time: Decimal, start_active_id: Decimal, crossed_bins: int):
        v_a = self._get_volatility_accumulator(parameters, v_parameters, current_time, start_active_id, crossed_bins)
        A = Decimal(str(parameters["variable_fee_control"])) / 10_000
        s = Decimal(str(bin_step)) / 10_000


        return A * (v_a * s) ** 2


    @staticmethod
    def _get_volatility_accumulator(parameters: MeteoraParameters, v_parameters: MeteoraVParameters,
                                    current_time: Decimal, start_active_id: Decimal, crossed_bins: int):
        t_d = current_time - v_parameters["last_update_timestamp"]
        if t_d < parameters["filter_period"]:
            v_r = Decimal(str(v_parameters["volatility_reference"])) / 10_000
            i_r = v_parameters["index_reference"]
        elif parameters["filter_period"] <= t_d < parameters["decay_period"]:
            R = Decimal(str(parameters["reduction_factor"])) / 10_000
            v_a = Decimal(str(v_parameters["volatility_accumulator"])) / 10_000

            v_r = R * v_a
            i_r = start_active_id
        else:
            v_r = Decimal("0")
            i_r = start_active_id

        v_a_calc = v_r + abs(i_r - (start_active_id + crossed_bins))
        max_v_a = Decimal(str(parameters["max_volatility_accumulator"])) / 10_000
        return min(v_a_calc, max_v_a)