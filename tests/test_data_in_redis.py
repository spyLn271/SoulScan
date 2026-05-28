import redis
import json

redis_client = redis.Redis(decode_responses=True)

raw = redis_client.get("snapshot:metadata:eth:uniswap:v3")
slot = json.loads(raw)

with open("slot0.json", "w") as f:
    f.write(json.dumps(slot, indent=4))