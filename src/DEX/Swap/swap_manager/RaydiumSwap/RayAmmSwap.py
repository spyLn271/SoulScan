from decimal import Decimal
from typing import TypedDict


####################################
from src.DEX.Swap.swap_manager.OriginSwap.UniswapV2Swap import UniswapV2Swap, PoolSwap
from src.DEX.DEXes.Raydium.RaydiumTypingDict import RaydiumHybridAmm
from src.DataFetcher.api_clients.Raydium.RaydiumMetadataTypingDict import RaydiumMetadata
####################################

class RayAmmSwapTD(TypedDict):
    pool_state: RaydiumHybridAmm
    metadata: RaydiumMetadata
    delta_amount: Decimal
    x_to_y: bool
    amount_specified_is_input: bool

class RayAmmSwap(UniswapV2Swap):
    raydium_swap_params = RayAmmSwapTD

    def get_fee(self, **kwargs) -> Decimal:
        """
        Should be without percentage.
        :param kwargs: There always will be 'crossed_tick: int' and 'current_time: Decimal'
        :return: 0.03 % -> 0.0003
        """
        metadat: RaydiumMetadata = kwargs['metadata']
        return Decimal(str(metadat['feeRate']))

    def raydium_amm_swap(self, params: RayAmmSwapTD) -> PoolSwap:
        state: RaydiumHybridAmm = params['pool_state']
        delta_amount: Decimal = params['delta_amount']
        x_to_y: bool = params['x_to_y']
        amount_specified_is_input: bool = params['amount_specified_is_input']

        swap_params = self.SwapTD(
            reserves_x=Decimal(str(state['baseVault']['amount'])),
            reserves_y=Decimal(str(state['quoteVault']['amount'])),
            delta_token=delta_amount,
            x_to_y=x_to_y,
            amount_specified_is_input=amount_specified_is_input,
            fee_kwarg={'metadata': params['metadata']}
        )
        return self.swap(swap_params)


def test():
    import redis
    import json
    from src.Config import config
    from src import RaydiumHybridAmmScheme
    from src.DataFetcher.api_clients.Raydium.RaydiumMetadataScheme import RaydiumMetadataScheme
    import time

    r = redis.Redis()

    market = 'raydium'
    version = 'amm'
    pool_address = '9nxAnMD7K78a9RMd2L3w8kQT5u9i7gsvV5aHiZ78sCC2'
    x_decimal = 9
    y_decimal = 9

    state = json.loads(r.get(config.POOLS_CURRENT_STATE_DICT_REDIS_KEY % (market, version)))
    metadata = json.loads(r.get(config.REDIS_METADATA_KEY % (market, version)))

    target_pool_state = RaydiumHybridAmmScheme(**state.get(pool_address))
    target_pool_metadata = RaydiumMetadataScheme(**metadata.get(pool_address))

    swapV2 = RayAmmSwap()

    params_test_1 = swapV2.raydium_swap_params(
        pool_state=target_pool_state.model_dump(),
        metadata=target_pool_metadata.model_dump(),
        delta_amount=Decimal(str(10000 * 10 ** y_decimal)),
        x_to_y=True,
        amount_specified_is_input=False)
    res_test_1 = swapV2.raydium_amm_swap(params_test_1)
    print(f"TEST 1: {params_test_1} \n"
          f"RESULT 1: {res_test_1} \n")
    print(f"Output: {res_test_1['result'] / 10 ** x_decimal}")
    print("_"*90)


if __name__ == '__main__':
    test()