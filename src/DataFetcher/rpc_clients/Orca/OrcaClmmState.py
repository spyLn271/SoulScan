####################################
from src.Config import config
from src.DataFetcher import PoolStateFetcher, PoolStateConfigScheme
from src import OrcaCLMM
####################################



class OrcaClmmState(PoolStateFetcher):
    MARKET, VERSION = config.MARKETS.get('orca_clmm').values()
    def __init__(self):
        conf = PoolStateConfigScheme(market=self.MARKET,
                                     version=self.VERSION,
                                     provider=OrcaCLMM,
                                     cache_update_time=4 * 60,
                                     interval_sleep_time=1)
        super().__init__(conf)


    async def _set_up_cache(self, provider_instance: OrcaCLMM, metadata: dict, addresses: list) -> bool:
        cache_data = await provider_instance.getCacheData(addresses=addresses)
        if not cache_data:
            return False

        self.cache = cache_data
        af_list, tick_spacing_list, tick_current_list, valid_addresses = self._get_BigBox_attributes(metadata)
        if not valid_addresses or not af_list or not tick_spacing_list or not tick_current_list:
            return False

        self.buffer['af_list'] = af_list
        self.buffer['tick_spacing_list'] = tick_spacing_list
        self.buffer['tick_current_list'] = tick_current_list
        self.buffer['valid_addresses'] = valid_addresses
        return True

    def _get_BigBox_attributes(self, metadata: dict) -> tuple[list, list, list, list]:
        af_list = []
        tick_spacing_list = []
        tick_current_list = []
        valid_addresses = []
        for address, data in self.cache.items():
            base_info = data.get('base_info')
            af = metadata.get(address, {}).get('af')
            if not base_info or af is None:
                continue

            tick_spacing = base_info.get('tickSpacing')
            tick_current = base_info.get('tickCurrentIndex')
            if tick_spacing is None or tick_current is None:
                continue

            af_list.append(af)
            tick_spacing_list.append(tick_spacing)
            tick_current_list.append(tick_current)
            valid_addresses.append(address)

        return af_list, tick_spacing_list, tick_current_list, valid_addresses






    async def _state_fetcher(self, provider_instance: OrcaCLMM, metadata: dict, addresses: list) -> dict:
        state_data = await provider_instance.getBigBox(addresses=self.buffer['valid_addresses'],
                                                       current_tick_list=self.buffer['tick_current_list'],
                                                       tick_spacing_list=self.buffer['tick_spacing_list'],
                                                       af_list=self.buffer['af_list'])
        return state_data