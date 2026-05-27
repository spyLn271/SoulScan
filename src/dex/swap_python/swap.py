from typing import TypedDict
from decimal import Decimal

####################################
from src.dex.swap_python import swap_manager
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
    uniswap_v3 = swap_manager.UniV3Swap()
    uniswap_v2 = swap_manager.UniV2Swap()


    def swap(self, dex: str, version: str, params: SwapParamsTD) -> swap_manager.PoolSwap:
        if dex.lower() == 'orca' and version.lower() == 'clmm':
            orca_params = swap_manager.OrcaClmmSwapTD(**params)
            return self.orca_clmm.orca_clmm_swap(orca_params)
        elif dex.lower() == 'raydium' and version.lower() == 'clmm':
            rayclmm_params = swap_manager.RayClmmSwapTD(**params)
            return self.raydium_clmm.raydium_clmm_swap(rayclmm_params)
        elif dex.lower() == 'raydium' and version.lower() == 'amm':
            rayamm_params = swap_manager.RayAmmSwapTD(**params)
            return self.raydium_amm.raydium_amm_swap(rayamm_params)
        elif dex.lower() == 'meteora' and version.lower() == 'dlmm':
            meteora_dlmm_params = swap_manager.MeteoraDlmmSwapTD(**params)
            return self.meteora_dlmm.meteora_dlmm_swap(meteora_dlmm_params)
        elif (dex.lower() == 'uniswap' or dex.lower() == 'pancakeswap' or dex.lower() == 'sushiswap') and (version.lower() == 'v3' or version.lower() == 'v4'):
            uniswap_v3_swap_params = swap_manager.UniV3SwapTD(**params)
            return self.uniswap_v3.uniswap_v3_swap(uniswap_v3_swap_params)
        elif (dex.lower() == 'uniswap' or dex.lower() == 'pancakeswap' or dex.lower() == 'sushiswap') and version.lower() == 'v2':
            uniswap_v2_swap_params = swap_manager.UniV2SwapTD(**params)
            return self.uniswap_v2.uniswap_v2_swap(uniswap_v2_swap_params)
        else:
            raise Exception(f"Market {dex}_{version} is not supported.")