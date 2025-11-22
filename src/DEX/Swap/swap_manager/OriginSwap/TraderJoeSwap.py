from decimal import Decimal
from typing import TypedDict
import time


####################################
from src.DEX.Swap.math_.OriginMath.TraderJoeMath import UltimateTraderJoeMath
from src.Config.BasicSchemeAndTypeDict import Bins
####################################

class SwapStepComputation(TypedDict):
    amount_in: Decimal
    amount_out: Decimal
    fee: Decimal
    is_max: bool

class PoolSwap(TypedDict):
    remain: Decimal
    result: Decimal
    fee: Decimal
    message: str

class TraderJoeSwapTD(TypedDict):
    amount_remaining: Decimal
    P: Decimal
    active_id: Decimal
    bin_step: Decimal
    bins: dict[str, Bins]
    x_to_y: bool
    amount_specified_is_input: bool
    fee_kwarg: dict

class TraderJoeSwapBinTD(TypedDict):
    amount_remaining: Decimal
    P: Decimal
    reserves_x: Decimal
    reserves_y: Decimal
    fee: Decimal
    x_to_y: bool
    amount_specified_is_input: bool


class TraderJoeSwap:
    ultimate_math = UltimateTraderJoeMath()
    SwapTD = TraderJoeSwapTD


    @staticmethod
    def get_fee(**kwargs) -> Decimal:
        """
        Should be without percentage.
        :param kwargs: There always will be 'crossed_bins: int' and 'current_time: Decimal'
        :return: 0.03 % -> 0.0003
        """
        raise Exception("Fee was not implemented yet.")


    def swap_within_bin(self, params: TraderJoeSwapBinTD) -> SwapStepComputation:
        amount_remaining = params['amount_remaining']
        P = params['P']
        reserves_x = params['reserves_x']
        reserves_y = params['reserves_y']
        fee = params['fee']
        x_to_y = params['x_to_y']
        amount_specified_is_input = params['amount_specified_is_input']

        # 1) Normalizing amount remaining
        amount_calc = amount_remaining
        if amount_specified_is_input:
            amount_calc = amount_remaining * (Decimal("1") - fee)


        # 2) Finding max swap amount
        if amount_specified_is_input:
            if x_to_y:
                amount_available_delta_token = self.ultimate_math.get_max_amount_of_x_in_bin(P, reserves_y)
            else:
                amount_available_delta_token = self.ultimate_math.get_max_amount_of_y_in_bin(P, reserves_x)
        else:
            if x_to_y:
                amount_available_delta_token = reserves_y
            else:
                amount_available_delta_token = reserves_x

        # 3) Determining if this max swap
        if amount_calc > amount_available_delta_token:
            is_max = True
            amount_being_swapped = amount_available_delta_token
        else:
            is_max = False
            amount_being_swapped = amount_calc

        # 4) actual swaping
        ultimate_math_params = self.ultimate_math.SwapingTD(
            P=P,
            delta_token=amount_being_swapped,
            x_to_y=x_to_y,
            amount_specified_is_input=amount_specified_is_input,
        )
        amount_swapped = self.ultimate_math.swap_exact_token(ultimate_math_params)

        if amount_specified_is_input:
            if is_max:
                fee_amount = (amount_being_swapped * fee) / (Decimal("1") - fee)
            else:
                fee_amount = amount_remaining - amount_calc

            return SwapStepComputation(
                amount_in=amount_being_swapped,
                amount_out=amount_swapped,
                fee=fee_amount,
                is_max=is_max,
            )
        else:
            fee_amount = amount_swapped * fee / (Decimal("1") - fee)
            return SwapStepComputation(
                amount_in=amount_swapped,
                amount_out=amount_being_swapped,
                fee=fee_amount,
                is_max=is_max,
            )


    def swap(self, params: TraderJoeSwapTD) -> PoolSwap:
        amount_remaining = params['amount_remaining']
        amount_calculated: Decimal = Decimal("0")
        fee_total: Decimal = Decimal("0")
        active_id = params['active_id']
        bin_step = params['bin_step']
        bins = params['bins']
        x_to_y = params['x_to_y']
        amount_specified_is_input = params['amount_specified_is_input']
        fee_kwarg = params['fee_kwarg'] | {"crossed_bins": 0, "current_time": Decimal(int(time.time()))}

        message: str = 'failure, loop was too long'
        bin_direction = -1 if x_to_y else 1
        break_counter = 0
        while amount_remaining > Decimal("1") and break_counter < len(bins):
            try:
                break_counter += 1
                active_reserves_x = Decimal(str(bins[str(active_id)]["amount_x"]))
                active_reserves_y = Decimal(str(bins[str(active_id)]["amount_y"]))
                if x_to_y and active_reserves_y == 0:
                    active_id += bin_direction
                    continue
                elif not x_to_y and active_reserves_x == 0:
                    active_id += bin_direction
                    continue
                P = self.ultimate_math.get_price_from_id(active_id, bin_step)
                feeRate = self.get_fee(**fee_kwarg)

                swap_computation = self.swap_within_bin({
                    "amount_remaining": amount_remaining,
                    "P": P,
                    "reserves_x": active_reserves_x,
                    "reserves_y": active_reserves_y,
                    "fee": feeRate,
                    "x_to_y": x_to_y,
                    "amount_specified_is_input": amount_specified_is_input,
                })
                amount_in = swap_computation['amount_in']
                amount_out = swap_computation['amount_out']
                fee = swap_computation['fee']
                is_max = swap_computation["is_max"]

                fee_total += fee
                if amount_specified_is_input:
                    amount_remaining -= (amount_in + fee)
                    amount_calculated += amount_out
                else:
                    amount_remaining -= amount_out
                    amount_calculated += amount_in + fee


                if not is_max or amount_remaining < Decimal("1"):
                    message = 'success'
                    break
                else:
                    fee_kwarg["crossed_bins"] += 1
                    active_id += bin_direction
            except KeyError:
                message = f"Bin with id: {str(active_id)} was not found."
                break
            except Exception as e:
                message = str(e)
                break

        return PoolSwap(
            remain=amount_remaining,
            result=amount_calculated,
            fee=fee_total,
            message=message,
        )