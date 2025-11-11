from solders.pubkey import Pubkey as SolanaPubkey
import pydantic

####################################
from src.Config import config
from src.DEX.tools.rpc.Solana import Solana
from src.DEX.tools.helpers.translater import Translater
from src.LoggerHandler.logger import setup_logger, get_logger
from src.DEX.DEXes.Orca.OrcaScheme import WhirlpoolDependenciesScheme, WhirlpoolCacheDependenciesScheme
####################################


class OrcaCLMMTranslater(Translater):
    def __init__(self, logger):
        super().__init__(logger)

    def tick_array_func(self, x: str, _tick_spacing, _start_indexes) -> dict:
        try:
            parsed_data = self.translate(x, market="orca")
            if not parsed_data: raise Exception('No parsed_data tick_array info found')

            ticks = parsed_data.get('ticks')
            ticks_dict = {}
            for pos, tick in enumerate(ticks):
                ticks_dict[str(_start_indexes + pos * _tick_spacing)] = {
                    'initialized': tick.get('initialized'),
                    'liquidityNet': tick.get('liquidityNet'),
                    'liquidityGross': tick.get('liquidityGross'),
                    'feeGrowthOutsideA': tick.get('feeGrowthOutsideA'),
                    'feeGrowthOutsideB': tick.get('feeGrowthOutsideB'),
                }
            return ticks_dict

        except Exception as e:
            self.logger.error(f"Error parsing TickArray data: {e}")
            return {}

    def base_info_func(self, x: str) -> dict:
        try:
            parsed_data = self.translate(x, market="orca")
            if not parsed_data: raise Exception('No parsed_data base info found')

            base_info_dict = {
                'tickSpacing': parsed_data.get('tickSpacing'),
                'feeRate': parsed_data.get('feeRate'),
                'liquidity': parsed_data.get('liquidity'),
                'sqrtPrice': parsed_data.get('sqrtPrice'),
                'tickCurrentIndex': parsed_data.get('tickCurrentIndex'),
                'rewardLastUpdatedTimestamp': parsed_data.get('rewardLastUpdatedTimestamp')
            }

            return base_info_dict
        except Exception as e:
            self.logger.error(f"Error parsing BaseInfo data: {e}")
            return {}

    def oracle_func(self, x: str) -> dict:
        try:
            parsed_data = self.translate(x, name="Oracle", market="orca")
            if not parsed_data: raise Exception("No dparsed_data oracle info found")

            adaptiveFeeConstants = parsed_data.get('adaptiveFeeConstants', {})
            adaptiveFeeVariables = parsed_data.get('adaptiveFeeVariables', {})

            del adaptiveFeeConstants['reserved']
            del adaptiveFeeVariables['reserved']
            oracle_dict = {
                'adaptiveFeeConstants': adaptiveFeeConstants,
                'adaptiveFeeVariables': adaptiveFeeVariables

            }
            return oracle_dict
        except Exception as e:
            self.logger.error(f"Error parsing TickArray data: {e}")
            return {}

class OrcaCLMM(Solana):
    def __init__(self, SOLANA_RPC_ENDPOINT=config.SOLANA_RPC_ENDPOINT, logger_name='OrcaCLMM',
                 logger_file="OrcaCLMM.log"):
        super().__init__(SOLANA_RPC_ENDPOINT)

        setup_logger(logger_name=logger_name, log_file=f'{config.LOG_MAIN_FOLDER}{logger_file}')
        self.translater = OrcaCLMMTranslater(logger=logger_name)
        self.logger = get_logger(logger_name)
        self.program_id = SolanaPubkey.from_string(config.ORCA_CLMM_PROGRAM_ID)

    @staticmethod
    def _get_start_index(current_tick, tick_spacing) -> int:
        return int((current_tick // (config.TICK_ARRAY_SIZE_ORCA_CLMM * tick_spacing)) *
                   (config.TICK_ARRAY_SIZE_ORCA_CLMM * tick_spacing))

    @staticmethod
    def _get_offset(tick_spacing) -> int:
        return int(config.TICK_ARRAY_SIZE_ORCA_CLMM * tick_spacing)


    # FOR FETCHING BIG BOX
    def _create_calldata_for_whirlpool(self, address: str, tick_spacing: int,
                                       current_tick: int, af: bool = False) -> WhirlpoolDependenciesScheme:
        start_index = self._get_start_index(current_tick, tick_spacing)
        offset = self._get_offset(tick_spacing)
        start_indexes = [start_index - 2 * offset, start_index - 1 * offset, start_index,
                         start_index + 1 * offset, start_index + 2 * offset, ]

        baseInfo = [address]
        Oracle = []
        PDAs = []
        for start_index in start_indexes:
            PDAs.append(self.findProgramDerivedAddress([b"tick_array", bytes(SolanaPubkey.from_string(address)),
                                                        str(start_index).encode()], self.program_id))

        if af:
            Oracle = [
                self.findProgramDerivedAddress([b"oracle", bytes(SolanaPubkey.from_string(address))], self.program_id)]

        dependencies = WhirlpoolDependenciesScheme(Address=address,
                                                   PDAs=PDAs,
                                                   BaseInfo=baseInfo,
                                                   Oracle=Oracle,
                                                   start_indexes=start_indexes,
                                                   tick_spacing=tick_spacing)

        return dependencies

    def _assemble_whirlpool_data(self, raw_data: dict, dependencies_list: list[WhirlpoolDependenciesScheme],
                                 af: bool = False) -> dict:
        final_assembled_pools = {}

        for dependencies in dependencies_list:
            address = dependencies.Address
            tick_spacing = dependencies.tick_spacing
            start_indexes = dependencies.start_indexes
            base_info = dependencies.BaseInfo
            oracle = dependencies.Oracle
            pdas = dependencies.PDAs

            processed_data = {address: {}}
            raw_base_info = raw_data.get(base_info[0], [{}])[0].get('data')
            if not raw_base_info:
                self.logger.error(f"No BaseInfo data found for address {address}.")
                continue
            base_info_data = self.translater.base_info_func(raw_base_info)
            if not base_info_data:
                self.logger.error(f"Error parsing BaseInfo data for address {address}.")
                continue
            processed_data[address]['base_info'] = base_info_data

            if af:
                raw_oracle = raw_data.get(oracle[0], [{}])[0].get('data')
                if not raw_oracle:
                    self.logger.error(f"No Oracle data found for address {address}.")
                    continue
                oracle_data = self.translater.oracle_func(raw_oracle)
                if not oracle_data:
                    self.logger.error(f"Error parsing Oracle data for address {address}.")
                    continue
                processed_data[address]['oracle'] = oracle_data

            tick_arrays = {}
            for i, pda in enumerate(pdas):
                raw_tick_array = raw_data.get(pda, [{}])[0].get('data')
                if not raw_tick_array:
                    self.logger.error(f"No TickArray data found for address {address}.")
                    continue
                tick_array_data = self.translater.tick_array_func(raw_tick_array, tick_spacing, start_indexes[i])
                if not tick_array_data:
                    self.logger.error(f"Error parsing TickArray data for address {address}.")
                    continue

                tick_arrays.update(tick_array_data)

            if not tick_arrays:
                self.logger.error(f"No TickArray data found for address {address}.")
                continue

            processed_data[address]['ticks'] = tick_arrays
            final_assembled_pools.update(processed_data)

        return final_assembled_pools

    def _create_calldata(self, addresses: list, tick_spacing_list: list, current_tick_list: list,
                         af: bool = False) -> tuple[list, list[WhirlpoolDependenciesScheme]]:
        if len(addresses) != len(tick_spacing_list) or len(addresses) != len(current_tick_list):
            self.logger.error("addresses, tick_spacing_list and current_tick_list must have the same length.")
            raise Exception("addresses, tick_spacing_list and current_tick_list must have the same length.")

        dependencies_list = []
        calldata_list = []

        for i, address in enumerate(addresses):
            try:
                dependencies = self._create_calldata_for_whirlpool(address, tick_spacing_list[i],
                                                                   current_tick_list[i], af)
                dependencies_list.append(dependencies)
                PDAs = dependencies.PDAs
                Oracle = dependencies.Oracle
                BaseInfo = dependencies.BaseInfo
                calldata = PDAs + Oracle + BaseInfo
                calldata_list.extend(calldata)
            except Exception as e:
                self.logger.error(f"Error creating calldata for address {address}: {e}")
                continue

        return calldata_list, dependencies_list

    ######################



    # FOR ESTABLISHING CACHE DATA
    def _create_cache_calldata_for_whirlpool(self, address: str,
                                             af: bool = False) -> WhirlpoolCacheDependenciesScheme:
        BaseInfo = [address]
        Oracle = []
        if af:
            Oracle = [
                self.findProgramDerivedAddress([b"oracle", bytes(SolanaPubkey.from_string(address))],
                                               self.program_id)]

        return WhirlpoolCacheDependenciesScheme(Address=address, BaseInfo=BaseInfo, Oracle=Oracle)

    def _create_cache_calldata(self, addresses: list,
                               af: bool = False) -> tuple[list, list[WhirlpoolCacheDependenciesScheme]]:
        dependencies_list = []
        calldata_list = []

        for address in addresses:
            try:
                dependencies = self._create_cache_calldata_for_whirlpool(address, af)

                dependencies_list.append(dependencies)
                Oracle = dependencies.Oracle
                BaseInfo = dependencies.BaseInfo
                calldata = Oracle + BaseInfo
                calldata_list.extend(calldata)
            except Exception as e:
                self.logger.error(f"Error creating calldata for address {address}: {e}")
                continue


        return calldata_list, dependencies_list

    def _assemble_cache_data(self, raw_data: dict, dependencies_list: list[WhirlpoolCacheDependenciesScheme],
                             af: bool = False) -> dict:
        final_assembled_cache_data = {}

        for dependencies in dependencies_list:
            address = dependencies.Address
            base_info = dependencies.BaseInfo
            oracle = dependencies.Oracle

            processed_data = {address: {}}
            raw_base_info = raw_data.get(base_info[0], [{}])[0].get('data')
            if not raw_base_info:
                self.logger.error(f"No BaseInfo data found for address {address}.")
                continue
            base_info_data = self.translater.base_info_func(raw_base_info)
            if not base_info_data:
                self.logger.error(f"Error parsing BaseInfo data for address {address}.")
                continue
            processed_data[address]['base_info'] = base_info_data


            if af:
                raw_oracle = raw_data.get(oracle[0], [{}])[0].get('data')
                if not raw_oracle:
                    self.logger.error(f"No Oracle data found for address {address}.")
                oracle_data = self.translater.oracle_func(raw_oracle)
                if not oracle_data:
                    self.logger.error(f"Error parsing Oracle data for address {address}.")
                    continue
                processed_data[address]['oracle'] = oracle_data

            final_assembled_cache_data.update(processed_data)

        return final_assembled_cache_data

    ######################



    async def getCacheData(self, addresses: list, af: bool = False) -> dict:
        calldata_list, dependencies_list = self._create_cache_calldata(addresses, af)
        raw_result = await self.getMultipleAccounts(calldata_list, ['data'], {'data': lambda x: x[0]})

        return self._assemble_cache_data(raw_result, dependencies_list, af)


    async def getBigBox(self, addresses: list, current_tick_list: list,
                        tick_spacing_list: list, af: bool = False) -> dict:
        try:
            calldata_list, dependencies_list = self._create_calldata(addresses, tick_spacing_list,
                                                                     current_tick_list, af)
        except Exception as e:
            self.logger.error(f"Error creating calldata: {e}")
            return {}
        raw_result = await self.getMultipleAccounts(calldata_list, ['data'], {'data': lambda x: x[0]})

        return self._assemble_whirlpool_data(raw_result, dependencies_list, af)