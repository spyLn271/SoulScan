from decimal import Decimal
from typing import TypedDict

####################################
from src.DEX.Swap.swap_manager.OriginSwap.TraderJoeSwap import TraderJoeSwap, PoolSwap
from src.DEX.Swap.math_.MeteoraMath.MeteoraDlmmMath import MeteoraDlmmMath
from src.DEX.DEXes.Meteora.MeteoraTypingDict import MeteoraDlmm, MeteoraLbPair
####################################

class MeteoraDlmmSwapTD(TypedDict):
    pool_state: MeteoraDlmm
    metadata: dict
    delta_amount: Decimal
    x_to_y: bool
    amount_specified_is_input: bool

class MeteoraDlmmSwap(TraderJoeSwap):
    meteora_dlmm_math = MeteoraDlmmMath()
    meteora_dlmm_swap_params = MeteoraDlmmSwapTD

    def get_fee(self, **kwargs) -> Decimal:
        """
        Should be without percentage.
        :param kwargs: There always will be 'crossed_bins: int', 'current_time: Decimal', 'current_id',
         and 'start_active_id'
        :return: 0.03 % -> 0.0003
        """

        LbPair: MeteoraLbPair = kwargs['LbPair']
        crossed_bins = kwargs['crossed_bins']
        current_time = kwargs['current_time']
        start_active_id = kwargs['start_active_id']

        dlmm_swap_params = self.meteora_dlmm_math.dlmm_swap_params(
            LbPair=LbPair,
            crossed_bins=crossed_bins,
            current_time=current_time,
            start_active_id=start_active_id
        )

        return self.meteora_dlmm_math.get_fee(dlmm_swap_params)

    def meteora_dlmm_swap(self, params: MeteoraDlmmSwapTD) -> PoolSwap:
        PoolState = params['pool_state']
        delta_amount = params['delta_amount']
        x_to_y = params['x_to_y']
        amount_specified_is_input = params['amount_specified_is_input']

        LbPair = PoolState['LbPair']
        bins = PoolState['bins']
        bin_step = Decimal(str(LbPair['bin_step']))
        active_id = Decimal(str(LbPair['active_id']))
        P = self.ultimate_math.get_price_from_id(active_id, bin_step)


        fee_kwargs = {
            'LbPair': LbPair
        }

        swap_params = self.SwapTD(
            amount_remaining=delta_amount,
            bin_step=bin_step,
            P=P,
            active_id=active_id,
            bins=bins,
            x_to_y=x_to_y,
            amount_specified_is_input=amount_specified_is_input,
            fee_kwarg=fee_kwargs
        )
        return self.swap(swap_params)


def test():
    import redis
    import json
    from src.Config import config
    from src import MeteoraDlmmScheme
    from src.DataFetcher.api_clients.Meteora.MeteoraMetadataScheme import MeteoraDlmmMetadataScheme

    r = redis.Redis()
    meteoraSwap = MeteoraDlmmSwap()

    market = 'meteora'
    version = 'dlmm'
    pool_address = '9d9mb8kooFfaD3SctgZtkxQypkshx6ezhbKio89ixyy2'

    x_decimal = 6
    y_decimal = 6


    metadata = json.loads(r.get(config.REDIS_METADATA_KEY % (market, version)))
    state = json.loads(r.get(config.POOLS_CURRENT_STATE_DICT_REDIS_KEY % (market, version)))

    target_pool_state = MeteoraDlmmScheme(**state.get(pool_address))
    target_pool_metadata = MeteoraDlmmMetadataScheme(**metadata.get(pool_address))

    prams_test_1 = meteoraSwap.meteora_dlmm_swap_params(
        pool_state=target_pool_state.model_dump(),
        metadata={},
        delta_amount=Decimal(str(29375 * 10 ** x_decimal)),
        x_to_y=True,
        amount_specified_is_input=True
    )
    res_test_1 = meteoraSwap.meteora_dlmm_swap(prams_test_1)
    print(f"TEST 1: {prams_test_1} \n"
          f"RESULT 1: {res_test_1} \n")
    print(f"Output: {res_test_1['result'] / 10 ** y_decimal}")
    print("_"*90)

    params_test_2 = meteoraSwap.meteora_dlmm_swap_params(
        pool_state=target_pool_state.model_dump(),
        metadata={},
        delta_amount=res_test_1["result"],
        x_to_y=True,
        amount_specified_is_input=False
    )
    res_test_2 = meteoraSwap.meteora_dlmm_swap(params_test_2)
    print(f"TEST 2: {params_test_2} \n"
          f"RESULT 2: {res_test_2} \n")
    print(f"Output: {res_test_2['result'] / 10 ** x_decimal}")
    print("_"*90)


    params_test_3 = meteoraSwap.meteora_dlmm_swap_params(
        pool_state=target_pool_state.model_dump(),
        metadata={},
        delta_amount=Decimal(str(129080 * 10 ** y_decimal)),
        x_to_y=False,
        amount_specified_is_input=True
    )
    res_test_3 = meteoraSwap.meteora_dlmm_swap(params_test_3)
    print(f"TEST 3: {params_test_3} \n"
          f"RESULT 3: {res_test_3} \n")
    print(f"Output: {res_test_3['result'] / 10 ** x_decimal}")
    print("_"*90)


    params_test_4 = meteoraSwap.meteora_dlmm_swap_params(
        pool_state=target_pool_state.model_dump(),
        metadata={},
        delta_amount=res_test_3["result"],
        x_to_y=False,
        amount_specified_is_input=False
    )
    res_test_4 = meteoraSwap.meteora_dlmm_swap(params_test_4)
    print(f"TEST 4: {params_test_4} \n"
          f"RESULT 4: {res_test_4} \n")
    print(f"Output: {res_test_4['result'] / 10 ** y_decimal}")
    print("_"*90)


if __name__ == '__main__':
    test()