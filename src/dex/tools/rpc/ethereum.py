from web3.eth.eth import ChecksumAddress
from web3 import AsyncWeb3, Web3
import logging
import asyncio

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

        tasks = [
            self.multicall_contract
            .functions
            .tryAggregate(False, _input)
            .call()

            for _input in self.chunks(inputs, chunk_size)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Multi Call failed: {result}")
                return_data.extend([(False, b'')] * chunk_size)
            else:
                return_data.extend(result)

        return return_data