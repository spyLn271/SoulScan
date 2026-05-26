from decimal import Decimal
from typing import TypedDict


####################################
from src.dex.swap_python.swap_manager.origin_swap.uniswap_v3_swap import UltimateUniswapV3Swap, PoolSwap
from src.dex.evm.type_dict import SlotDict
from src.settings.basic_schemes import Tick
from src.dex.evm.data_fetcher.metadata.coingecko_fetcher import MetadataDict
####################################

class UniV3State(TypedDict):
    slot: SlotDict
    ticks: dict[str, Tick]



class UniV3SwapTD(TypedDict):
    pool_state: UniV3State
    metadata: MetadataDict
    delta_amount: Decimal
    x_to_y: bool
    amount_specified_is_input: bool



class UniV3Swap(UltimateUniswapV3Swap):
    uniswap_swap_params = UniV3SwapTD

    def get_fee(self, **kwargs) -> Decimal:
        """
        Should be without percentage.
        :param kwargs: There always will be 'crossed_tick: int', 'current_time: Decimal', 'current_tick'
        and 'start_current_tick_group'
        :return: 0.03 % -> 0.0003
        """
        metadata: MetadataDict = kwargs['metadata']
        return Decimal(str(metadata['fee_rate'] / 1_000_000))


    def uniswap_v3_swap(self, params: UniV3SwapTD) -> PoolSwap:
        state: UniV3State = params['pool_state']
        delta_amount: Decimal = params['delta_amount']
        x_to_y: bool = params['x_to_y']
        amount_specified_is_input: bool = params['amount_specified_is_input']
        metadata: MetadataDict = params['metadata']

        swap_params = self.SwapScheme(
            amount_remaining=delta_amount,
            current_tick=Decimal(str(state["slot"]["tick_current"])),
            tick_spacing=Decimal(str(metadata["tick_spacing"])),
            unnormalized_sqrt_P_start=Decimal(str(int(state["slot"]["sqrt_price_x96"], 2))),
            factor=Decimal("96"),
            L=Decimal(str(state["slot"]["liquidity"])),
            x_to_y=x_to_y,
            amount_specified_is_input=amount_specified_is_input,
            fee_kwarg={'metadata': metadata},
            ticks=state['ticks']
        )


        return self.swap(swap_params)



