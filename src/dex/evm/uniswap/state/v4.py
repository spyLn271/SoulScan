import asyncio
from web3 import Web3

####################################
from src.dex.tools.rpc.ethereum import Ethereum
from src.settings.config import get_config, POOL_MANAGER_ADDRESSES, DEX, Network
from src.logger_handler.logger import get_logger, setup_logger
####################################



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
        results = {}
        tasks = []

        for pool_id_chunk in self.chunks(pool_ids, chunk_size):
            tasks.append(
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
            )

        res = await asyncio.gather(*tasks, return_exceptions=True)

        for logs in res:
            if isinstance(logs, Exception):
                self.logger.error(f"Error fetching logs: {logs}")
                continue

            for log in logs:
                decoded = self.pool_manager.events.Initialize().process_log(log)

                args = decoded["args"]

                pool_id = Web3.to_hex(args["id"]).lower()

                curr0 = args["currency0"].lower()
                curr1 = args["currency1"].lower()
                hooks = args["hooks"].lower()
                tickSpacing = int(args["tickSpacing"])
                fee_rate = int(args["fee"])

                if hooks != "0x0000000000000000000000000000000000000000" and fee_rate == 0:
                    fee_rate = 500

                results[pool_id] = {
                    "currency0": curr0,
                    "currency1": curr1,
                    "fee_rate": fee_rate,
                    "tick_spacing": tickSpacing,
                    "hooks": hooks,
                }

        return results