from decimal import Decimal
from typing import TypedDict


####################################
from src.DEX.Swap.swap_manager.OriginSwap.UniswapV2Swap import UniswapV2Swap, PoolSwap
from src.DEX.DEXes.Raydium.RaydiumTypingDict import RaydiumHybridAmm
from src.DataFetcher.api_clients.Raydium.RaydiumMetadataTypingDict import RaydiumMetadata
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

        swap_params = self.SwapTD(
            reserves_x=Decimal(str(state['baseVault']['amount'])),
            reserves_y=Decimal(str(state['quoteVault']['amount'])),
            delta_token=delta_amount,
            x_to_y=x_to_y,
            amount_specified_is_input=amount_specified_is_input,
            fee_kwarg={'metadata': params['metadata']}
        )
        return self.swap(swap_params)