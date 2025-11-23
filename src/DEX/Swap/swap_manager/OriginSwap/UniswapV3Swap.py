from decimal import Decimal, ROUND_HALF_UP
from typing import TypedDict
import time

####################################
from src.DEX.Swap.math_.OriginMath import UltimateUniswapV3Math
from src.Config.BasicSchemeAndTypeDict import Tick
####################################

class SwapStepComputation(TypedDict):
    amount_in: Decimal
    amount_out: Decimal
    fee: Decimal
    boundary_sqrt_P: Decimal
    is_max: bool

class PoolSwap(TypedDict):
    remain: Decimal
    result: Decimal
    fee: Decimal
    message: str


class UniswapV3SwapTD(TypedDict):
    amount_remaining: Decimal
    current_tick: Decimal
    tick_spacing: Decimal
    unnormalized_sqrt_P_start: Decimal
    factor: Decimal
    L: Decimal
    x_to_y: bool
    amount_specified_is_input: bool
    ticks: dict[str, Tick]
    fee_kwarg: dict

class UniswapV3SwapTickTD(TypedDict):
    amount_remaining: Decimal
    sqrt_P_start: Decimal
    upper_tick: Decimal
    lower_tick: Decimal
    L: Decimal
    fee: Decimal
    x_to_y: bool
    amount_specified_is_input: bool




class UltimateUniswapV3Swap:
    ultimate_math = UltimateUniswapV3Math()

    SwapTD = UniswapV3SwapTD

    def get_fee(self, **kwargs) -> Decimal:
        """
        Should be without percentage.
        :param kwargs: There always will be 'crossed_tick: int', 'current_time: Decimal', 'current_tick'
        and 'start_current_tick_group'
        :return: 0.03 % -> 0.0003
        """
        # return Decimal(str(kwargs["feeRate"])) / 1_000_000  # for test
        raise Exception("Fee was not implemented yet.")

    def swap_within_tick(self, params: UniswapV3SwapTickTD) -> SwapStepComputation:
        sqrt_P_start = params['sqrt_P_start']
        amount_remaining = params['amount_remaining']
        amount_specified_is_input = params['amount_specified_is_input']
        x_to_y = params['x_to_y']
        upper_tick = params['upper_tick']
        lower_tick = params['lower_tick']
        L = params['L']
        fee = params['fee']

        # 1) Normalizing amount_remaining
        amount_calc = amount_remaining
        if amount_specified_is_input:
            amount_calc = (amount_remaining * (1 - fee)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        # 2) setting sqrt_P_target
        if x_to_y:
            sqrt_P_target = self.ultimate_math.get_sqrt_P_from_tick(lower_tick)
        else:
            sqrt_P_target = self.ultimate_math.get_sqrt_P_from_tick(upper_tick)

        # 3) finding the available amount of token in the current tick range
        if amount_specified_is_input:
            if x_to_y:
                amount_available_delta_token = self.ultimate_math.get_x_amount(sqrt_P_start, sqrt_P_target, L)
            else:
                amount_available_delta_token = self.ultimate_math.get_y_amount(sqrt_P_start, sqrt_P_target, L)
        else:
            if x_to_y:
                amount_available_delta_token = self.ultimate_math.get_y_amount(sqrt_P_start, sqrt_P_target, L)
            else:
                amount_available_delta_token = self.ultimate_math.get_x_amount(sqrt_P_start, sqrt_P_target, L)

        # 4) determining if this is the max swap
        if amount_calc > amount_available_delta_token:
            is_max = True
            amount_being_swapped = amount_available_delta_token
        else:
            is_max = False
            amount_being_swapped = amount_calc

        # 5) actual swaping

        ultimate_math_params = self.ultimate_math.SwapingTD(
            sqrt_P_start=sqrt_P_start,
            L=L,
            delta_token=amount_being_swapped,
            x_to_y=x_to_y,
            amount_specified_is_input=amount_specified_is_input,
        )
        amount_swapped = self.ultimate_math.swap_exact_token(ultimate_math_params)

        if amount_specified_is_input:
            if is_max:
                fee_amount = (amount_being_swapped * fee) / (1 - fee)
            else:
                fee_amount = amount_remaining - amount_calc

            return SwapStepComputation(
                amount_in=amount_being_swapped,
                amount_out=amount_swapped,
                fee=fee_amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP),
                boundary_sqrt_P=sqrt_P_target,
                is_max=is_max,
            )
        else:
            fee_amount = amount_swapped * fee / (1 - fee)
            return SwapStepComputation(
                amount_in=amount_swapped,
                amount_out=amount_being_swapped,
                fee=fee_amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP),
                boundary_sqrt_P=sqrt_P_target,
                is_max=is_max,
            )

    def swap(self, params: UniswapV3SwapTD) -> PoolSwap:
        amount_remaining = params['amount_remaining']
        amount_calculated: Decimal = Decimal("0")
        fee_total: Decimal = Decimal("0")
        current_tick = params['current_tick']
        tick_spacing = params['tick_spacing']
        sqrt_P_start = self.ultimate_math.normalize_sqrt_P(params['unnormalized_sqrt_P_start'], params['factor'])
        x_to_y = params['x_to_y']
        L = params['L']
        liquidity_direction = -1 if x_to_y else 1
        amount_specified_is_input = params['amount_specified_is_input']
        ticks = params['ticks']
        fee_kwarg = params['fee_kwarg'] | {"crossed_tick": 0,
                                           "current_time": Decimal(int(time.time())),
                                           "current_tick": current_tick,
                                           "start_current_tick_group": current_tick // tick_spacing}

        current_tick_sterilized = (current_tick // tick_spacing) * tick_spacing
        lower_tick = current_tick_sterilized
        upper_tick = current_tick_sterilized + tick_spacing


        break_counter = 0
        while amount_remaining > 0 and break_counter < len(ticks):
            try:
                feeRate = self.get_fee(**fee_kwarg)

                swap_computation = self.swap_within_tick({
                    "sqrt_P_start": sqrt_P_start,
                    "amount_remaining": amount_remaining,
                    "amount_specified_is_input": amount_specified_is_input,
                    "x_to_y": x_to_y,
                    "upper_tick": upper_tick,
                    "lower_tick": lower_tick,
                    "L": L,
                    "fee": feeRate,
                })

                amount_in = swap_computation['amount_in']
                amount_out = swap_computation['amount_out']
                fee = swap_computation['fee']
                is_max = swap_computation["is_max"]
                boundary_sqrt_P = swap_computation['boundary_sqrt_P']

                fee_total += fee
                if amount_specified_is_input:
                    amount_remaining -= (amount_in + fee)
                    amount_calculated += amount_out
                else:
                    amount_remaining -= amount_out
                    amount_calculated += amount_in + fee


                if not is_max or amount_remaining < Decimal("1"):
                    break
                else:
                    if x_to_y:
                        current_tick = lower_tick
                        upper_tick = lower_tick
                        lower_tick -= tick_spacing
                        L += liquidity_direction * Decimal(ticks[str(current_tick - tick_spacing)]["liquidityNet"])
                    else:
                        current_tick = upper_tick
                        lower_tick = upper_tick
                        upper_tick += tick_spacing
                        L += liquidity_direction * Decimal(ticks[str(current_tick)]["liquidityNet"])

                    fee_kwarg["crossed_tick"] += liquidity_direction
                    fee_kwarg["current_tick"] = current_tick
                    sqrt_P_start = boundary_sqrt_P



            except Exception as e:
                return PoolSwap(
                    remain=amount_remaining,
                    result=amount_calculated,
                    fee=fee_total,
                    message=str(e),
                )

            break_counter += 1

        return PoolSwap(
            remain=amount_remaining,
            result=amount_calculated,
            fee=fee_total,
            message='success' if break_counter < len(ticks) else 'failure, loop was too long',
        )




def test():
    import redis
    import json
    from src.Config import config
    from src import WhirlpoolClmmScheme
    from src.DataFetcher.api_clients.Orca.OrcaMetadataScheme import OrcaMetadataScheme

    r = redis.Redis()

    market = 'orca'
    version = 'clmm'
    pool = 'Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE'
    x_decimal = 9
    y_decimal = 6

    current_state = json.loads(r.get(config.POOLS_CURRENT_STATE_DICT_REDIS_KEY % (market, version)))
    metadata = json.loads(r.get(config.REDIS_METADATA_KEY % (market, version)))
    swapV3 = UltimateUniswapV3Swap()

    target_pool_metadata = OrcaMetadataScheme(**metadata.get(pool))
    target_pool_state = WhirlpoolClmmScheme(**current_state.get(pool))


    # test 1

    amount_remaining_test_1 = Decimal(str(1139 * 10 ** x_decimal))
    swap_params_test_1 = swapV3.SwapTD(
        amount_remaining=amount_remaining_test_1,
        current_tick=Decimal(str(target_pool_state.base_info.tickCurrentIndex)),
        tick_spacing=Decimal(target_pool_state.base_info.tickSpacing),
        unnormalized_sqrt_P_start=Decimal(str(target_pool_state.base_info.sqrtPrice)),
        factor=Decimal("64"),
        L=Decimal(str(target_pool_state.base_info.liquidity)),
        x_to_y=True,
        amount_specified_is_input=True,
        ticks=target_pool_state.model_dump().get("ticks"),
        fee_kwarg=target_pool_metadata.model_dump()
    )
    result_test_1 = swapV3.swap(swap_params_test_1)
    print(f"TEST 1: {swap_params_test_1} \n"
          f"RESULT 1: {result_test_1} \n")
    print("_"*90)

    # test 2
    amount_remaining_test_2 = result_test_1["result"]
    swap_params_test_2 = swapV3.SwapTD(
        amount_remaining=amount_remaining_test_2,
        current_tick=Decimal(str(target_pool_state.base_info.tickCurrentIndex)),
        tick_spacing=Decimal(target_pool_state.base_info.tickSpacing),
        unnormalized_sqrt_P_start=Decimal(str(target_pool_state.base_info.sqrtPrice)),
        factor=Decimal("64"),
        L=Decimal(str(target_pool_state.base_info.liquidity)),
        x_to_y=True,
        amount_specified_is_input=False,
        ticks=target_pool_state.model_dump().get("ticks"),
        fee_kwarg=target_pool_metadata.model_dump()
    )
    result_test_2 = swapV3.swap(swap_params_test_2)
    print(f"TEST 2: {swap_params_test_2} \n"
          f"RESULT 2: {result_test_2} \n")
    print("_" * 90)

    # test 3
    amount_remaining_test_3 = Decimal(str(1200 * 10 ** x_decimal))
    swap_params_test_3 = swapV3.SwapTD(
        amount_remaining=amount_remaining_test_3,
        current_tick=Decimal(str(target_pool_state.base_info.tickCurrentIndex)),
        tick_spacing=Decimal(target_pool_state.base_info.tickSpacing),
        unnormalized_sqrt_P_start=Decimal(str(target_pool_state.base_info.sqrtPrice)),
        factor=Decimal("64"),
        L=Decimal(str(target_pool_state.base_info.liquidity)),
        x_to_y=False,
        amount_specified_is_input=False,
        ticks=target_pool_state.model_dump().get("ticks"),
        fee_kwarg=target_pool_metadata.model_dump()
    )
    result_test_3 = swapV3.swap(swap_params_test_3)
    print(f"TEST 3: {swap_params_test_3} \n"
          f"RESULT 3: {result_test_3} \n")
    print("_" * 90)

    # test 4
    amount_remaining_test_4 = result_test_3["result"]
    swap_params_test_4 = swapV3.SwapTD(
        amount_remaining=amount_remaining_test_4,
        current_tick=Decimal(str(target_pool_state.base_info.tickCurrentIndex)),
        tick_spacing=Decimal(target_pool_state.base_info.tickSpacing),
        unnormalized_sqrt_P_start=Decimal(str(target_pool_state.base_info.sqrtPrice)),
        factor=Decimal("64"),
        L=Decimal(str(target_pool_state.base_info.liquidity)),
        x_to_y=False,
        amount_specified_is_input=True,
        ticks=target_pool_state.model_dump().get("ticks"),
        fee_kwarg=target_pool_metadata.model_dump()
    )
    result_test_4 = swapV3.swap(swap_params_test_4)
    print(f"TEST 4: {swap_params_test_4} \n"
          f"RESULT 4: {result_test_4} \n")
    print("_" * 90)


if __name__ == '__main__':
    test()