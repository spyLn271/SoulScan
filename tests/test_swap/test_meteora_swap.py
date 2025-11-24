def test():
    from src.DEX.Swap.swap_manager.MeteoraSwap.MeteoraDlmmSwap import MeteoraDlmmSwap
    from decimal import Decimal
    import redis
    import json
    from src.Config import config
    from src import MeteoraDlmmScheme
    from src.DataFetcher.api_clients.Meteora.MeteoraMetadataScheme import MeteoraDlmmMetadataScheme

    r = redis.Redis()
    meteoraSwap = MeteoraDlmmSwap()

    market = 'meteora'
    version = 'dlmm'
    pool_address = '5SHjDACvwtox5nY8kpWNYyaceWjtTG8C6L821D9Gtpjf'

    x_decimal = 6
    y_decimal = 6


    metadata = json.loads(r.get(config.REDIS_METADATA_KEY % (market, version)))
    state = json.loads(r.get(config.POOLS_CURRENT_STATE_DICT_REDIS_KEY % (market, version)))

    target_pool_state = MeteoraDlmmScheme(**state.get(pool_address))
    target_pool_metadata = MeteoraDlmmMetadataScheme(**metadata.get(pool_address))
    print(target_pool_metadata.model_dump())

    prams_test_1 = meteoraSwap.meteora_dlmm_swap_params(
        pool_state=target_pool_state.model_dump(),
        metadata={},
        delta_amount=Decimal(str(4900 * 10 ** x_decimal)),
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
        delta_amount=Decimal(str(149 * 10 ** y_decimal)),
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