import asyncio
from web3 import Web3
from web3.eth.eth import ChecksumAddress

####################################
from src.dex.evm.type_dict import MetadataDict, SlotDict
from src.settings.basic_schemes import Tick
from src.dex.tools.rpc.ethereum import Ethereum
from src.settings.config import get_config, DEX, Network, EVM_FETCHER_LOG_FILE
from src.logger_handler.logger import get_logger, setup_logger
####################################

UNISWAP_V4_ABI = [
    {
        "inputs": [
            {
                "internalType": "PoolId",
                "name": "poolId",
                "type": "bytes32"
            },
            {
                "internalType": "int24",
                "name": "tick",
                "type": "int24"
            }
        ],
        "name": "getTickLiquidity",
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
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "PoolId",
                "name": "poolId",
                "type": "bytes32"
            }
        ],
        "name": "getSlot0",
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
                "internalType": "uint24",
                "name": "protocolFee",
                "type": "uint24"
            },
            {
                "internalType": "uint24",
                "name": "lpFee",
                "type": "uint24"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "PoolId",
                "name": "poolId",
                "type": "bytes32"
            }
        ],
        "name": "getLiquidity",
        "outputs": [
            {
                "internalType": "uint128",
                "name": "liquidity",
                "type": "uint128"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

POOL_MANAGER_ADDRESSES = {
    "base": "0x498581ff718922c3f8e6a244956af099b2652b2b",
    "eth": "0x000000000004444c5dc75cB358380D2e3dE08A90",
    "arbitrum": "0x360e68faccca8ca495c1b759fd9eee466db9fb32",
    "avax": "0x06380c0e0912312b5150364b9dc4542ba0dbbc85",
    "bsc": "0x28e2ea090877bf75740558f6bfb36a5ffee9e9df",
    "polygon": "0x67366782805870060151383f4bbff9dab53e5cd6",
    "optimism": "0x9a13f98cb987694c9f086b1f5eb990eea8264ec3",
}

STATE_VIEW_ADDRESS = {
    'base': '0xa3c0c9b65bad0b08107aa264b0f3db444b867a71',
    'eth': '0x7ffe42c4a5deea5b0fec41c94c136cf115597227',
    'arbitrum': '0x76fd297e2d437cd7f76d50f01afe6160f86e9990',
    'avax': '0xc3c9e198c735a4b97e3e683f391ccbdd60b69286',
    'bsc': '0xd13dd3d6e93f276fafc9db9e6bb47c1180aee0c4',
    'polygon': '0x5ea1bd7974c8a611cbab0bdcafcb1d9cc9b3ba5a',
    'optimism': '0xc18a3169788f4f75a170290584eca6395c75ecdb'
}

SLOT0_TYPES = ["uint160", "int24", "uint24", "uint24"]

LIQUIDITY_TYPES = ["uint128"]

TICKS_TYPES = ["uint128", "int128"]

class UniswapV4(Ethereum):
    def __init__(
            self,
            network: Network,
            dex: DEX
    ):
        setup_logger(
            logger_name=f"uniswap_v4_rpc_{network}_{dex}",
            log_file=EVM_FETCHER_LOG_FILE,
        )

        self.logger = get_logger(f"uniswap_v4_rpc_{network}_{dex}")
        self.network = network
        self.dex = dex

        super().__init__(logger=self.logger, network=network, dex=dex)


        self.ABI_INIT_EVENT = [
            {
                "type": "event",
                "name": "Initialize",
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "id", "type": "bytes32"},
                    {"indexed": True, "name": "currency0", "type": "address"},
                    {"indexed": True, "name": "currency1", "type": "address"},
                    {"indexed": False, "name": "fee", "type": "uint24"},
                    {"indexed": False, "name": "tickSpacing", "type": "int24"},
                    {"indexed": False, "name": "hooks", "type": "address"},
                    {"indexed": False, "name": "sqrtPriceX96", "type": "uint160"},
                    {"indexed": False, "name": "tick", "type": "int24"},
                ],
            }
        ]

        self.POOL_MANAGER_ADDRESS = Web3.to_checksum_address(POOL_MANAGER_ADDRESSES[self.network])
        self.STATE_VIEW_ADDRESS = Web3.to_checksum_address(STATE_VIEW_ADDRESS[self.network])

        self.pool_manager = self.w3.eth.contract(address=self.POOL_MANAGER_ADDRESS, abi=self.ABI_INIT_EVENT)
        self.uniswap_v4_contract = self.w3.eth.contract(abi=UNISWAP_V4_ABI)

        self.fetching_range: int = get_config().EVM_TICKS_FETCH_RANGE

    def _calldata(self, name: str, args: list) -> bytes:
        return bytes.fromhex(self.uniswap_v4_contract.encode_abi(name, args=args)[2:])

    async def fetch_initialize_events(
            self,
            pool_ids: list[str],
            chunk_size: int = 100
    ) -> dict[str, dict[str, int]]:
        n_inputs = len(pool_ids)
        n_chunks = (n_inputs + chunk_size - 1) // chunk_size if n_inputs else 0
        self.logger.info(f"fetch_initialize_events start: {n_inputs} pool_ids in {n_chunks} chunks")

        results: dict[str, dict[str, int]] = {}

        tasks = [
            self.w3.eth.get_logs(
                {
                    "address": self.POOL_MANAGER_ADDRESS,
                    "fromBlock": 0,
                    "toBlock": "latest",
                    "topics": [
                        "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438",
                        pool_id_chunk,
                    ],
                }
            )

            for pool_id_chunk in self.chunks(pool_ids, chunk_size)
        ]

        res = await asyncio.gather(*tasks, return_exceptions=True)

        n_fallback = 0

        for logs in res:
            if isinstance(logs, Exception):
                self.logger.error(f"Error fetching logs: {logs}", exc_info=logs)
                continue

            for log in logs:
                decoded = self.pool_manager.events.Initialize().process_log(log)

                args = decoded["args"]

                pool_id = Web3.to_hex(args["id"]).lower()

                hooks = args["hooks"].lower()
                tickSpacing = int(args["tickSpacing"])
                fee_rate = int(args["fee"])

                if hooks != "0x0000000000000000000000000000000000000000":
                    self.logger.warning(f"hooked pool_id: {pool_id}. So skipping it.")
                    continue

                results[pool_id] = {
                    "fee_rate": fee_rate,
                    "tick_spacing": tickSpacing,
                }

        if n_fallback > 0:
            self.logger.info(
                f"applied dynamic-fee fallback (fee_rate=500) to {n_fallback} hooked pools"
            )

        missing = set(p.lower() for p in pool_ids) - set(results.keys())
        if missing:
            self.logger.warning(f"no Initialize event found for {len(missing)} pool_ids")

        self.logger.info(f"fetch_initialize_events done: {len(results)}/{n_inputs} ok")

        return results

    async def fetch_slot0_data(
            self,
            metadata: dict[str, MetadataDict],
            chunk_size: int = 100
    ) -> dict[str, SlotDict]:
        slot_state: dict[str, SlotDict] = {}

        pool_addresses = list(metadata.keys())

        self.logger.info(f"fetch_slot0_data start: {len(pool_addresses)} pools")

        multicall_inputs: list[tuple[ChecksumAddress, bytes]] = []

        for pool_id in pool_addresses:

            multicall_inputs.append((
                self.STATE_VIEW_ADDRESS,
                self._calldata("getSlot0", [self.w3.to_bytes(hexstr=pool_id)])
            ))

            multicall_inputs.append((
                self.STATE_VIEW_ADDRESS,
                self._calldata("getLiquidity", [self.w3.to_bytes(hexstr=pool_id)])
            ))

        results = await self.multicall(multicall_inputs, chunk_size=chunk_size)

        for pool_id, slot0_call_res, liquidity_call_res in zip(pool_addresses, results[0::2], results[1::2]):
            try:
                _is_success_slot0 = slot0_call_res[0]
                _is_success_liquidity = liquidity_call_res[0]

                if not _is_success_slot0 or not _is_success_liquidity:
                    self.logger.error(f"Failed to fetch slot0 or liquidity for pool_id: {pool_id}")
                    continue

                slot0_data = self.w3.codec.decode(SLOT0_TYPES, slot0_call_res[1])

                liquidity = self.w3.codec.decode(LIQUIDITY_TYPES, liquidity_call_res[1])

                slot_state[pool_id.lower()] = {
                    "sqrt_price_x96": bin(slot0_data[0])[2:],
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
            pool_id: str,
            tick_current: int,
            tick_spacing: int,
    ) -> list[tuple[ChecksumAddress, bytes]]:
        # Unlike in Rust, Python's "//" round towards negative infinity
        current_tick_group = tick_current // tick_spacing
        pool_id_bytes = self.w3.to_bytes(hexstr=pool_id)

        payload: list[tuple[ChecksumAddress, bytes]] = []

        for offset in range(-self.fetching_range, self.fetching_range + 1):
            tick = (current_tick_group + offset) * tick_spacing

            payload.append((
                self.STATE_VIEW_ADDRESS,
                self._calldata("getTickLiquidity", [pool_id_bytes, tick])
            ))

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

