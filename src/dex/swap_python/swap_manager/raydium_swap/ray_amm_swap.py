from decimal import Decimal
from typing import TypedDict


####################################
from src.dex.swap_python.swap_manager.origin_swap.uniswap_v2_swap import UniswapV2Swap, PoolSwap
from src.dex.solana.raydium.state.raydium_typing_dict import RaydiumHybridAmm
from src.dex.solana.raydium.metadata.raydium_metadata_tp import RaydiumMetadata
####################################

class RayAmmSwapTD(TypedDict):
    pool_state: RaydiumHybridAmm
    metadata: RaydiumMetadata
    delta_amount: Decimal
    x_to_y: bool
    amount_specified_is_input: bool

class RayAmmSwap(UniswapV2Swap):
    raydium_swap_params = RayAmmSwapTD

    def get_fee(self, **kwargs) -> Decimal:
        """
        Should be without percentage.
        :param kwargs: There always will be 'crossed_tick: int' and 'current_time: Decimal'
        :return: 0.03 % -> 0.0003
        """
        metadat: RaydiumMetadata = kwargs['metadata']
        return Decimal(str(metadat['feeRate']))

    def raydium_amm_swap(self, params: RayAmmSwapTD) -> PoolSwap:
        state: RaydiumHybridAmm = params['pool_state']
        delta_amount: Decimal = params['delta_amount']
        x_to_y: bool = params['x_to_y']
        amount_specified_is_input: bool = params['amount_specified_is_input']

        swap_params = self.SwapScheme(
            reserves_x=Decimal(str(state['baseVault']['amount'])),
            reserves_y=Decimal(str(state['quoteVault']['amount'])),
            delta_token=delta_amount,
            x_to_y=x_to_y,
            amount_specified_is_input=amount_specified_is_input,
            fee_kwarg={'metadata': params['metadata']}
        )
        return self.swap(swap_params)