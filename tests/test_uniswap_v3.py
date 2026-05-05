from src.dex.evm.uniswap.v3 import UniswapV3
import asyncio
import redis
import json


r = redis.Redis(decode_responses=True)
metadata = json.loads(r.get("snapshot:metadata:bsc:uniswap:v3"))

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

if __name__ == "__main__":
    asyncio.run(test())
