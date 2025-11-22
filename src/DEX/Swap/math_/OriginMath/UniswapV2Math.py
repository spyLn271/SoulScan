from decimal import Decimal, ROUND_UP, ROUND_DOWN
import typing

class UniswapV2SwapingTD(typing.TypedDict):
    reserves_x: Decimal
    reserves_y: Decimal
    delta_token: Decimal
    x_to_y: bool
    amount_specified_is_input: bool


class UltimateUniswapV2Math:
    SwapingTD = UniswapV2SwapingTD

    """
    This class is pure for math. And it is assumed that delta_token was adjusted with fee.
    Fee will be considered in a higher class (Swapper class).
    """

    @staticmethod
    def swap_exact_token(params: UniswapV2SwapingTD) -> Decimal:
        reserves_x = params['reserves_x']
        reserves_y = params['reserves_y']
        delta_token = params['delta_token']
        x_to_y = params['x_to_y']
        amount_specified_is_input = params['amount_specified_is_input']

        if not amount_specified_is_input:
            delta_token *= -1
            x_to_y = not x_to_y

        if x_to_y:
            delta_y: Decimal = (reserves_y * delta_token) / (reserves_x + delta_token)
            return delta_y.quantize(Decimal("1"), ROUND_UP).__abs__()
        else:
            delta_x: Decimal = (reserves_x * delta_token) / (reserves_y + delta_token)
            return delta_x.quantize(Decimal("1"), ROUND_DOWN).__abs__()


def test():
    v2 = UltimateUniswapV2Math
    params = v2.SwapingTD(reserves_y=Decimal(str(500 * 10 ** 6)),
                          reserves_x=Decimal(str(100 * 10 ** 9)),
                          delta_token=Decimal(str(93490* 10 ** 9)),
                          x_to_y=True,
                          amount_specified_is_input=True)
    res = v2.swap_exact_token(params)
    print(res)

    params_2 = v2.SwapingTD(reserves_y=Decimal(str(500 * 10 ** 6)),
                            reserves_x=Decimal(str(100 * 10 ** 9)),
                            delta_token=res,
                            x_to_y=True,
                            amount_specified_is_input=False)
    res_2 = v2.swap_exact_token(params_2)
    print(res_2)

if __name__ == "__main__":
    test()