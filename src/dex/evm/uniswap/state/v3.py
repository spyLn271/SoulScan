from web3.eth.eth import ChecksumAddress
import asyncio
from web3 import Web3

####################################
from src.dex.tools.rpc.ethereum import Ethereum
from src.settings.config import get_config, DEX, Network
from src.logger_handler.logger import get_logger, setup_logger
####################################

UNISWAP_V3_ABI = [
    {
        "inputs": [
            {
                "internalType": "int24",
                "name": "",
                "type": "int24"
            }
        ],
        "name": "ticks",
        "outputs": [
            {
                "internalType": "uint128",
                "name": "liquidityGross",
                "type": "uint128"
            },
            {
                "internalType": "int128",
                "name": "liquidityNet",
                "type": "int128"
            },
            {
                "internalType": "uint256",
                "name": "feeGrowthOutside0X128",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "feeGrowthOutside1X128",
                "type": "uint256"
            },
            {
                "internalType": "int56",
                "name": "tickCumulativeOutside",
                "type": "int56"
            },
            {
                "internalType": "uint160",
                "name": "secondsPerLiquidityOutsideX128",
                "type": "uint160"
            },
            {
                "internalType": "uint32",
                "name": "secondsOutside",
                "type": "uint32"
            },
            {
                "internalType": "bool",
                "name": "initialized",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "tickSpacing",
        "outputs": [
            {
                "internalType": "int24",
                "name": "",
                "type": "int24"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {
                "internalType": "uint160",
                "name": "sqrtPriceX96",
                "type": "uint160"
            },
            {
                "internalType": "int24",
                "name": "tick",
                "type": "int24"
            },
            {
                "internalType": "uint16",
                "name": "observationIndex",
                "type": "uint16"
            },
            {
                "internalType": "uint16",
                "name": "observationCardinality",
                "type": "uint16"
            },
            {
                "internalType": "uint16",
                "name": "observationCardinalityNext",
                "type": "uint16"
            },
            {
                "internalType": "uint8",
                "name": "feeProtocol",
                "type": "uint8"
            },
            {
                "internalType": "bool",
                "name": "unlocked",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "liquidity",
        "outputs": [
            {
                "internalType": "uint128",
                "name": "",
                "type": "uint128"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "fee",
        "outputs": [
            {
                "internalType": "uint24",
                "name": "",
                "type": "uint24"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

SLOT0_TYPES_UNISWAP = ['uint160', 'int24', 'uint16', 'uint16', 'uint16', 'uint8', 'bool']
SLOT0_TYPES_PANCAKESWAP = ['uint160', 'int24', 'uint16', 'uint16', 'uint16', 'uint32', 'bool']

FEE_TYPES = ['uint24']

TICK_SPACING = ['int24']

class UniswapV3(Ethereum):
    def __init__(
            self,
            network: Network,
            dex: DEX
    ):
        setup_logger(
            logger_name="Uniswap_v3_state",
            log_file=f"{get_config().DATA_FETCHER_LOG_FOLDER}/uniswap_v3_state.log"
        )

        self.logger = get_logger("Uniswap_v3_state")
        self.network = network
        self.dex = dex

        super().__init__(logger=self.logger, network=network, dex=dex)

        self.uniswap_v3_contract = self.w3.eth.contract(abi=UNISWAP_V3_ABI)



    async def fetch_metadata_initialization(
            self,
            pool_address: list[str],
            chunk_size: int = 100
    ) -> dict[str, dict[str, int]]:
        return_data: dict[str, dict[str, int]] = {}

        multicall_inputs: list[tuple[ChecksumAddress, bytes]] = []

        tick_spacing_call_data = bytes.fromhex(self.uniswap_v3_contract.encode_abi(abi_element_identifier="tickSpacing")[2:])
        fee_rate_call_data = bytes.fromhex(self.uniswap_v3_contract.encode_abi(abi_element_identifier="fee")[2:])

        for pool_id in pool_address:
            pool_id = self.w3.to_checksum_address(pool_id)

            multicall_inputs.extend([(pool_id, tick_spacing_call_data)])
            multicall_inputs.extend([(pool_id, fee_rate_call_data)])

        results = await self.multicall(multicall_inputs, chunk_size=chunk_size)

        for pool_id, tick_spacing_call_res, fee_call_res in zip(pool_address, results[0::2], results[1::2]):
            _is_success_tick_spacing = tick_spacing_call_res[0]
            _is_success_fee = fee_call_res[0]

            if not _is_success_tick_spacing or not _is_success_fee:
                self.logger.error(f"Failed to fetch slot0 or fee for pool_id: {pool_id}")
                continue

            tick_spacing = self.w3.codec.decode(TICK_SPACING, tick_spacing_call_res[1])
            fee_rate = self.w3.codec.decode(FEE_TYPES, fee_call_res[1])

            return_data[pool_id.lower()] = {
              "tick_spacing": tick_spacing[0],
              "fee_rate": fee_rate[0]
            }


        return return_data