from web3.eth.eth import ChecksumAddress
from web3 import AsyncWeb3, Web3
import logging
import asyncio
import time

####################################
from src.settings.config import get_config, EVM_RPC_ENDPOINT, DEX, Network
####################################

class Ethereum:
    def __init__(
            self,
            network: Network,
            dex: DEX,
            logger: logging.Logger = None
    ):
        self.config = get_config()

        self.network = network
        self.dex = dex

        self.logger = logger or logging.getLogger(__name__)

        self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(EVM_RPC_ENDPOINT[network]))

        self.MULTICALL_ABI = [{
            "inputs": [
                {
                    "internalType": "bool",
                    "name": "requireSuccess",
                    "type": "bool"
                },
                {
                    "components": [
                        {
                            "internalType": "address",
                            "name": "target",
                            "type": "address"
                        },
                        {
                            "internalType": "bytes",
                            "name": "callData",
                            "type": "bytes"
                        }
                    ],
                    "internalType": "struct Multicall3.Call[]",
                    "name": "calls",
                    "type": "tuple[]"
                }
            ],
            "name": "tryAggregate",
            "outputs": [
                {
                    "components": [
                        {
                            "internalType": "bool",
                            "name": "success",
                            "type": "bool"
                        },
                        {
                            "internalType": "bytes",
                            "name": "returnData",
                            "type": "bytes"
                        }
                    ],
                    "internalType": "struct Multicall3.Result[]",
                    "name": "returnData",
                    "type": "tuple[]"
                }
            ],
            "stateMutability": "payable",
            "type": "function"
        }]
        self.multicall_contract = self.w3.eth.contract(
            abi=self.MULTICALL_ABI,
            address=Web3.to_checksum_address('0xcA11bde05977b3631167028862bE2a173976CA11')
        )

        self.logger.info(f"Ethereum init: network={network} dex={dex} rpc={EVM_RPC_ENDPOINT[network]}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.w3.provider.disconnect()
        self.logger.info("provider disconnected")

    @staticmethod
    def chunks(items, size):
        for i in range(0, len(items), size):
            yield items[i:i + size]


    async def multicall(
            self,
            inputs: list[tuple[ChecksumAddress, bytes]],
            chunk_size: int = 100
    ) -> list[tuple[bool, bytes]]:
        return_data: list[tuple[bool, bytes]] = []

        n_inputs = len(inputs)
        if n_inputs == 0:
            self.logger.debug("multicall called with empty inputs; skipping")
            return return_data

        n_chunks = (n_inputs + chunk_size - 1) // chunk_size
        self.logger.info(f"multicall start: {n_inputs} calls in {n_chunks} chunks (size={chunk_size})")

        t0 = time.perf_counter()

        tasks = [
            self.multicall_contract
            .functions
            .tryAggregate(False, _input)
            .call()

            for _input in self.chunks(inputs, chunk_size)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for chunk_input, result in zip(list(self.chunks(inputs, chunk_size)), results):
            if isinstance(result, Exception):
                self.logger.error(f"Multi Call failed: {result}", exc_info=result)
                return_data.extend([(False, b'')] * len(chunk_input))
            else:
                return_data.extend(result)

        elapsed = time.perf_counter() - t0
        n_failed_chunks = sum(1 for r in results if isinstance(r, Exception))
        n_failed_calls = sum(1 for s, _ in return_data if not s)
        self.logger.info(
            f"multicall done in {elapsed:.2f}s: "
            f"{n_inputs - n_failed_calls}/{n_inputs} ok, "
            f"{n_failed_chunks}/{n_chunks} chunks failed"
        )

        return return_data