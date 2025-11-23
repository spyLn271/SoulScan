from decimal import Decimal
from typing import TypedDict


####################################
from src.DEX.Swap.swap_manager.OriginSwap.UniswapV3Swap import UltimateUniswapV3Swap, PoolSwap
from src.DEX.Swap.math_.OrcaMath.OrcaClmmMath import OrcaClmmMath
from src.DEX.DEXes.Orca.OrcaTypingDict import WhirlpoolClmm
from src.DataFetcher.api_clients.Orca.OrcaMetadataTypingDict import OrcaMetadata
####################################


class OrcaClmmSwapTD(TypedDict):
    pool_state: WhirlpoolClmm
    metadata: OrcaMetadata
    delta_amount: Decimal
    x_to_y: bool
    amount_specified_is_input: bool

class OrcaClmmSwap(UltimateUniswapV3Swap):
    orca_math = OrcaClmmMath()
    orca_swap_params = OrcaClmmSwapTD

    def get_fee(self, **kwargs) -> Decimal:
        """
        Should be without percentage.
        :param kwargs: There always will be 'crossed_tick: int', 'current_time: Decimal', 'current_tick'
        and 'start_current_tick_group'
        :return: 0.03 % -> 0.0003
        """
        oracle = kwargs.get("oracle")
        crossed_tick = kwargs["crossed_tick"]
        current_time = kwargs["current_time"]
        start_current_tick_group = kwargs["start_current_tick_group"]
        feeRate = kwargs["feeRate"]

        return self.orca_math.get_fee(self.orca_math.orca_fee_params(
            fee_base=feeRate,
            oracle=oracle,
            crossed_tick=crossed_tick,
            current_time=current_time,
            start_current_tick_group=start_current_tick_group
        ))

    def orca_clmm_swap(self, params: OrcaClmmSwapTD) -> PoolSwap:
        state = params['pool_state']
        metadata = params['metadata']
        delta_amount = params['delta_amount']
        x_to_y = params['x_to_y']
        amount_specified_is_input = params['amount_specified_is_input']

        current_tick = Decimal(str(state['base_info']['tickCurrentIndex']))
        tick_spacing = Decimal(str(state['base_info']['tickSpacing']))
        unnormalized_sqrt_P_start = Decimal(str(state['base_info']['sqrtPrice']))
        factor = Decimal("64")
        L = Decimal(str(state['base_info']['liquidity']))
        x_to_y = x_to_y
        amount_specified_is_input = amount_specified_is_input
        ticks = state['ticks']
        fee_kwarg = {'oracle': state['oracle'], 'feeRate': metadata['feeRate']}

        swap_params = self.SwapTD(
            amount_remaining=delta_amount,
            current_tick=current_tick,
            tick_spacing=tick_spacing,
            unnormalized_sqrt_P_start=unnormalized_sqrt_P_start,
            factor=factor,
            L=L,
            x_to_y=x_to_y,
            amount_specified_is_input=amount_specified_is_input,
            ticks=ticks,
            fee_kwarg=fee_kwarg
        )
        return self.swap(swap_params)




def test():
    import redis
    import json
    from src.Config import config
    from src import WhirlpoolClmmScheme
    from src.DataFetcher.api_clients.Orca.OrcaMetadataScheme import OrcaMetadataScheme
    import time

    r = redis.Redis()

    market = 'orca'
    version = 'clmm'
    pool = 'HsQGWEh3ib6w59rBh5n1jXmi8VXFBqKEjxozL6PGfcgb'
    x_decimal = 9
    y_decimal = 6

    current_state = json.loads(r.get(config.POOLS_CURRENT_STATE_DICT_REDIS_KEY % (market, version)))
    metadata = json.loads(r.get(config.REDIS_METADATA_KEY % (market, version)))
    swapV3 = OrcaClmmSwap()

    target_pool_metadata = OrcaMetadataScheme(**metadata.get(pool))
    target_pool_state = WhirlpoolClmmScheme(**current_state.get(pool))

    start_time = time.time()
    params_test_1 = swapV3.orca_swap_params(
        pool_state=target_pool_state.model_dump(),
        metadata=target_pool_metadata.model_dump(),
        delta_amount=Decimal(str(272 * 10 ** x_decimal)),
        x_to_y=True,
        amount_specified_is_input=True
    )
    print(target_pool_state.model_dump())
    print(target_pool_metadata.model_dump())
    res_test_1 = swapV3.orca_clmm_swap(params_test_1)
    print(f"TEST 1: {params_test_1} \n"
          f"RESULT 1: {res_test_1} \n")
    print(f"Output: {res_test_1['result'] / 10 ** y_decimal}")
    print(f"Time: {time.time() - start_time}")
    print("_"*90)



if __name__ == '__main__':
    test()