from decimal import Decimal
from typing import TypedDict
import time
import pydantic

####################################
from src.DEX.Swap.math_.OriginMath.UniswapV2Math import UltimateUniswapV2Math
####################################



class UniswapV2SwapScheme(pydantic.BaseModel):
    reserves_x: Decimal
    reserves_y: Decimal
    delta_token: Decimal
    x_to_y: bool
    amount_specified_is_input: bool
    fee_kwarg: dict

class PoolSwap(TypedDict):
    remain: Decimal
    result: Decimal
    fee: Decimal
    message: str


class UniswapV2Swap:
    ultimate_math = UltimateUniswapV2Math()
    SwapScheme = UniswapV2SwapScheme

    def get_fee(self, **kwargs) -> Decimal:
        """
        Should be without percentage.
        :param kwargs: There always will be 'crossed_tick: int' and 'current_time: Decimal'
        :return: 0.03 % -> 0.0003
        """
        # return Decimal(str(kwargs["feeRate"]))  # for test
        raise Exception("Fee was not implemented yet.")

    def swap(self, params: UniswapV2SwapScheme) -> PoolSwap:
        reserves_x = params.reserves_x
        reserves_y = params.reserves_y
        delta_token = params.delta_token
        x_to_y = params.x_to_y
        amount_specified_is_input = params.amount_specified_is_input
        fee_kwarg = params.fee_kwarg | {"crossed_tick": 0, "current_time": Decimal(int(time.time()))}
        print(fee_kwarg)

        feeRate = self.get_fee(**fee_kwarg)

        amount_calc = delta_token
        if amount_specified_is_input:
            amount_calc = delta_token * (1 - feeRate)

        swap_computation = self.ultimate_math.swap_exact_token({
            "reserves_x": reserves_x,
            "reserves_y": reserves_y,
            "delta_token": amount_calc,
            "x_to_y": x_to_y,
            "amount_specified_is_input": amount_specified_is_input,
        })

        if amount_specified_is_input:
            return PoolSwap(
                remain=Decimal("0"),
                result=swap_computation,
                fee=delta_token - amount_calc,
                message='success'
            )
        else:
            return PoolSwap(
                remain=Decimal("0"),
                result=round(swap_computation / (1-feeRate)),
                fee=round(swap_computation * feeRate),
                message='success'
            )