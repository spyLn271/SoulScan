def test_clmm():
    import redis
    import json
    from src.Config import config
    from src import RaydiumClmmScheme
    from src.DataFetcher.api_clients.Raydium.RaydiumMetadataScheme import RaydiumMetadataScheme
    import time
    from src.DEX.Swap.swap_manager.RaydiumSwap.RayClmmSwap import RayClmmSwap
    from decimal import Decimal

    r = redis.Redis()

    market = 'raydium'
    version = 'clmm'
    pool = 'AQAGYQsdU853WAKhXM79CgNdoyhrRwXvYHX6qrDyC1FS'
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
        delta_amount=Decimal(str(909080 * 10 ** y_decimal)),
        x_to_y=False,
        amount_specified_is_input=True
    )
    res_test_1 = swapV3.raydium_clmm_swap(swap_params_test_1)
    print(f"TEST 1: {swap_params_test_1} \n"
          f"RESULT 1: {res_test_1} \n")
    print(f"Output: {res_test_1['result'] / 10 ** x_decimal}")
    print("_"*90)


def test_amm():
    import redis
    import json
    from src.Config import config
    from src import RaydiumHybridAmmScheme
    from src.DataFetcher.api_clients.Raydium.RaydiumMetadataScheme import RaydiumMetadataScheme
    import time
    from src.DEX.Swap.swap_manager.RaydiumSwap.RayAmmSwap import RayAmmSwap
    from decimal import Decimal

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
    test_clmm()

"""
Before: 0.36206730632628861867852373968013068861182546243072, 79472422872020, -20320, -20280, -20220
After: 0.36387333474683045885890895661548806806251790850291, 79474613484042, -20220, -20220, -20160
Before: 0.36387333474683045885890895661548806806251790850291, 79474613484042, -20220, -20220, -20160
After: 0.36496653907840055165145447387241019199378417398298, 79359190604612, -20160, -20160, -20100
Before: 0.36496653907840055165145447387241019199378417398298, 79359190604612, -20160, -20160, -20100
"""