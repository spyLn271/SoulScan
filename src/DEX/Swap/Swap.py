from typing import TypedDict
from decimal import Decimal

####################################
from src.DEX.Swap import swap_manager
from src.Config import config
####################################

class SwapParamsTD(TypedDict):
    pool_state: dict
    metadata: dict
    delta_amount: Decimal
    x_to_y: bool
    amount_specified_is_input: bool

class Swap:
    swap_params = SwapParamsTD

    orca_clmm = swap_manager.OrcaClmmSwap()
    raydium_clmm = swap_manager.RayClmmSwap()
    raydium_amm = swap_manager.RayAmmSwap()
    meteora_dlmm = swap_manager.MeteoraDlmmSwap()


    def swap(self, dex: str, version: str, params: SwapParamsTD) -> swap_manager.PoolSwap:
        if dex == 'orca' and version == 'clmm':
            orca_params = swap_manager.OrcaClmmSwapTD(**params)
            return self.orca_clmm.orca_clmm_swap(orca_params)
        elif dex == 'raydium' and version == 'clmm':
            rayclmm_params = swap_manager.RayClmmSwapTD(**params)
            return self.raydium_clmm.raydium_clmm_swap(rayclmm_params)
        elif dex == 'raydium' and version == 'amm':
            rayamm_params = swap_manager.RayAmmSwapTD(**params)
            return self.raydium_amm.raydium_amm_swap(rayamm_params)
        elif dex == 'meteora' and version == 'dlmm':
            meteora_dlmm_params = swap_manager.MeteoraDlmmSwapTD(**params)
            return self.meteora_dlmm.meteora_dlmm_swap(meteora_dlmm_params)
        else:
            raise Exception(f"Market {dex}_{version} is not supported.")

    @staticmethod
    def get_active_market():
        return config.ACTIVE_MARKETS


def test_swap():
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
    swap = Swap()

    target_pool_metadata = RaydiumMetadataScheme(**metadata.get(pool))
    target_pool_state = RaydiumClmmScheme(**current_state.get(pool))

    swap_params_test_1 = SwapParamsTD(
        pool_state=target_pool_state.model_dump(),
        metadata=target_pool_metadata.model_dump(),
        delta_amount=Decimal(str(1 * 10 ** x_decimal)),
        x_to_y=True,
        amount_specified_is_input=True
    )
    res_test_1 = swap.swap(dex=market, version=version, params=swap_params_test_1)
    print(f"TEST 1: {swap_params_test_1} \n"
          f"RESULT 1: {res_test_1} \n")
    print(f"Output: {res_test_1['result'] / 10 ** y_decimal}")
    print("_"*90)

if __name__ == '__main__':
    test_swap()