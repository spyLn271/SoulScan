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