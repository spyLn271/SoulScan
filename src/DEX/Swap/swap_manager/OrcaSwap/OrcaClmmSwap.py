from decimal import Decimal
from typing import TypedDict


####################################
from src.DEX.Swap.swap_manager.OriginSwap.UniswapV3Swap import UltimateUniswapV3Swap, PoolSwap
from src.DEX.Swap.math_.OrcaMath.OrcaClmmMath import OrcaClmmMath
from src.DEX.DEXes.Orca.OrcaTypingDict import WhirlpoolClmm
from src.DataFetcher.api_clients.Orca.OrcaMetadataTypingDict import OrcaMetadata
####################################


class OrcaClmmSwapTD(TypedDict):
    pool_state: WhirlpoolClmm
    metadata: OrcaMetadata
    delta_amount: Decimal
    x_to_y: bool
    amount_specified_is_input: bool

class OrcaClmmSwap(UltimateUniswapV3Swap):
    orca_math = OrcaClmmMath()
    orca_swap_params = OrcaClmmSwapTD

    def get_fee(self, **kwargs) -> Decimal:
        """
        Should be without percentage.
        :param kwargs: There always will be 'crossed_tick: int', 'current_time: Decimal', 'current_tick'
        and 'start_current_tick_group'
        :return: 0.03 % -> 0.0003
        """
        oracle = kwargs.get("oracle")
        crossed_tick = kwargs["crossed_tick"]
        current_time = kwargs["current_time"]
        start_current_tick_group = kwargs["start_current_tick_group"]
        feeRate = kwargs["feeRate"]

        return self.orca_math.get_fee(self.orca_math.orca_fee_params(
            fee_base=feeRate,
            oracle=oracle,
            crossed_tick=crossed_tick,
            current_time=current_time,
            start_current_tick_group=start_current_tick_group
        ))

    def orca_clmm_swap(self, params: OrcaClmmSwapTD) -> PoolSwap:
        state = params['pool_state']
        metadata = params['metadata']
        delta_amount = params['delta_amount']
        x_to_y = params['x_to_y']
        amount_specified_is_input = params['amount_specified_is_input']

        current_tick = Decimal(str(state['base_info']['tickCurrentIndex']))
        tick_spacing = Decimal(str(state['base_info']['tickSpacing']))
        unnormalized_sqrt_P_start = Decimal(str(state['base_info']['sqrtPrice']))
        factor = Decimal("64")
        L = Decimal(str(state['base_info']['liquidity']))
        x_to_y = x_to_y
        amount_specified_is_input = amount_specified_is_input
        ticks = state['ticks']
        fee_kwarg = {'oracle': state.get('oracle'), 'feeRate': metadata['feeRate']}

        swap_params = self.SwapScheme(
            amount_remaining=delta_amount,
            current_tick=current_tick,
            tick_spacing=tick_spacing,
            unnormalized_sqrt_P_start=unnormalized_sqrt_P_start,
            factor=factor,
            L=L,
            x_to_y=x_to_y,
            amount_specified_is_input=amount_specified_is_input,
            ticks=ticks,
            fee_kwarg=fee_kwarg
        )
        return self.swap(swap_params)