import asyncio
import json
from src.dex.evm.uniswap.state.v2 import UniswapV2


async def test():
    async with UniswapV2(network="bsc", dex="uniswap") as uniV2:
        reserves = await uniV2.fetch_reserves(
            pool_addresses=[
                "0x5ba8e0a79b44199700e19b8e228ed09390f81a51"
            ]
        )
        print(json.dumps(reserves, indent=4))



if __name__ == "__main__":
    asyncio.run(test())