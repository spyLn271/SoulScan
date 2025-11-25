from src.DEX.Swap.swap_manager.OrcaSwap.OrcaClmmSwap import OrcaClmmSwap
from decimal import Decimal
import redis
import json
from src.Config import config
from src import WhirlpoolClmmScheme
from src.DataFetcher.api_clients.Orca.OrcaMetadataScheme import OrcaMetadataScheme
import time


def test():
    r = redis.Redis()

    market = 'orca'
    version = 'clmm'
    pool = 'DehSVMLfV4fjyn9JAfgvDbT9kE2t97WnGJTXFnk7EkQx'
    x_decimal = 6
    y_decimal = 6

    current_state = json.loads(r.get(config.POOLS_CURRENT_STATE_DICT_REDIS_KEY % (market, version)))
    metadata = json.loads(r.get(config.REDIS_METADATA_KEY % (market, version)))
    swapV3 = OrcaClmmSwap()

    target_pool_metadata = OrcaMetadataScheme(**metadata.get(pool))
    target_pool_state = WhirlpoolClmmScheme(**current_state.get(pool))


    # params_test_1 = swapV3.orca_swap_params(
    #     pool_state=target_pool_state.model_dump(),
    #     metadata=target_pool_metadata.model_dump(),
    #     delta_amount=Decimal(str(192385 * 10 ** y_decimal)),
    #     x_to_y=False,
    #     amount_specified_is_input=True
    # )
    #
    # print(target_pool_state.model_dump())
    # print(target_pool_metadata.model_dump())
    # start_time = time.time()
    # res_test_1 = swapV3.orca_clmm_swap(params_test_1)
    # print(f"Time: {time.time() - start_time}")
    # print(f"TEST 1: {params_test_1} \n"
    #       f"RESULT 1: {res_test_1} \n")
    # print(f"Output: {res_test_1['result'] / 10 ** x_decimal}")
    # print("_"*90)
    #
    # params_test_2 = swapV3.orca_swap_params(
    #     pool_state=target_pool_state.model_dump(),
    #     metadata=target_pool_metadata.model_dump(),
    #     delta_amount=res_test_1['result'],
    #     x_to_y=False,
    #     amount_specified_is_input=False
    # )
    # res_test_2 = swapV3.orca_clmm_swap(params_test_2)
    # print(f"TEST 2: {params_test_2} \n"
    #       f"RESULT 2: {res_test_2} \n")
    # print(f"Output: {res_test_2['result'] / 10 ** x_decimal}")
    # print("_"*90)

    params_test_3 = swapV3.orca_swap_params(
        pool_state=target_pool_state.model_dump(),
        metadata=target_pool_metadata.model_dump(),
        delta_amount=Decimal(str(213523 * 10 ** x_decimal)),
        x_to_y=True,
        amount_specified_is_input=True
    )
    res_test_3 = swapV3.orca_clmm_swap(params_test_3)
    print(f"TEST 3: {params_test_3} \n"
          f"RESULT 3: {res_test_3} \n")
    print(f"Output: {res_test_3['result'] / 10 ** y_decimal}")
    print("_"*90)

    # params_test_4 = swapV3.orca_swap_params(
    #     pool_state=target_pool_state.model_dump(),
    #     metadata=target_pool_metadata.model_dump(),
    #     delta_amount=res_test_3['result'],
    #     x_to_y=True,
    #     amount_specified_is_input=False
    # )
    # res_test_4 = swapV3.orca_clmm_swap(params_test_4)
    # print(f"TEST 4: {params_test_4} \n"
    #       f"RESULT 4: {res_test_4} \n")
    # print(f"Output: {res_test_4['result'] / 10 ** x_decimal}")



if __name__ == '__main__':
    test()