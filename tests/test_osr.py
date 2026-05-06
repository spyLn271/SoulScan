from redis import Redis
from src.engine.osr.osr_helper import get_network_active_metadata, get_network_active_state
import json

"""
ACTIVE_NETWORK_MARKETS = {
    "solana": ['meteora_dlmm', 'orca_clmm', 'raydium_clmm', 'raydium_amm',],
    "eth": ['eth_uniswap_v2', 'eth_uniswap_v3', 'eth_uniswap_v4',],
    "arbitrum": ['arbitrum_uniswap_v2', 'arbitrum_uniswap_v3', 'arbitrum_uniswap_v4',],
    "base": ['base_uniswap_v2', 'base_uniswap_v3', 'base_uniswap_v4',],
    "bsc": ['bsc_uniswap_v2', 'bsc_uniswap_v3', 'bsc_uniswap_v4',],
}
"""

redis_con = Redis(
    decode_responses=True
)

def test_metadata_fetching():
    network = "bsc"

    metadata = get_network_active_metadata(network=network, redis_connection=redis_con)
    with open(f"{network}_metadata.json", "w") as f:
        f.write(json.dumps(metadata, indent=4))


def test_state_fetching():
    networks = ["bsc", "eth", "arbitrum", "base", "solana"]
    for n in networks:
        state = get_network_active_state(network=n, redis_connection=redis_con)
        with open(f"{n}_state.json", "w") as f:
            f.write(
                json.dumps(state, indent=4)
            )


if __name__ == "__main__":
    test_state_fetching()
