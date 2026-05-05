from web3.eth.eth import ChecksumAddress
from typing import TypedDict

####################################
from src.dex.tools.rpc.ethereum import Ethereum
from src.settings.config import get_config, DEX, Network
from src.logger_handler.logger import get_logger, setup_logger
####################################

UNISWAP_V2_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {
                "internalType": "uint112",
                "name": "_reserve0",
                "type": "uint112"
            },
            {
                "internalType": "uint112",
                "name": "_reserve1",
                "type": "uint112"
            },
            {
                "internalType": "uint32",
                "name": "_blockTimestampLast",
                "type": "uint32"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

RESERVE_TYPES = ['uint112', 'uint112', 'uint32']

class UniswapV2Reserves(TypedDict):
    reserve0: int
    reserve1: int



class UniswapV2(Ethereum):
    def __init__(
            self,
            network: Network,
            dex: DEX
    ):
        setup_logger(
            logger_name=f"Uniswap_v2_state_{network}_{dex}",
            log_file=f"{get_config().DATA_FETCHER_LOG_FOLDER}/Uniswap_v2_state_{network}_{dex}.log"
        )

        self.logger = get_logger(f"Uniswap_v2_state_{network}_{dex}")

        super().__init__(network=network, dex=dex, logger=self.logger)

        self.uniswap_v2_contract = self.w3.eth.contract(abi=UNISWAP_V2_ABI)


    def _calldata(self, name: str, args: list) -> bytes:
        return bytes.fromhex(self.uniswap_v2_contract.encode_abi(name, args=args)[2:])


    async def fetch_reserves(
            self,
            pool_addresses: list[str],
            chunk_size: int = 100
    ) -> dict[str, UniswapV2Reserves]:
        reserves: dict[str, UniswapV2Reserves] = {}

        self.logger.info(f"fetch_reserves start: {len(pool_addresses)} pools")

        multicall_inputs: list[tuple[ChecksumAddress, bytes]] = []

        for pool_address in pool_addresses:
            checksum_address = self.w3.to_checksum_address(pool_address)

            multicall_inputs.append(
                (checksum_address, self._calldata("getReserves", []))
            )


        results = await self.multicall(multicall_inputs, chunk_size=chunk_size)

        for pool_address, call_res in zip(pool_addresses, results):
            try:
                _is_success = call_res[0]

                if not _is_success:
                    self.logger.error(f"Failed to fetch reserves for pool_address: {pool_address}")
                    continue

                reserve0, reserve1, _ = self.w3.codec.decode(RESERVE_TYPES, call_res[1])

                reserves[pool_address.lower()] = {
                    "reserve0": reserve0,
                    "reserve1": reserve1
                }

            except Exception as e:
                self.logger.error(
                    f"Occurred error while fetching reserves for pool_address: {pool_address}, error: {e}",
                    exc_info=True,
                )
                continue


        self.logger.info(f"fetch_reserves done: {len(reserves)}/{len(pool_addresses)} ok")


        return reserves