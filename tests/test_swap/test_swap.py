from src.DEX.Swap import Swap, SwapParamsTD
import redis
import json
from src.Config import config
from src import WhirlpoolClmmScheme
from src.DataFetcher.api_clients.Orca.OrcaMetadataScheme import OrcaMetadataScheme
from decimal import Decimal
import time


def test_orca_clmm():
    r = redis.Redis()

    market = 'orca'
    version = 'clmm'
    pool = 'DehSVMLfV4fjyn9JAfgvDbT9kE2t97WnGJTXFnk7EkQx'
    x_decimal = 6
    y_decimal = 6

    current_state = json.loads(r.get(config.POOLS_CURRENT_STATE_DICT_REDIS_KEY % (market, version)))
    metadata = json.loads(r.get(config.REDIS_METADATA_KEY % (market, version)))
    swap = Swap()

    target_pool_metadata = OrcaMetadataScheme(**metadata.get(pool))
    target_pool_state = WhirlpoolClmmScheme(**current_state.get(pool))


    params_test_1 = swap.swap_params(
        pool_state=target_pool_state.model_dump(),
        metadata=target_pool_metadata.model_dump(),
        delta_amount=Decimal(str(60600 * 10 ** y_decimal)),
        x_to_y=False,
        amount_specified_is_input=True
    )

    print(target_pool_state.model_dump())
    print(target_pool_metadata.model_dump())
    start_time = time.time()
    res_test_1 = swap.swap(params=params_test_1, dex='orca', version='clmm')
    print(f"Time: {time.time() - start_time}")
    print(f"TEST 1: {params_test_1} \n"
          f"RESULT 1: {res_test_1} \n")
    print(f"Output: {res_test_1['result'] / 10 ** x_decimal}")
    print("_"*90)

    params_test_2 = swap.swap_params(
        pool_state=target_pool_state.model_dump(),
        metadata=target_pool_metadata.model_dump(),
        delta_amount=res_test_1['result'],
        x_to_y=False,
        amount_specified_is_input=False
    )
    res_test_2 = swap.swap(params=params_test_2, dex='orca', version='clmm')
    print(f"TEST 2: {params_test_2} \n"
          f"RESULT 2: {res_test_2} \n")
    print(f"Output: {res_test_2['result'] / 10 ** x_decimal}")
    print("_"*90)

if __name__ == '__main__':
    test_orca_clmm()