from src.dex.evm.uniswap.state.v4 import UniswapV4
import asyncio
import redis
import json


r = redis.Redis(decode_responses=True)
metadata = json.loads(r.get("snapshot:metadata:eth:uniswap:v4"))

pool_ids = list(metadata.keys())

res = asyncio.run(UniswapV4(network="eth", dex="uniswap").fetch_initialize_events(pool_ids))

print(json.dumps(res, indent=2))