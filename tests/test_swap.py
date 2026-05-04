import time
from src.dex.swap_python import Swap
import redis
import json
from decimal import Decimal
import rusted_swap

redis_client = redis.Redis()

raw_orca_json = redis_client.get("snapshot:state:metadata:clmm")
orca_clmm = json.loads(raw_orca_json.decode()).get("pool_state")

raw_orca_metadata = redis_client.get("snapshot:metadata:metadata:clmm")
orca_metadata = json.loads(raw_orca_metadata.decode())

sol_usdt_pool = orca_clmm.get("Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE")
sol_usdt_metadata = orca_metadata.get("Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE")


payload = Swap.swap_params(
    pool_state=sol_usdt_pool,
    metadata=sol_usdt_metadata,
    delta_amount=Decimal("2000_000_000_000"),
    amount_specified_is_input=True,
    x_to_y=True
)

start = time.perf_counter()

res = Swap().swap(dex="metadata", version="clmm", params=payload)

elapsed = time.perf_counter() - start

print(f"Python result: {res}")
print(f"Python time: {elapsed} seconds")


whirlpool = json.dumps(sol_usdt_pool)
timestamp = int(time.time())
x_to_y = True
amount_specified_is_input = True
delta_amount = 2000_000_000_000

start = time.perf_counter()
swap_res_rust = rusted_swap.orca_swap(
    x_to_y,
    amount_specified_is_input,
    delta_amount,
    timestamp,
    whirlpool
)
elapsed = time.perf_counter() - start

print(f"Rust swap result: (total_amount_in: {swap_res_rust.total_amount_in}, total_amount_out: {swap_res_rust.total_amount_out}, total_fee_amount: {swap_res_rust.total_fee_amount})")
print(f"Rust swap time: {elapsed} seconds")
