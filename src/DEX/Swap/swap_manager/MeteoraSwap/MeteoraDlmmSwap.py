from decimal import Decimal
from typing import TypedDict

####################################
from src.DEX.Swap.swap_manager.OriginSwap.TraderJoeSwap import TraderJoeSwap, PoolSwap
from src.DEX.Swap.math_.MeteoraMath.MeteoraDlmmMath import MeteoraDlmmMath
from src.DEX.DEXes.Meteora.MeteoraTypingDict import MeteoraDlmm, MeteoraLbPair
####################################

class MeteoraDlmmSwapTD(TypedDict):
    pool_state: MeteoraDlmm
    metadata: dict
    delta_amount: Decimal
    x_to_y: bool
    amount_specified_is_input: bool

class MeteoraDlmmSwap(TraderJoeSwap):
    meteora_dlmm_math = MeteoraDlmmMath()
    meteora_dlmm_swap_params = MeteoraDlmmSwapTD

    def get_fee(self, **kwargs) -> Decimal:
        """
        Should be without percentage.
        :param kwargs: There always will be 'crossed_bins: int', 'current_time: Decimal', 'current_id',
         and 'start_active_id'
        :return: 0.03 % -> 0.0003
        """

        LbPair: MeteoraLbPair = kwargs['LbPair']
        crossed_bins = kwargs['crossed_bins']
        current_time = kwargs['current_time']
        start_active_id = kwargs['start_active_id']

        dlmm_fee_params = self.meteora_dlmm_math.dlmm_fee_params(
            LbPair=LbPair,
            crossed_bins=crossed_bins,
            current_time=current_time,
            start_active_id=start_active_id
        )

        return self.meteora_dlmm_math.get_fee(dlmm_fee_params)

    def meteora_dlmm_swap(self, params: MeteoraDlmmSwapTD) -> PoolSwap:
        PoolState = params['pool_state']
        delta_amount = params['delta_amount']
        x_to_y = params['x_to_y']
        amount_specified_is_input = params['amount_specified_is_input']

        LbPair = PoolState['LbPair']
        bins = PoolState['bins']
        bin_step = Decimal(str(LbPair['bin_step']))
        active_id = Decimal(str(LbPair['active_id']))
        P = self.ultimate_math.get_price_from_id(active_id, bin_step)


        fee_kwargs = {
            'LbPair': LbPair
        }

        swap_params = self.SwapScheme(
            amount_remaining=delta_amount,
            bin_step=bin_step,
            P=P,
            active_id=active_id,
            bins=bins,
            x_to_y=x_to_y,
            amount_specified_is_input=amount_specified_is_input,
            fee_kwarg=fee_kwargs
        )
        return self.swap(swap_params)