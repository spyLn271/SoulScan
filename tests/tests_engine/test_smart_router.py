


def test_raydium_route():
    from src.SoulEngine.SmartRouter.MathSmartRouter import MathSmartRouter
    from src.Config import config
    import redis
    import json
    import time

    math_router = MathSmartRouter()
    r = redis.Redis()

    metadata = json.loads(r.get(config.REDIS_METADATA_KEY % ('raydium', 'clmm')))
    state = json.loads(r.get(config.POOLS_CURRENT_STATE_DICT_REDIS_KEY % ('raydium', 'clmm')))

    raydium_SOL_USD1_route_1 = ['3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv', 'BCDdHonby65iduz3Ev3c9v5XjNkzyu5e56KRFHpBM4T9']
    raydium_SOL_USD1_route_2 = ['AQAGYQsdU853WAKhXM79CgNdoyhrRwXvYHX6qrDyC1FS']

    SOL_mint = 'So11111111111111111111111111111111111111112'
    USD1_mint = 'USD1ttGY1N17NEEHLmELoaybftRBUSErhqYiQzvEmuB'

    delta_amount = 300 * 10 ** 9
    amount_specified_is_input = True

    start_time = time.time()
    smart_swap_result_1 = math_router.smart_swap(
        route=raydium_SOL_USD1_route_1,
        base_mint=SOL_mint,
        quote_mint=USD1_mint,
        delta_amount=delta_amount,
        amount_specified_is_input=amount_specified_is_input,
        metadata=metadata,
        state=state
    )
    print(f"Time: {time.time() - start_time}")
    print(smart_swap_result_1)

    start_time = time.time()
    smart_swap_result_2 = math_router.smart_swap(
        route=raydium_SOL_USD1_route_2,
        base_mint=SOL_mint,
        quote_mint=USD1_mint,
        delta_amount=delta_amount,
        amount_specified_is_input=amount_specified_is_input,
        metadata=metadata,
        state=state
    )
    print(f"Time: {time.time() - start_time}")
    print(smart_swap_result_2)

def test_OSRV1():
    from src.SoulEngine.SmartRouter.OnlineSmartRouter import (OnlineSmartRouterEngineV1,
                                                              get_active_state,
                                                              get_active_metadata,
                                                              create_graph,
                                                              OnlineSmartRouter,
                                                              OnlineSmartRouterConfigScheme)
    from src.Config import config, Bases
    import redis
    import json
    import time
    from src.SoulEngine.SmartRouter.MathSmartRouter import MathSmartRouter
    from src.DEX.Swap import Swap, SwapParamsTD
    import logging

    r = redis.Redis(decode_responses=True)
    metadata = get_active_metadata(r)
    state = get_active_state(r)



    target_mint = ['NUZ3FDWTtN5SP72BsefbsqpnbAY5oe21LE8bCSkqsEK',
                   '5U24oSxbCDiVEpbXYwZ2sF7sd6TUHs93u56WsR9bonk',
                   'vEHiuRmd8WvCkswH8Xy4VXTEMXA7JScik47XZkDbonk',
                   '6S8PhTWWmnAEfFWxoMJhRk9BVbvaztAr4uYrX6Zq2y8s',
                   'BUF3TvvZfCMMWaPZJMTGm5WWVmi2arQ9Swze4CPEbonk',
                   '7ZCm8WBN9aLa3o47SoYctU6iLdj7wkGG5SV2hE5CgtD5',
                   '87B6mb9KBjaF5NHrB3H33f7grdUHi4oWmMErjhZ5bonk',
                   '8Aq4fWMgPqJbF3w8w8PnLDRVUAFe4mzsCvPKxAArbonk',
                   '8oRpiDdQhLTV2SmscjKp4SWdZ9as2C3kZdTj4qVvbonk',
                   '3ThdFZQKM6kRyVGLG48kaPg5TRMhYMKY1iCRa9xop1WC',
                   'WFRGSWjaz8tbAxsJitmbfRuFV2mSNwy7BMWcCwaA28U',
                   '7zaerpu4De3Aob5TJwqXQoit72S2woTEfsbGWP95bonk',
                   '36Q5RuwiXbLxvRHvCjkKQxEpWmmoVUEM8dYQT2Wcbonk',
                   '3XzjXPicZSejBK7nRJbJjEjh4oQdVDLaP8J4u2CaqmxK',
                   '7kkSNPgZi6DqiAeyRZSoGmMtPfUckKQVatStt6fabonk',
                   '3wPQhXYqy861Nhoc4bahtpf7G3e89XCLfZ67ptEfZUSA',
                   'BFxTqBjHbNSQoWeSirXP3Szf7gMJT2dCXddfNzZ1bonk',
                   'DVb1znJKBVJzcuzbgvcG3cSghf2i1YzdJqoJFb7ZdQuX',
                   'JDt9rRGaieF6aN1cJkXFeUmsy7ZE4yY3CZb8tVMXVroS',
                   'DriFtupJYLTosbwoN8koMbEYSx54aFAVLddWsbksjwg7',
                   '758yZPp2QEmrMgMACiUS2K2sTLsfSw9NprWoGxdxbonk',
                   'E7geR74zbneUJFYSNrZQppsX2TVbi84G8aXw5dpCbonk',
                   '5n5ah88Za1M9MVo51YAQWSkpNdz2S3RDvGeTApmM5Qpv',
                   'A8vZhzWsLosrTnseSRcThSkBuZqinYs3Q3SwQeoyQFBH',
                   'iMm4Yc8Lha88up8wMnrR5DHQe34hXGnfixnhMTvbonk',
                   '6KUvHeiDhXxWJGBjg4f3gMt4N9juvmytrs1SMwZAbonk',
                   'AidQVWaKa6tJSBHzDGxQ7QmuxYQ79R3CwCrbWoT8bonk',
                   'ENkcaFPHRJFXqV7MHsaqXGyKCuV5CS6h5SnvyfTjbonk',
                   'AzVCECC5zr21ikYQne4Xtoh3SVg848duPHUHb3M7bonk',
                   'GCHR3KpJKhRx2SFPn5PmhRf8Lc4G67L1DwMZQZqEbonk',
                   'Ch87t1PM7vYeiHAz2pjbw646pNLSFSzGtfMQWeGNbonk',
                   'METADDFL6wWMWEoKTFJwcThTbUmtarRJZjRpzUvkxhr',
                   '9xbhrLumH11DJ3WK9uNTn95Mmp29BVWsFCGKzEzqbonk']

    # for pool, data in metadata.items():
    #     mint0 = data['mint0']
    #     mint1 = data['mint1']
    #     if mint0 in target_mint:
    #         print(f'{mint0} in {pool}')
    #     elif mint1 in target_mint:
    #         print(f'{mint1} in {pool}')

    # target_pool = '6keoGHNmqDgLm6Cn27i2SWXzAr2N2U92mr5E6jibcaDE'
    # market = 'meteora'
    # version = 'dlmm'
    # metadata = metadata[target_pool]
    # state = state[target_pool]
    # x_decimals = 9
    # y_decimals = 6
    #
    # swap_params = SwapParamsTD(
    #     metadata=metadata,
    #     pool_state=state,
    #     amount_specified_is_input=True,
    #     x_to_y=True,
    #     delta_amount=10 * 10 ** x_decimals
    # )
    # swap = Swap()
    # res = swap.swap(dex=market, version=version, params=swap_params)
    # print(res)

    conf = OnlineSmartRouterConfigScheme()
    osr = OnlineSmartRouter(conf)
    osr.start()


def check_osr():
    import redis
    from src.Config import config, Bases
    import json

    r = redis.Redis(decode_responses=True)
    all_path_unsterilized = r.hgetall(config.REDIS_KEY_COLD_PATH)

    all_path_sterilized = {}
    not_found = 0
    not_founded_token = []
    for quote, value in all_path_unsterilized.items():
        all_path_sterilized[quote] = json.loads(value)

        if all_path_sterilized[quote].get('routes') == []:
            base, quote = quote.split('/')
            not_founded_token.append(base)
            not_found += 1


    print(f"Not found: {not_found}")
    print(json.dumps(all_path_sterilized, indent=4))

def get_pools_with_mint(mint_list):
    from src.SoulEngine.SmartRouter.OnlineSmartRouter import (OnlineSmartRouterEngineV1,
                                                              get_active_state,
                                                              get_active_metadata,
                                                              create_graph,
                                                              OnlineSmartRouter,
                                                              OnlineSmartRouterConfigScheme)

    import redis
    from src.Config import config, Bases
    import json

    r = redis.Redis(decode_responses=True)
    metadata = get_active_metadata(r)
    state = get_active_state(r)

    pools_with_mint = {}
    for pool, data in metadata.items():
        mint0 = data['mint0']
        mint1 = data['mint1']
        if mint0 in mint_list:
            bar = pools_with_mint.setdefault(mint0, {})
            bar[pool] = data
        elif mint1 in mint_list:
            bar = pools_with_mint.setdefault(mint1, {})
            bar[pool] = data

    print(json.dumps(pools_with_mint, indent=4))






if __name__ == '__main__':
    test_OSRV1()

