from typing import Tuple, List
from solders.pubkey import Pubkey as SolanaPubkey
import os

####################################
from src.settings import config
from src.dex.tools.rpc.Solana import Solana
from src.dex.tools.helpers.solana.translater import Translater
from src.logger_handler.logger import setup_logger, get_logger
from src.dex.solana.raydium.state.raydium_scheme import RaydiumCLMMDependenciesScheme, RaydiumCacheCLMMDependenciesScheme
####################################








"""
1) what is state CLMM ?
2) How it works ?
3) How data is organized ?
4) what information do I need from it?


1)
    state CLMM is Uniswap V3 for Solana. There is no Dynamic Fee.
2) 
    The math is Uniswap V3.
3)
    In PoolState is current pools data and all needed information.
    In TickArray accounts, which was chunked in 60 pieces for every TickArray, has all Liquidity.
4)
    Cache func will need to fetch Pool State.
    BigBox func will need to fetch Pool State and TickArray.

"""
class RaydiumCLMMTranslater(Translater):
    def __init__(self, logger):
        super().__init__(logger)

    def translate_PoolState(self, x: str) -> dict:
        try:
            parsed_data = self.translate(data=x, market='state', name='PoolState')
            if not parsed_data:
                raise Exception("Failed to translate PoolState")

            tick_spacing = parsed_data['tick_spacing']
            liquidity = parsed_data['liquidity']
            sqrt_price_x64 = parsed_data['sqrt_price_x64']
            tick_current = parsed_data['tick_current']


            return {"tick_spacing": tick_spacing,
                    "liquidity": liquidity,
                    "sqrt_price_x64": sqrt_price_x64,
                    "tick_current": tick_current}
        except Exception as e:
            self.logger.error(e)
            return {}

    def translate_TickArray(self, x: str | None, start_index: int, tick_spacing: int) -> dict:
        if x is None:
            not_init_ticks_dict = {}
            for i in range(config.TICK_ARRAY_SIZE_RAYDIUM_CLMM):
                not_init_ticks_dict[str(start_index + i * tick_spacing)] = {
                    "liquidityNet": 0,
                    "liquidityGross": 0
                }

            return not_init_ticks_dict

        try:
            parsed_data = self.translate(data=x, market='state', name='TickArray')
            if not parsed_data:
                raise Exception("Failed to translate TickArray")

            start_tick_index = parsed_data['start_tick_index']
            if start_tick_index != start_index:
                raise Exception("start_tick_index must be equal to start_index")
            ticks_array = parsed_data['ticks']
            ticks_dict = {}
            for i, tick in enumerate(ticks_array):
                ticks_dict[str(start_index + i * tick_spacing)] = {
                    "liquidityNet": tick["liquidity_net"],
                    "liquidityGross": tick["liquidity_gross"]
                }

            return ticks_dict
        except Exception as e:
            self.logger.error(e)
            return {}


class RaydiumCLMM(Solana):
    def __init__(self, SOLANA_RPC_ENDPOINT=config.SOLANA_RPC_ENDPOINT, logger_name='RaydiumCLMM',
                 logger_file="RaydiumCLMM.log"):
        super().__init__(SOLANA_RPC_ENDPOINT)

        setup_logger(logger_name=logger_name,
                     log_file=os.path.join(config.DATA_FETCHER_LOG_FOLDER, logger_file))
        self.logger = get_logger(logger_name=logger_name)
        self.translater = RaydiumCLMMTranslater(logger=self.logger)
        self.program_id = SolanaPubkey.from_string(config.RAYDIUM_CLMM_PROGRAM_ID)

    @staticmethod
    def _get_start_index(current_tick, tick_spacing) -> int:
        return ((current_tick // (config.TICK_ARRAY_SIZE_RAYDIUM_CLMM * tick_spacing)) *
                (config.TICK_ARRAY_SIZE_RAYDIUM_CLMM * tick_spacing))

    @staticmethod
    def _get_offset(tick_spacing) -> int:
        return int(config.TICK_ARRAY_SIZE_RAYDIUM_CLMM * tick_spacing)

    # FOR FETCHING BIG BOX
    def _create_dependencies_for_pool(self, address: str, current_tick: int,
                                     tick_spacing: int) -> RaydiumCLMMDependenciesScheme:
        idx = self._get_start_index(current_tick, tick_spacing)
        offset = self._get_offset(tick_spacing)
        start_indexes = [idx - 2 * offset,
                         idx - 1 * offset,
                         idx,
                         idx + 1 * offset,
                         idx + 2 * offset]
        PoolState = [address]
        PDAs = []
        for start_index in start_indexes:
            PDA = self.findProgramDerivedAddress(
                [b"tick_array", bytes(SolanaPubkey.from_string(address)),
                 start_index.to_bytes(4, signed=True)],
                self.program_id
            )
            PDAs.append(PDA)

        return RaydiumCLMMDependenciesScheme(
            Address=address,
            PoolState=PoolState,
            PDAs=PDAs,
            start_indexes=start_indexes,
            tick_spacing=tick_spacing
        )

    def _create_calldata(self, addresses: list[str], current_tick_list: list[int],
                                 tick_spacing_list: list[int]) -> Tuple[list[str], List[RaydiumCLMMDependenciesScheme]]:
        dependencies_list: List[RaydiumCLMMDependenciesScheme] = []
        calldata_list: list[str] = []
        if len(addresses) != len(current_tick_list) or len(current_tick_list) != len(tick_spacing_list):
            self.logger.error(f"Address and current_tick_list and tick_spacing_list must have same length")
            return calldata_list, dependencies_list

        for i, address in enumerate(addresses):
            current_tick = current_tick_list[i]
            tick_spacing = tick_spacing_list[i]

            try:
                dependencies = self._create_dependencies_for_pool(address, current_tick, tick_spacing)
                PoolState = dependencies.PoolState
                PDAs = dependencies.PDAs
                calldata = PoolState + PDAs

                calldata_list.extend(calldata)
                dependencies_list.append(dependencies)
            except Exception as e:
                self.logger.error(f"Failed to create dependencies for address {address}, exception {e}")


        return calldata_list, dependencies_list

    def _assemble_BigBox_data(self, raw_data: dict, dependencies_list: List[RaydiumCLMMDependenciesScheme]) -> dict:
        final_assembled_pools = {}

        for dependencies in dependencies_list:
            address = dependencies.Address
            PoolState = dependencies.PoolState[0]
            PDAs = dependencies.PDAs
            start_indexes = dependencies.start_indexes
            tick_spacing = dependencies.tick_spacing

            raw_pool_state = raw_data.get(PoolState, [{}])[0].get('data')
            if not raw_pool_state:
                self.logger.error(f"Raw pool state for address {address} was not found in the data")
                continue
            pool_state = self.translater.translate_PoolState(raw_pool_state)
            if not pool_state:
                self.logger.error(f"Couldn't translate Pool state for address {address} was not found in the data")
                continue

            tickArray = {}
            for i, PDA in enumerate(PDAs):
                start_index = start_indexes[i]
                if PDA not in raw_data:
                    self.logger.error(f"PDA({PDA}) info was not found in Solana response. "
                                      f"Maybe there was some error problem the request in RPC part.")
                    continue

                raw_tick_array = raw_data.get(PDA, [{}])[0].get('data')
                tick_array = self.translater.translate_TickArray(raw_tick_array, start_index, tick_spacing)
                if not tick_array: continue
                tickArray.update(tick_array)

            final_assembled_pools[address] = {
                'PoolState': pool_state,
                'ticks': tickArray,
            }

        return final_assembled_pools

    ######################

    # FOR ESTABLISHING CACHE DATA

    @staticmethod
    def _create_cache_dependencies_for_pool(address: str) -> RaydiumCacheCLMMDependenciesScheme:
        return RaydiumCacheCLMMDependenciesScheme(Address=address, PoolState=address)

    def _create_cache_calldata(self, addresses: list[str]) -> Tuple[list[str], list[RaydiumCacheCLMMDependenciesScheme]]:
        dependencies_list: List[RaydiumCacheCLMMDependenciesScheme] = []
        calldata_list: list[str] = []

        for address in addresses:
            dependencies = self._create_cache_dependencies_for_pool(address)
            PoolState = dependencies.PoolState

            calldata_list.append(PoolState)
            dependencies_list.append(dependencies)

        return calldata_list, dependencies_list

    def _assemble_cache_data(self, raw_data: dict, dependencies_list: List[RaydiumCacheCLMMDependenciesScheme]) -> dict:
        final_assembled_pools = {}

        for dependencies in dependencies_list:
            address = dependencies.Address
            PoolState = dependencies.PoolState
            raw_pool_state = raw_data.get(PoolState, [{}])[0].get('data')
            if not raw_pool_state:
                self.logger.error(f"Raw pool state for address {address} was not found in the data")
                continue
            pool_state = self.translater.translate_PoolState(raw_pool_state)
            if not pool_state:
                self.logger.error(f"Couldn't translate Pool state for address {address} was not found in the data")
                continue
            final_assembled_pools[address] = pool_state

        return final_assembled_pools

    ######################


    async def getBigBox(self, addresses: list[str], current_tick_list: list[int],
                        tick_spacing_list: list[int]) -> dict:
        try:
            calldata_list, dependencies_list = self._create_calldata(addresses, current_tick_list, tick_spacing_list)
            raw_data = await self.getMultipleAccounts(calldata_list,
                                                      field=['data'],
                                                      funcs={'data': lambda x: x[0]})
            return self._assemble_BigBox_data(raw_data, dependencies_list)
        except Exception as e:
            self.logger.error(f"Failed to get big box for address {addresses}, exception {e}")
            return {}

    async def getCacheData(self, addresses: list[str]) -> dict:
        try:
            calldata_list, dependencies_list = self._create_cache_calldata(addresses)
            raw_data = await self.getMultipleAccounts(calldata_list, field=['data'], funcs={'data': lambda x: x[0]})
            return self._assemble_cache_data(raw_data, dependencies_list)
        except Exception as e:
            self.logger.error(f"Failed to get cache data for address {addresses}, exception {e}")
            return {}