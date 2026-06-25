import json
from src.dex.evm.uniswap.v2 import UniswapV2
from src.dex.evm.data_fetcher.state.uniswap_v2 import UniswapV2StateFetcher
import redis


r = redis.Redis(decode_responses=True)
metadata = json.loads(r.get("snapshot:metadata:eth:uniswap:v2"))

pool_ids = list(metadata.keys())

async def test():
    async with UniswapV2(network="bsc", dex="uniswap") as uniV2:
        reserves = await uniV2.fetch_reserves(
            pool_addresses=[
                "0x5ba8e0a79b44199700e19b8e228ed09390f81a51"
            ]
        )
        print(json.dumps(reserves, indent=4))


def test_state_fetcher():
    uni = UniswapV2StateFetcher()

    uni.main()


def test_uniswap_v2_swap():
    from src.dex.swap_python.swap import Swap, SwapParamsTD
    from decimal import Decimal

    raw = r.get(name="snapshot:state:eth:uniswap:v2")
    reserves = json.loads(raw)["pool_state"]

    pool = "0x76a411f14a704099ba476ce8dffc288a53295218"

    pool_state = reserves[pool]

    swap = Swap()

    params = SwapParamsTD(
        pool_state={
            "reserve0": pool_state["reserve0"],
            "reserve1": pool_state["reserve1"],
        },
        metadata=metadata[pool],
        delta_amount=Decimal(str(10 * 10 ** 18)),
        x_to_y=True,
        amount_specified_is_input=True,
    )

    print(swap.swap(params=params, dex="uniswap", version="v2"))




if __name__ == "__main__":
    # asyncio.run(test())
    test_uniswap_v2_swap()