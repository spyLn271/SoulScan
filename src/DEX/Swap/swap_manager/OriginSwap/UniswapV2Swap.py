from decimal import Decimal
from typing import TypedDict
import time

####################################
from src.DEX.Swap.math_.OriginMath.UniswapV2Math import UltimateUniswapV2Math
####################################



class UniswapV2SwapTD(TypedDict):
    reserves_x: Decimal
    reserves_y: Decimal
    delta_token: Decimal
    x_to_y: bool
    amount_specified_is_input: bool
    fee_kwarg: dict

class PoolSwap(TypedDict):
    remain: Decimal
    result: Decimal
    fee: Decimal
    message: str


class UniswapV2Swap:
    ultimate_math = UltimateUniswapV2Math()
    SwapTD = UniswapV2SwapTD

    @staticmethod
    def get_fee(**kwargs) -> Decimal:
        """
        Should be without percentage.
        :param kwargs: There always will be 'crossed_tick: int' and 'current_time: Decimal'
        :return: 0.03 % -> 0.0003
        """
        # return Decimal(str(kwargs["feeRate"]))  # for test
        raise Exception("Fee was not implemented yet.")

    def swap(self, params: UniswapV2SwapTD) -> PoolSwap:
        reserves_x = params['reserves_x']
        reserves_y = params['reserves_y']
        delta_token = params['delta_token']
        x_to_y = params['x_to_y']
        amount_specified_is_input = params['amount_specified_is_input']
        fee_kwarg = params['fee_kwarg'] | {"crossed_tick": 0, "current_time": Decimal(int(time.time()))}

        feeRate = self.get_fee(**fee_kwarg)

        amount_calc = delta_token
        if amount_specified_is_input:
            amount_calc = delta_token * (1 - feeRate)

        swap_computation = self.ultimate_math.swap_exact_token({
            "reserves_x": reserves_x,
            "reserves_y": reserves_y,
            "delta_token": amount_calc,
            "x_to_y": x_to_y,
            "amount_specified_is_input": amount_specified_is_input,
        })

        if amount_specified_is_input:
            return PoolSwap(
                remain=Decimal("0"),
                result=swap_computation,
                fee=delta_token - amount_calc,
                message='success'
            )
        else:
            return PoolSwap(
                remain=Decimal("0"),
                result=round(swap_computation / (1-feeRate)),
                fee=round(swap_computation * feeRate),
                message='success'
            )


def test():
    import redis
    import json
    from src.Config import config
    from src import RaydiumHybridAmmScheme
    from src.DataFetcher.api_clients.Raydium.RaydiumMetadataScheme import RaydiumMetadataScheme

    r = redis.Redis()

    swapV2 = UniswapV2Swap()
    market = 'raydium'
    version = 'amm'
    pool_address = '9SxEcmwzHtSZu2jJSpSxuyxweYECvvtykoP3qtEprkvj' # SOL/LION
    x_decimal = 9
    y_decimal = 9

    current_state = json.loads(r.get(config.POOLS_CURRENT_STATE_DICT_REDIS_KEY % (market, version)))
    metadata = json.loads(r.get(config.REDIS_METADATA_KEY % (market, version)))

    target_pool_state = RaydiumHybridAmmScheme(**current_state.get(pool_address))
    target_pool_metadata = RaydiumMetadataScheme(**metadata.get(pool_address))

    params_test_1 = UniswapV2Swap.SwapTD(
        reserves_x=Decimal(str(target_pool_state.baseVault.amount)),
        reserves_y=Decimal(str(target_pool_state.quoteVault.amount)),
        delta_token=183 * 10 ** x_decimal,
        x_to_y=True,
        amount_specified_is_input=True,
        fee_kwarg=target_pool_metadata.model_dump()
    )
    res_test_1 = swapV2.swap(params_test_1)
    print(f"TEST 1: {params_test_1} \n"
          f"RESULT 1: {res_test_1} \n")
    print("_"*90)

    params_test_2 = UniswapV2Swap.SwapTD(
        reserves_x=Decimal(str(target_pool_state.baseVault.amount)),
        reserves_y=Decimal(str(target_pool_state.quoteVault.amount)),
        delta_token=res_test_1['result'],
        x_to_y=True,
        amount_specified_is_input=False,
        fee_kwarg=target_pool_metadata.model_dump()
    )
    res_test_2 = swapV2.swap(params_test_2)
    print(f"TEST 2: {params_test_2} \n"
          f"RESULT 2: {res_test_2} \n")
    print("_"*90)

    params_test_3 = UniswapV2Swap.SwapTD(
        reserves_x=Decimal(str(target_pool_state.baseVault.amount)),
        reserves_y=Decimal(str(target_pool_state.quoteVault.amount)),
        delta_token=Decimal(str(10280 * 10 ** y_decimal)),
        x_to_y=False,
        amount_specified_is_input=True,
        fee_kwarg=target_pool_metadata.model_dump()
    )
    res_test_3 = swapV2.swap(params_test_3)
    print(f"TEST 3: {params_test_3} \n"
          f"RESULT 3: {res_test_3} \n")
    print("_"*90)

    params_test_4 = UniswapV2Swap.SwapTD(
        reserves_x=Decimal(str(target_pool_state.baseVault.amount)),
        reserves_y=Decimal(str(target_pool_state.quoteVault.amount)),
        delta_token=res_test_3['result'],
        x_to_y=False,
        amount_specified_is_input=False,
        fee_kwarg=target_pool_metadata.model_dump()
    )
    res_test_4 = swapV2.swap(params_test_4)
    print(f"TEST 4: {params_test_4} \n"
          f"RESULT 4: {res_test_4} \n")
    print("_"*90)


if __name__ == '__main__':
    test()