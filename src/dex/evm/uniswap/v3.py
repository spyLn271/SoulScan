from web3.eth.eth import ChecksumAddress

####################################
from src.dex.tools.rpc.ethereum import Ethereum
from src.settings.config import get_config, DEX, Network
from src.logger_handler.logger import get_logger, setup_logger
from src.dex.evm.type_dict import MetadataDict, SlotDict
from src.settings.basic_schemes import Tick
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

LIQUIDITY_TYPES = ['uint128']

TICKS_TYPES = ['uint128', 'int128', 'uint256', 'uint256', 'int56', 'uint160', 'uint32', 'bool']

class UniswapV3(Ethereum):
    def __init__(
            self,
            network: Network,
            dex: DEX
    ):
        setup_logger(
            logger_name=f"Uniswap_v3_state_{network}_{dex}",
            log_file=f"{get_config().DATA_FETCHER_LOG_FOLDER}/Uniswap_v3_state_{network}_{dex}.log"
        )

        self.fetching_range: int = get_config().EVM_TICKS_FETCH_RANGE

        self.logger = get_logger(f"Uniswap_v3_state_{network}_{dex}")
        self.network = network
        self.dex = dex

        super().__init__(logger=self.logger, network=network, dex=dex)

        self.uniswap_v3_contract = self.w3.eth.contract(abi=UNISWAP_V3_ABI)

    def _calldata(self, name: str, args: list) -> bytes:
        return bytes.fromhex(self.uniswap_v3_contract.encode_abi(name, args=args)[2:])

    async def fetch_metadata_initialization(
            self,
            pool_address: list[str],
            chunk_size: int = 100
    ) -> dict[str, dict[str, int]]:
        self.logger.info(f"fetch_metadata_initialization start: {len(pool_address)} pools")

        return_data: dict[str, dict[str, int]] = {}

        multicall_inputs: list[tuple[ChecksumAddress, bytes]] = []

        tick_spacing_call_data = self._calldata("tickSpacing", [])
        fee_rate_call_data = self._calldata("fee", [])

        for pool_id in pool_address:
            pool_id = self.w3.to_checksum_address(pool_id)

            multicall_inputs.extend([(pool_id, tick_spacing_call_data)])
            multicall_inputs.extend([(pool_id, fee_rate_call_data)])

        results = await self.multicall(multicall_inputs, chunk_size=chunk_size)

        for pool_id, tick_spacing_call_res, fee_call_res in zip(pool_address, results[0::2], results[1::2]):
            try:
                _is_success_tick_spacing = tick_spacing_call_res[0]
                _is_success_fee = fee_call_res[0]

                if not _is_success_tick_spacing or not _is_success_fee:
                    self.logger.error(f"Failed to fetch tick spacing or fee for pool_id: {pool_id}")
                    continue

                tick_spacing = self.w3.codec.decode(TICK_SPACING, tick_spacing_call_res[1])
                fee_rate = self.w3.codec.decode(FEE_TYPES, fee_call_res[1])

                return_data[pool_id.lower()] = {
                    "tick_spacing": tick_spacing[0],
                    "fee_rate": fee_rate[0]
                }
            except Exception as e:
                self.logger.error(f"Error processing pool_id: {pool_id}, error: {e}", exc_info=True)
                continue

        self.logger.info(f"fetch_metadata_initialization done: {len(return_data)}/{len(pool_address)} ok")

        return return_data

    async def fetch_slot0_data(
            self,
            metadata: dict[str, MetadataDict],
            chunk_size: int = 100
    ) -> dict[str, SlotDict]:
        slot_state: dict[str, SlotDict] = {}

        pool_addresses = list(metadata.keys())

        self.logger.info(f"fetch_slot0_data start: {len(pool_addresses)} pools")

        multicall_inputs: list[tuple[ChecksumAddress, bytes]] = []

        slot0_call_data = self._calldata("slot0", [])
        liquidity_call_data = self._calldata("liquidity", [])

        for pool_id in pool_addresses:
            pool_id = self.w3.to_checksum_address(pool_id)

            multicall_inputs.extend([(pool_id, slot0_call_data)])
            multicall_inputs.extend([(pool_id, liquidity_call_data)])


        results = await self.multicall(multicall_inputs, chunk_size=chunk_size)

        for pool_id, slot0_call_res, liquidity_call_res in zip(pool_addresses, results[0::2], results[1::2]):
            try:
                _is_success_slot0 = slot0_call_res[0]
                _is_success_liquidity = liquidity_call_res[0]

                if not _is_success_slot0 or not _is_success_liquidity:
                    self.logger.error(f"Failed to fetch slot0 or liquidity for pool_id: {pool_id}")
                    continue


                dex = metadata[pool_id.lower()]["dex"]

                if dex == "uniswap" or dex == "sushiswap":
                    slot0_data = self.w3.codec.decode(SLOT0_TYPES_UNISWAP, slot0_call_res[1])
                elif dex == "pancakeswap":
                    slot0_data = self.w3.codec.decode(SLOT0_TYPES_PANCAKESWAP, slot0_call_res[1])
                else:
                    self.logger.error(f"Unsupported dex: {dex} for pool_id: {pool_id}")
                    continue

                liquidity = self.w3.codec.decode(LIQUIDITY_TYPES, liquidity_call_res[1])

                slot_state[pool_id.lower()] = {
                    "sqrt_price_x96": slot0_data[0],
                    "tick_current": slot0_data[1],
                    "liquidity": liquidity[0]
                }

            except Exception as e:
                self.logger.error(f"Error processing pool_id: {pool_id}, error: {e}", exc_info=True)
                continue

        self.logger.info(f"fetch_slot0_data done: {len(slot_state)}/{len(pool_addresses)} ok")

        return slot_state


    def _create_payload_for_tick_range(
            self,
            address: str,
            tick_current: int,
            tick_spacing: int,
    ) -> list[tuple[ChecksumAddress, bytes]]:
        # Unlike in Rust, Python's "//" round towards negative infinity
        current_tick_group = tick_current // tick_spacing

        payload: list[tuple[ChecksumAddress, bytes]] = []

        for offset in range(-self.fetching_range, self.fetching_range + 1):
            payload.append(
                (
                    self.w3.to_checksum_address(address),
                    self._calldata("ticks", [(current_tick_group + offset) * tick_spacing]),
                )
            )

        return payload

    def _decode_tick_range(
            self,
            tick_range_call_res: list[tuple[bool, bytes]],
            tick_current: int,
            tick_spacing: int,
    ) -> dict[int, Tick]:
        ticks: dict[int, Tick] = {}
        current_tick_group = tick_current // tick_spacing

        for i, (is_success, data) in enumerate(tick_range_call_res):
            if not is_success:
                continue

            decoded = self.w3.codec.decode(TICKS_TYPES, data)

            offset = i - self.fetching_range

            ticks[(current_tick_group + offset) * tick_spacing] = {
                "liquidityGross": decoded[0],
                "liquidityNet": decoded[1],
            }

        return ticks

    async def fetch_ticks_liquidity(
            self,
            slot0_data: dict[str, SlotDict],
            metadata: dict[str, MetadataDict],
            chunk_size: int = 100,
    ) -> dict[str, dict[int, Tick]]:

        self.logger.info(
            f"fetch_ticks_liquidity start: {len(slot0_data)} pools, range=±{self.fetching_range}"
        )

        ticks_liquidity: dict[str, dict[int, Tick]] = {}

        pool_ids = list(slot0_data.keys())

        multicall_inputs: list[tuple[ChecksumAddress, bytes]] = []

        valid_pool_ids: list[str] = []

        for pool_id in pool_ids:
            if pool_id.lower() not in metadata:
                self.logger.error(f"Pool_id: {pool_id} not found in metadata for fetching ticks liquidity.")
                continue

            tick_current = slot0_data[pool_id.lower()]["tick_current"]
            tick_spacing = metadata[pool_id.lower()]["tick_spacing"]

            multicall_inputs.extend(
                self._create_payload_for_tick_range(pool_id, tick_current, tick_spacing)
            )

            valid_pool_ids.append(pool_id.lower())

        results = await self.multicall(multicall_inputs, chunk_size=chunk_size)

        offset = self.fetching_range * 2 + 1

        res_chunks = (results[i:i + offset] for i in range(0, len(results), offset))

        for pool_id, tick_range_call_res in zip(valid_pool_ids, res_chunks, strict=True):
            try:
                tick_current = slot0_data[pool_id.lower()]["tick_current"]
                tick_spacing = metadata[pool_id.lower()]["tick_spacing"]

                ticks_liquidity[pool_id.lower()] = self._decode_tick_range(
                    tick_range_call_res,
                    tick_current,
                    tick_spacing,
                )

            except Exception as e:
                self.logger.error(f"Error processing pool_id: {pool_id}, error: {e}", exc_info=True)

        n_ticks = sum(len(t) for t in ticks_liquidity.values())
        self.logger.info(
            f"fetch_ticks_liquidity done: {len(ticks_liquidity)}/{len(pool_ids)} pools, "
            f"{n_ticks} ticks decoded"
        )

        return ticks_liquidity
