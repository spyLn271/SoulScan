from src.dex.evm.uniswap.v3 import UniswapV3
import asyncio
import redis
import json


r = redis.Redis(decode_responses=True)
metadata = json.loads(r.get("snapshot:metadata:base:uniswap:v4"))

pool_ids = list(metadata.keys())

async def test():
    async with UniswapV3(network="bsc", dex="uniswap") as univ3:
        on_chain_metadata = await univ3.fetch_metadata_initialization(pool_ids[:3])
        print(on_chain_metadata)

        slot0_data = await univ3.fetch_slot0_data(metadata)

        with open("slot0.json", "w") as f:
            f.write(json.dumps(slot0_data, indent=4))

        with open("liquidity.json", "w") as f:
            ticks_liq = asyncio.run(
                univ3.fetch_ticks_liquidity(
                    slot0_data=slot0_data,
                    metadata=metadata,
                )
            )

            f.write(json.dumps(ticks_liq, indent=4))

        print("ok")


async def test_redis_data():
    raw = r.hget(name="snapshot:state:eth:uniswap:v3", key="slot")
    slot = json.loads(raw)


    with open("slot0.json", "w") as f:
        f.write(json.dumps(slot, indent=4))

    raw = r.hget(name="snapshot:state:eth:uniswap:v3", key="ticks")
    ticks = json.loads(raw)

    with open("liquidity.json", "w") as f:
        f.write(json.dumps(ticks, indent=4))


def test_uniswap_v3_swap():
    from src.dex.swap_python.swap import Swap, SwapParamsTD
    from decimal import Decimal

    raw = r.hget(name="snapshot:state:base:uniswap:v4", key="slot")
    slots = json.loads(raw)["pool_state"]

    raw = r.hget(name="snapshot:state:base:uniswap:v4", key="ticks")
    ticks = json.loads(raw)["pool_state"]

    pool = "0xe070797535b13431808f8fc81fdbe7b41362960ed0b55bc2b6117c49c51b7eb9"

    pool_slot = slots[pool]
    pool_tick = ticks[pool]

    swap = Swap()

    params = SwapParamsTD(
        pool_state={
            "slot": pool_slot,
            "ticks": pool_tick,
        },
        metadata=metadata[pool],
        delta_amount=Decimal(str(1000 * 10 ** 18)),
        x_to_y=True,
        amount_specified_is_input=True,
    )

    print(swap.swap(params=params, dex="uniswap", version="v4"))



if __name__ == "__main__":
    # asyncio.run(test_redis_data())
    test_uniswap_v3_swap()