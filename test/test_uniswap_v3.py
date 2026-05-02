from src.dex.evm.uniswap.state.v3 import UniswapV3
import asyncio
import redis
import json


r = redis.Redis(decode_responses=True)
metadata = json.loads(r.get("snapshot:metadata:eth:uniswap:v3"))

pool_ids = list(metadata.keys())

univ3 = UniswapV3(network="eth", dex="uniswap")

res = asyncio.run(univ3.fetch_metadata_initialization(pool_ids))

print(res)