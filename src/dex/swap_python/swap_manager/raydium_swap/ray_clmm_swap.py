from decimal import Decimal
from typing import TypedDict


####################################
from src.dex.swap_python.swap_manager.origin_swap.uniswap_v3_swap import UltimateUniswapV3Swap, PoolSwap
from src.dex.solana.raydium.state.raydium_typing_dict import RaydiumClmm
from src.dex.solana.raydium.metadata.raydium_metadata_tp import RaydiumMetadata
####################################

class RayClmmSwapTD(TypedDict):
    pool_state: RaydiumClmm
    metadata: RaydiumMetadata
    delta_amount: Decimal
    x_to_y: bool
    amount_specified_is_input: bool

class RayClmmSwap(UltimateUniswapV3Swap):
    raydium_swap_params = RayClmmSwapTD

    def get_fee(self, **kwargs) -> Decimal:
        """
        Should be without percentage.
        :param kwargs: There always will be 'crossed_tick: int', 'current_time: Decimal', 'current_tick'
        and 'start_current_tick_group'
        :return: 0.03 % -> 0.0003
        """
        metadata: RaydiumMetadata = kwargs['metadata']
        return Decimal(str(metadata['feeRate']))

    def raydium_clmm_swap(self, params: RayClmmSwapTD) -> PoolSwap:
        state: RaydiumClmm = params['pool_state']
        delta_amount: Decimal = params['delta_amount']
        x_to_y: bool = params['x_to_y']
        amount_specified_is_input: bool = params['amount_specified_is_input']

        swap_params = self.SwapScheme(
            amount_remaining=delta_amount,
            current_tick=Decimal(str(state['PoolState']['tick_current'])),
            tick_spacing=Decimal(str(state['PoolState']['tick_spacing'])),
            unnormalized_sqrt_P_start=Decimal(str(state['PoolState']['sqrt_price_x64'])),
            factor=Decimal("64"),
            L=Decimal(str(state['PoolState']['liquidity'])),
            x_to_y=x_to_y,
            amount_specified_is_input=amount_specified_is_input,
            ticks=state['ticks'],
            fee_kwarg={'metadata': params['metadata']}
        )
        return self.swap(swap_params)