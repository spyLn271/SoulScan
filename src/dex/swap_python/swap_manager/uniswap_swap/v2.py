from decimal import Decimal
from typing import TypedDict


####################################
from src.dex.swap_python.swap_manager.origin_swap.uniswap_v2_swap import UniswapV2Swap, PoolSwap
from src.dex.evm.data_fetcher.metadata.coingecko_fetcher import MetadataDict
####################################

class UniV2State(TypedDict):
    reserve0: int
    reserve1: int

class UniV2SwapTD(TypedDict):
    pool_state: UniV2State
    metadata: MetadataDict
    delta_amount: Decimal
    x_to_y: bool
    amount_specified_is_input: bool


class UniV2Swap(UniswapV2Swap):
    uniswap_swap_params = UniV2SwapTD

    def get_fee(self, **kwargs) -> Decimal:
        """
        Should be without percentage.
        :param kwargs: There always will be 'crossed_tick: int', 'current_time: Decimal', 'current_tick'
        and 'start_current_tick_group'
        :return: 0.03 % -> 0.0003
        """
        metadata: MetadataDict = kwargs['metadata']
        return Decimal(str(metadata['fee_rate'] / 1_000_000))

    def uniswap_v2_swap(self, params: UniV2SwapTD) -> PoolSwap:
        state: UniV2State = params['pool_state']
        delta_amount: Decimal = params['delta_amount']
        x_to_y: bool = params['x_to_y']
        amount_specified_is_input: bool = params['amount_specified_is_input']
        metadata: MetadataDict = params['metadata']


        swap_params = self.SwapScheme(
            reserves_x=Decimal(str(state['reserve0'])),
            reserves_y=Decimal(str(state['reserve1'])),
            delta_token=delta_amount,
            x_to_y=x_to_y,
            amount_specified_is_input=amount_specified_is_input,
            fee_kwarg={'metadata': metadata}
        )
        return self.swap(swap_params)