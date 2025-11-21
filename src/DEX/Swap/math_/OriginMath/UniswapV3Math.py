from decimal import Decimal, getcontext, ROUND_HALF_UP
import typing

getcontext().prec = 50
class UniswapV3SwapingTD(typing.TypedDict):
    sqrt_P_start: Decimal
    L: Decimal
    delta_token: Decimal
    amount_specified_is_input: bool
    x_to_y: bool

class UltimateUniswapV3Math:
    SwapingTD = UniswapV3SwapingTD

    """
    sqrt_P = sqrt(y/x)
    1/sqrt_P = sqrt(x/y)

    delta_y = (sqrt_P_end - sqrt_P_start) * L
    delta_x = (1/sqrt_P_end - 1/sqrt_P_start) * L

    if delta_token < 0, then that amount of token will be removed from a pool.
    if delta_token > 0, then that amount of token will be added to a pool.
    but functions will always return positive value.
    
    P.S this class is pure for math within one single tick range. 
    And it is assumed that delta_token was adjusted with fee.
    Fee will be considered in a higher class (Swapper class).
    """
    @staticmethod
    def normalize_sqrt_P(sqrt_P: Decimal, factor: int | Decimal = 64) -> Decimal:
        return sqrt_P / 2 ** factor

    @staticmethod
    def get_sqrt_P_from_tick(tick: Decimal) -> Decimal:
        return Decimal("1.0001") ** (tick / 2)

    @staticmethod
    def get_x_amount(sqrt_P_start: Decimal, sqrt_P_end: Decimal, L: Decimal) -> Decimal:
        delta_x: Decimal = abs((1/sqrt_P_end - 1/sqrt_P_start) * L)
        return abs(delta_x.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    @staticmethod
    def get_y_amount(sqrt_P_start: Decimal, sqrt_P_end: Decimal, L: Decimal) -> Decimal:
        delta_y: Decimal = abs((sqrt_P_end - sqrt_P_start) * L)
        return abs(delta_y.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    @staticmethod
    def get_sqrt_P_end_with_x(sqrt_P_start: Decimal, L: Decimal, delta_x: Decimal) -> Decimal:
        sqrt_P_end: Decimal = (L * sqrt_P_start) / (delta_x * sqrt_P_start + L)
        return sqrt_P_end

    @staticmethod
    def get_sqrt_P_end_with_y(sqrt_P_start: Decimal, L: Decimal, delta_y: Decimal) -> Decimal:
        sqrt_P_end: Decimal = delta_y / L + sqrt_P_start
        return sqrt_P_end

    def swap_exact_token(self, params: UniswapV3SwapingTD) -> Decimal:
        sqrt_P_start = params['sqrt_P_start']
        L = params['L']
        delta_token = params['delta_token']
        amount_specified_is_input = params['amount_specified_is_input']
        x_to_y = params['x_to_y']

        if not amount_specified_is_input:
            delta_token *= -1
            x_to_y = not x_to_y

        if x_to_y:
            sqrt_P_end = self.get_sqrt_P_end_with_x(sqrt_P_start=sqrt_P_start, L=L, delta_x=delta_token)
            return self.get_y_amount(sqrt_P_start=sqrt_P_start, sqrt_P_end=sqrt_P_end, L=L)
        else:
            sqrt_P_end = self.get_sqrt_P_end_with_y(sqrt_P_start=sqrt_P_start, L=L, delta_y=delta_token)
            return self.get_x_amount(sqrt_P_start=sqrt_P_start, sqrt_P_end=sqrt_P_end, L=L)


def test():
    v3 = UltimateUniswapV3Math()
    x_decimal = 9
    y_decimal = 6

    sqrt_P_start_unnormal = Decimal("6704935623889218560")
    sqrt_P_start = v3.normalize_sqrt_P(sqrt_P_start_unnormal, Decimal("64"))
    L = Decimal("106501969658262")
    delta_token = Decimal("1000") * 10 ** y_decimal

    params = v3.SwapingTD(sqrt_P_start=sqrt_P_start, L=L, delta_token=delta_token, amount_specified_is_input=False,
                          x_to_y=True)
    print(
        v3.swap_exact_token(params) / 10 ** x_decimal
    )

    params = v3.SwapingTD(sqrt_P_start=sqrt_P_start, L=L, delta_token=v3.swap_exact_token(params), amount_specified_is_input=True, x_to_y=True)
    print(
        v3.swap_exact_token(params) / 10 ** y_decimal
    )


    next_tick = Decimal("-20241")
    next_sqrt_P = v3.get_sqrt_P_from_tick(tick=next_tick)

    amount_x = v3.get_x_amount(sqrt_P_start=sqrt_P_start, sqrt_P_end=next_sqrt_P, L=L) / 10 ** x_decimal
    amount_y = v3.get_y_amount(sqrt_P_start=sqrt_P_start, sqrt_P_end=next_sqrt_P, L=L) / 10 ** y_decimal
    print(amount_x, amount_y)
    print(type(amount_x), type(amount_y))
    print(next_sqrt_P, sqrt_P_start)

if __name__ == '__main__':
    test()