from decimal import Decimal
import typing

class UniswapV2SwapingTD(typing.TypedDict):
    reserves_x: Decimal
    reserve_y: Decimal
    delta_token: Decimal
    x_to_y: bool


class UltimateUniswapV2Math:
    SwapingTD = UniswapV2SwapingTD

    """
    This class is pure for math. And it is assumed that delta_token was adjusted with fee.
    Fee will be considered in a higher class (Swapper class).
    """

    @staticmethod
    def swap_exact_token(params: UniswapV2SwapingTD) -> Decimal:
        reserves_x = params['reserves_x']
        reserve_y = params['reserve_y']
        delta_token = params['delta_token']
        x_to_y = params['x_to_y']

        if x_to_y:
            delta_y: Decimal = (reserve_y * delta_token) // (reserves_x + delta_token)
            return delta_y
        else:
            delta_x: Decimal = (reserves_x * delta_token) // (reserve_y + delta_token)
            return delta_x


def test():
    v2 = UltimateUniswapV2Math
    params = v2.SwapingTD(reserve_y=Decimal("500") * 10 ** 6,
                          reserves_x=Decimal("100") * 10 ** 9,
                          delta_token=Decimal("1") * 10 ** 9, x_to_y=True)
    print(
        v2.swap_exact_token(params)
    )

if __name__ == "__main__":
    test()