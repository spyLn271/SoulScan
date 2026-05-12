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


def test_get_all_cold_path():
    from src.engine.osr.online_smart_router import config

    entries = redis_con.hgetall(config.REDIS_KEY_COLD_PATH)

    all_cold_paths = {}

    total_empty = 0

    evm_empty = 0

    solana_empty = 0

    solana_cold_paths = 0
    evm_cold_paths = 0

    total_cold_paths = 0

    for pair, payload in entries.items():
        data = json.loads(payload)
        all_cold_paths[pair] = data

        addr0, addr1 = pair.split('/')

        if addr0.startswith("0x") and addr1.startswith("0x"):
            evm_cold_paths += 1
        else:
            solana_cold_paths += 1

        total_cold_paths += 1


        if not data["routes"]:
            total_empty += 1

            if addr0.startswith("0x") and addr1.startswith("0x"):
                evm_empty += 1
            else:
                solana_empty += 1

    with open("cold_paths.json", "w") as f:
        f.write(json.dumps(all_cold_paths, indent=4))

    print(f"Empty cold paths: {total_empty}")
    print(f"EVM empty cold paths: {evm_empty}")
    print(f"Solana empty cold paths: {solana_empty}")

    print(f"Total cold paths: {total_cold_paths}")
    print(f"EVM cold paths: {evm_cold_paths}")
    print(f"Solana cold paths: {solana_cold_paths}")

def test_brute_for_pair():
    """
    Simulates _find_candidates_for_pair_v1 + _filter_candidates_v1 for ONE
    base/quote pair on a given network. Prints per-route failure reasons so
    you can see why empty cold paths happen.

    Edit the constants below and run:
        python3.12 -m tests.test_osr
    """
    import logging
    from collections import Counter
    from decimal import Decimal
    from src.engine.osr.osr_helper import create_graph
    from src.engine.osr.online_smart_router import OnlineSmartRouterEngineV1
    from src.engine.osr.math_smart_router import MathSmartRouter
    from src.settings.bases import AMOUNT_PROBE

    NETWORK = "eth"
    BASE = "0x1003ffc452d2797c555d89317534cdd215aa2560"
    QUOTE = "0xdac17f958d2ee523a2206206994597c13d831ec7"  # USDT on ETH

    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger("brute_test")

    metadata = get_network_active_metadata(network=NETWORK, redis_connection=redis_con)
    state = get_network_active_state(network=NETWORK, redis_connection=redis_con)
    print(f"\nmetadata={len(metadata)} pools, state={len(state)} pools")

    G = create_graph(metadata, state)
    print(f"graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"base in graph: {BASE in G.nodes}, quote in graph: {QUOTE in G.nodes}")
    if BASE not in G.nodes or QUOTE not in G.nodes:
        print("base or quote missing from graph; nothing to simulate.")
        return

    engine = OnlineSmartRouterEngineV1(
        logger=logger,
        math_smart_router=MathSmartRouter(logger=logger),
        network=NETWORK,
    )

    candidates = engine._find_candidates_for_pair_v1(G, BASE, QUOTE)
    print(f"\ncandidates after Bases filter: {len(candidates)}")
    if not candidates:
        return

    # decimals of input token from a sample candidate's first pool
    sample_pool = candidates[0][0]
    pool_meta = metadata[sample_pool]
    if pool_meta.get("mint0") == BASE:
        decimals = pool_meta["decimals0"]
    else:
        decimals = pool_meta["decimals1"]
    print(f"input decimals = {decimals}")

    # how many candidates have all pools present in state?
    fully_in_state = sum(
        1 for c in candidates if all(p in state for p in c)
    )
    print(f"candidates with all pools in state: {fully_in_state}/{len(candidates)}")

    # per-probe simulation summary
    print(f"\n{'probe':>12s}  {'succ':>5s}  {'fail':>5s}  top failure reasons")
    for human_amount in AMOUNT_PROBE:
        atomic = int(human_amount * (Decimal(10) ** decimals))
        succ = 0
        reasons: Counter = Counter()
        best_out = Decimal(0)
        for route in candidates:
            res = engine.math_smart_router.smart_swap(
                route=route,
                metadata=metadata,
                state=state,
                delta_amount=atomic,
                base_mint=BASE,
                quote_mint=QUOTE,
                amount_specified_is_input=True,
            )
            if res["is_success"] and res["result"] > 0:
                succ += 1
                if res["result"] > best_out:
                    best_out = res["result"]
            else:
                # collapse the variable parts so the counter buckets cleanly
                msg = res["message"]
                key = msg.split(":")[0] if ":" in msg else msg
                reasons[key] += 1

        top = ", ".join(f"{k}({v})" for k, v in reasons.most_common(3))
        print(f"  {str(human_amount):>10s}  {succ:>5d}  {sum(reasons.values()):>5d}  {top}")
        if succ:
            print(f"  {'':>10s}  best_out={best_out}")

    # show the FULL failure message for one route so we see the real exception
    print("\nFull failure for first candidate at smallest probe:")
    atomic = int(AMOUNT_PROBE[-1] * (Decimal(10) ** decimals))
    res = engine.math_smart_router.smart_swap(
        route=candidates[0],
        metadata=metadata,
        state=state,
        delta_amount=atomic,
        base_mint=BASE,
        quote_mint=QUOTE,
        amount_specified_is_input=True,
    )
    print(f"  route: {candidates[0]}")
    print(f"  result: {res}")
    # also dump the offending pool's metadata + state
    bad_pool = candidates[0][0]
    print(f"\n  pool {bad_pool} metadata: {metadata.get(bad_pool)}")
    bad_state = state.get(bad_pool)
    if isinstance(bad_state, dict):
        slot = bad_state.get("slot", {})
        ticks = bad_state.get("ticks", {})
        print(f"  slot: {slot}")
        print(f"  ticks count: {len(ticks) if isinstance(ticks, dict) else 'n/a'}")
        if isinstance(ticks, dict):
            print(f"  sample ticks: {list(ticks.items())[:5]}")
    else:
        print(f"  state: {bad_state}")


if __name__ == "__main__":
    test_brute_for_pair()
