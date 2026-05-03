from src.dex.evm.uniswap.state.v4 import UniswapV4
import asyncio
import redis
import json


r = redis.Redis(decode_responses=True)
metadata: dict = dict(list(json.loads(r.get("snapshot:metadata:eth:uniswap:v4")).items())[:3])

print(metadata)

uniV4 = UniswapV4(network="eth", dex="uniswap")

slot0 = asyncio.run(uniV4.fetch_slot0_data(metadata))

tick_liq = asyncio.run(uniV4.fetch_ticks_liquidity(slot0, metadata))

with open("slot0.json", "w") as f:
    f.write(json.dumps(slot0, indent=4))


with open("liquidity.json", "w") as f:
    f.write(json.dumps(tick_liq, indent=4))