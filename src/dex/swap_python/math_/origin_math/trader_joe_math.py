from decimal import *
from typing import TypedDict

class TraderJoeSwapingTD(TypedDict):
    P: Decimal
    delta_token: Decimal
    x_to_y: bool
    amount_specified_is_input: bool


class UltimateTraderJoeMath:
    SwapingTD = TraderJoeSwapingTD

    @staticmethod
    def get_price_from_id(activeId: Decimal, binStep: Decimal) -> Decimal:
        return (1 + binStep / 10_000) ** activeId

    @staticmethod
    def get_max_amount_of_x_in_bin(P: Decimal, reserveY: Decimal) -> Decimal:
        return reserveY / P

    @staticmethod
    def get_max_amount_of_y_in_bin(P: Decimal, reserveX: Decimal) -> Decimal:
        return reserveX * P


    @staticmethod
    def swap_exact_token(params: TraderJoeSwapingTD) -> Decimal:
        P = params['P']
        delta_token = params['delta_token']
        x_to_y = params['x_to_y']
        amount_specified_is_input = params['amount_specified_is_input']

        if not amount_specified_is_input:
            x_to_y = not x_to_y

        if x_to_y:
            return P * delta_token
        else:
            return delta_token / P