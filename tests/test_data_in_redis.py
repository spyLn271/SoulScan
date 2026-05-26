import redis
import json

redis_client = redis.Redis(decode_responses=True)

raw = redis_client.hget("snapshot:state:eth:uniswap:v3", "slot")
slot = json.loads(raw)

wrtie_to_file = open("slot0.json", "w")
wrtie_to_file.write(json.dumps(slot, indent=4))
wrtie_to_file.close()