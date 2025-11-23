from decimal import Decimal
from typing import TypedDict


####################################
from src.DEX.Swap.swap_manager.OriginSwap.UniswapV3Swap import UltimateUniswapV3Swap, PoolSwap
from src.DEX.DEXes.Raydium.RaydiumTypingDict import RaydiumClmm
from src.DataFetcher.api_clients.Raydium.RaydiumMetadataTypingDict import RaydiumMetadata
####################################

class RayClmmSwapTD(TypedDict):
    pool_state: RaydiumClmm
    metadata: RaydiumMetadata
    delta_amount: Decimal
    x_to_y: bool
    amount_specified_is_input: bool

class RayClmmSwap(UltimateUniswapV3Swap):
    raydium_swap_params = RayClmmSwapTD

    def get_fee(self, **kwargs) -> Decimal:
        """
        Should be without percentage.
        :param kwargs: There always will be 'crossed_tick: int', 'current_time: Decimal', 'current_tick'
        and 'start_current_tick_group'
        :return: 0.03 % -> 0.0003
        """
        metadat: RaydiumMetadata = kwargs['metadata']
        return Decimal(str(metadat['feeRate']))

    def raydium_clmm_swap(self, params: RayClmmSwapTD) -> PoolSwap:
        state: RaydiumClmm = params['pool_state']
        delta_amount: Decimal = params['delta_amount']
        x_to_y: bool = params['x_to_y']
        amount_specified_is_input: bool = params['amount_specified_is_input']

        swap_params = self.SwapTD(
            amount_remaining=delta_amount,
            current_tick=Decimal(str(state['PoolState']['tick_current'])),
            tick_spacing=Decimal(str(state['PoolState']['tick_spacing'])),
            unnormalized_sqrt_P_start=Decimal(str(state['PoolState']['sqrt_price_x64'])),
            factor=Decimal("64"),
            L=Decimal(str(state['PoolState']['liquidity'])),
            x_to_y=x_to_y,
            amount_specified_is_input=amount_specified_is_input,
            ticks=state['ticks'],
            fee_kwarg={'metadata': params['metadata']}
        )
        return self.swap(swap_params)



def test():
    import redis
    import json
    from src.Config import config
    from src import RaydiumClmmScheme
    from src.DataFetcher.api_clients.Raydium.RaydiumMetadataScheme import RaydiumMetadataScheme
    import time

    r = redis.Redis()

    market = 'raydium'
    version = 'clmm'
    pool = '2AXXcN6oN9bBT5owwmTH53C7QHUXvhLeu718Kqt8rvY2'
    x_decimal = 9
    y_decimal = 6

    current_state = json.loads(r.get(config.POOLS_CURRENT_STATE_DICT_REDIS_KEY % (market, version)))
    metadata = json.loads(r.get(config.REDIS_METADATA_KEY % (market, version)))
    swapV3 = RayClmmSwap()

    target_pool_metadata = RaydiumMetadataScheme(**metadata.get(pool))
    target_pool_state = RaydiumClmmScheme(**current_state.get(pool))

    swap_params_test_1 = swapV3.raydium_swap_params(
        pool_state=target_pool_state.model_dump(),
        metadata=target_pool_metadata.model_dump(),
        delta_amount=Decimal(str(1 * 10 ** x_decimal)),
        x_to_y=True,
        amount_specified_is_input=True
    )
    res_test_1 = swapV3.raydium_clmm_swap(swap_params_test_1)
    print(f"TEST 1: {swap_params_test_1} \n"
          f"RESULT 1: {res_test_1} \n")
    print(f"Output: {res_test_1['result'] / 10 ** y_decimal}")
    print("_"*90)

if __name__ == '__main__':
    test()

