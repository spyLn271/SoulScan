from src.dex.tools.rpc.ethereum import Ethereum

import asyncio


eth = Ethereum(network="eth", dex="uniswap")

call_data: bytes = bytes.fromhex("3850c7bd")

print(call_data)

inputs = [
    ("0xe0554a476a092703abdb3ef35c80e0d76d32939f", call_data),
    ("0xCBCdF9626bC03E24f779434178A73a0B4bad62eA", call_data)
]

res = asyncio.run(eth.multicall(inputs, chunk_size=1))
print(res)

