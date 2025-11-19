from solders.pubkey import Pubkey as SolanaPubkey
from typing import List

####################################
from src.Config import config
from src.DEX.tools.rpc.Solana import Solana
from src.DEX.tools.helpers.translater import Translater
from src.LoggerHandler.logger import setup_logger, get_logger
from src.DEX.DEXes.Meteora.MeteoraScheme import LbPairDependenciesScheme
####################################

class MeteoraDLMMTranslater(Translater):
    def __init__(self, logger):
        super().__init__(logger)

    def translate_LbPair(self, x: str) -> dict:
        try:
            parsed_data = self.translate(x, market="dlmm")
            if not parsed_data: raise Exception('No parsed_data LbPair info found')
            parameters = parsed_data.get('parameters')
            v_parameters = parsed_data.get('v_parameters')
            active_id = parsed_data.get('active_id')
            bin_step = parsed_data.get('bin_step')
            oracle = parsed_data.get('oracle')

            del parameters['_padding']
            del v_parameters['_padding']
            del v_parameters['_padding_1']

            return {
                'parameters': parameters,
                'v_parameters': v_parameters,
                'active_id': active_id,
                'bin_step': bin_step,
                'oracle': oracle}
        except Exception as e:
            self.logger.error(f"Error parsing LbPair data: {e}")
            return {}

    def translate_BinArray(self, x: str | None, start_index: int) -> dict:
        if x is None:
            not_init_binArray = {}
            for i in range(config.MAX_BIN_PER_ARRAY_DLMM):
                not_init_binArray[str(start_index + i)] = {
                    "amount_x": 0,
                    "amount_y": 0,
                }
            return not_init_binArray



        try:
            parsed_data = self.translate(x, market="dlmm", name='BinArray')
            if not parsed_data: raise Exception('No parsed_data BinArray info found')
            bins_list = parsed_data.get('bins')

            binArray = {}
            for i, _bin in enumerate(bins_list):
                binArray[str(start_index + i)] = {
                    "amount_x": _bin['amount_x'],
                    "amount_y": _bin['amount_y'],
                }

            return binArray
        except Exception as e:
            self.logger.error(f"Error parsing BinArray data: {e}")
            return {}



class MeteoraDLMM(Solana):
    def __init__(self, SOLANA_RPC_ENDPOINT=config.SOLANA_RPC_ENDPOINT, logger_name='MeteoraDLMM',
                 logger_file="MeteoraDLMM.log"):
        super().__init__(SOLANA_RPC_ENDPOINT)

        setup_logger(logger_name=logger_name, log_file=f"{config.LOG_MAIN_FOLDER}{logger_file}")
        self.logger = get_logger(logger_name)
        self.translater = MeteoraDLMMTranslater(self.logger)
        self.program_id = SolanaPubkey.from_string(config.METEORA_DLMM_PROGRAM_ID)

    @staticmethod
    def bin_id_to_bin_array_index(bin_id: int) -> int:
        idx, rem = divmod(bin_id, config.MAX_BIN_PER_ARRAY_DLMM)
        return idx


    # FOR FETCHING BIG BOX
    def _create_calldata_for_LbPair(self, address: str, bin_id: int) -> LbPairDependenciesScheme:
        bin_array_index = self.bin_id_to_bin_array_index(bin_id)
        bin_array_list = [bin_array_index - 1,
                          bin_array_index,
                          bin_array_index + 1,]
        start_indexes: list[int] = [i_index * config.MAX_BIN_PER_ARRAY_DLMM for i_index in bin_array_list]

        PDA = []
        for bin_index in bin_array_list:
            PDA.append(self.findProgramDerivedAddress([b"bin_array", bytes(SolanaPubkey.from_string(address)),
                                            bin_index.to_bytes(8, 'little', signed=True)],
                                           self.program_id))

        LbPair = [address]
        dependencies = LbPairDependenciesScheme(
            Address=address,
            PDA=PDA,
            LbPair=LbPair,
            start_indexes=start_indexes,
        )
        return dependencies

    def _create_calldata(self, addresses: list, bin_id_list: list) -> tuple[list, List[LbPairDependenciesScheme]]:
        dependencies_list = []
        calldata_list = []
        if len(addresses) != len(bin_id_list):
            self.logger.error(f"Addresses and bin_id_list and bin_step_list must have same length")
            return calldata_list, dependencies_list


        for i, address in enumerate(addresses):
            bin_id = bin_id_list[i]

            try:
                dependencies = self._create_calldata_for_LbPair(address, bin_id)
                PDA = dependencies.PDA
                LbPair = dependencies.LbPair
                calldata = LbPair + PDA

                calldata_list.extend(calldata)
                dependencies_list.append(dependencies)
            except Exception as e:
                self.logger.warning(f'Error creating calldata for address {address} with bin_id {bin_id}: {e}')
                continue

        return calldata_list, dependencies_list

    def _assemble_LbPair_data(self, raw_data: dict, dependencies_list: List[LbPairDependenciesScheme], ) -> dict:
        final_assembled_pools = {}

        for dependencies in dependencies_list:
            address = dependencies.Address
            PDA = dependencies.PDA
            LbPair = dependencies.LbPair[0]
            start_indexes = dependencies.start_indexes

            raw_LbPair_info = raw_data.get(LbPair, [{}])[0].get('data')
            if not raw_LbPair_info:
                self.logger.error(f"LbPair info for address {address} has no data")
                continue
            LbPair_info = self.translater.translate_LbPair(raw_LbPair_info)
            if not LbPair_info:
                self.logger.error(f"LbPair info for address {address} couldn't be translated")
                continue

            binArrays = {}
            for i, pda in enumerate(PDA):
                if pda not in raw_data:
                    self.logger.error(f"PDA({pda}) info was not found in Solana response. "
                                      f"Maybe there was some error problem the request in RPC part.")
                    continue

                raw_pda_info = raw_data.get(pda, [{}])[0].get('data')
                binArray_info = self.translater.translate_BinArray(raw_pda_info, start_indexes[i])
                if not binArray_info:
                    self.logger.error(f"BinArray({pda}) info for address {address} couldn't be translated")
                    continue
                binArrays.update(binArray_info)

            if not binArrays:
                self.logger.error(f"BinArray({PDA}) info for address {address} could not be found")
                continue


            final_assembled_pools[address] = {
                'LbPair': LbPair_info,
                'bins': binArrays
            }

        return final_assembled_pools



    ######################


    async def getCacheData(self, addresses: list) -> dict:
        raw_data = await self.getMultipleAccounts(addresses, ['data'], {'data': lambda x: x[0]})
        final_assembled_cache_data = {}

        for address, data_list in raw_data.items():
            try:
                data = data_list[0].get('data')
                parsed_data = self.translater.translate_LbPair(data)
                if not parsed_data: continue
                final_assembled_cache_data[address] = parsed_data
            except Exception as e:
                self.logger.error(f"Error parsing LbPair data for address {address}: {e}")
                continue

        return final_assembled_cache_data

    async def getBigBox(self, addresses: list, bin_id_list: list) -> dict:
        try:
            calldata_list, dependencies_list = self._create_calldata(addresses, bin_id_list)
        except Exception as e:
            self.logger.error(f"Error creating calldata: {e}")
            return {}

        raw_data = await self.getMultipleAccounts(calldata_list, ['data'], {'data': lambda x: x[0]})
        return self._assemble_LbPair_data(raw_data, dependencies_list)