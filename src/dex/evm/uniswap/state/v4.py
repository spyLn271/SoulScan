import asyncio
from web3 import Web3

####################################
from src.dex.tools.rpc.ethereum import Ethereum
from src.settings.config import get_config, DEX, Network
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

class UniswapV4(Ethereum):
    def __init__(
            self,
            network: Network,
            dex: DEX
    ):
        setup_logger(
            logger_name="Uniswap_v4_state",
            log_file=f"{get_config().DATA_FETCHER_LOG_FOLDER}/uniswap_v4_state.log"
        )

        self.logger = get_logger("Uniswap_v4_state")
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
        self.pool_manager = self.w3.eth.contract(address=self.POOL_MANAGER_ADDRESS, abi=self.ABI_INIT_EVENT)



    async def fetch_initialize_events(
            self,
            pool_ids: list[str],
            chunk_size: int = 100
    ) -> dict[str, dict[str, int]]:
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

        for logs in res:
            if isinstance(logs, Exception):
                self.logger.error(f"Error fetching logs: {logs}")
                continue

            for log in logs:
                decoded = self.pool_manager.events.Initialize().process_log(log)

                args = decoded["args"]

                pool_id = Web3.to_hex(args["id"]).lower()

                hooks = args["hooks"].lower()
                tickSpacing = int(args["tickSpacing"])
                fee_rate = int(args["fee"])

                if hooks != "0x0000000000000000000000000000000000000000" and fee_rate == 0:
                    fee_rate = 500

                results[pool_id] = {
                    "fee_rate": fee_rate,
                    "tick_spacing": tickSpacing,
                }

        return results