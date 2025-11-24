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