from decimal import *


class UltimateTraderJoeMath:
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
    def swap_in_x_to_y_within_bin(P: Decimal, amountX: Decimal) -> Decimal:
        return P * amountX

    @staticmethod
    def swap_in_y_to_x_within_bin(P: Decimal, amountY: Decimal) -> Decimal:
        return amountY / P

    @staticmethod
    def swap_out_x_to_y_within_bin(P: Decimal, amountOutY: Decimal) -> Decimal:
        """
        Return the amount of token X is needed to get 'amountOutY' of token Y.
        """
        return amountOutY / P

    @staticmethod
    def swap_out_y_to_x_within_bin(P: Decimal, amountOutX: Decimal) -> Decimal:
        """
        Return the amount of token Y is needed to get 'amountOutX' of token X.
        """
        return P * amountOutX