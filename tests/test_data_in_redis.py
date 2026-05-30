import redis
import json
from src.engine.osr.osr_helper import get_network_active_metadata, get_network_active_state, get_all_tokens

redis_client = redis.Redis(decode_responses=True)

def test_all_tokens():
    metadata = get_network_active_metadata(redis_connection=redis_client, network="solana")
    state = get_network_active_state(redis_connection=redis_client, network="solana")
    all_tokens = get_all_tokens(metadata=metadata, state=state)
    with open("all_tokens_sol.json", "w") as f:
        f.write(json.dumps(all_tokens, indent=4))


if __name__ == "__main__":
    test_all_tokens()