from src.dex.tools.rpc.ethereum import Ethereum
import asyncio
import redis
import json


r = redis.Redis(decode_responses=True)
metadata = json.loads(r.get("snapshot:metadata:eth:uniswap:v4"))

pool_ids = list(metadata.keys())

res = asyncio.run(Ethereum(network="eth", market="uniswap").fetch_initialize_events_uniswap_v4(pool_ids))

print(json.dumps(res, indent=2))