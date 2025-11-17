####################################
from src.Config import config
from src.DataFetcher import PoolStateFetcher, PoolStateConfigScheme
from src import RaydiumCLMM
####################################


class RaydiumClmmState(PoolStateFetcher):
    MARKET, VERSION = config.MARKETS.get('raydium_clmm').values()

    def __init__(self):
        conf = PoolStateConfigScheme(market=self.MARKET,
                                     version=self.VERSION,
                                     provider=RaydiumCLMM,
                                     cache_update_time=4 * 60)
        super().__init__(conf)


    async def _set_up_cache(self, provider_instance: RaydiumCLMM, metadata: dict, addresses: list) -> bool:
        cache_data = await provider_instance.getCacheData(addresses=addresses)
        if not cache_data:
            return False

        self.cache = cache_data
        tick_spacing_list, tick_current_list, valid_addresses = self._get_BigBox_attributes()
        if not valid_addresses or not tick_spacing_list or not tick_current_list:
            return False

        self.buffer['tick_spacing_list'] = tick_spacing_list
        self.buffer['tick_current_list'] = tick_current_list
        self.buffer['valid_addresses'] = valid_addresses
        return True

    def _get_BigBox_attributes(self) -> tuple[list, list, list]:
        tick_spacing_list = []
        tick_current_list = []
        valid_addresses = []
        for address, data in self.cache.items():
            tick_spacing = data.get('tick_spacing')
            tick_current = data.get('tick_current')
            if tick_spacing is None or tick_current is None:
                continue

            tick_spacing_list.append(tick_spacing)
            tick_current_list.append(tick_current)
            valid_addresses.append(address)

        return tick_spacing_list, tick_current_list, valid_addresses

    async def _state_fetcher(self, provider_instance: RaydiumCLMM, metadata: dict, addresses: list) -> dict:
        return await provider_instance.getBigBox(addresses=self.buffer['valid_addresses'],
                                                 current_tick_list=self.buffer['tick_current_list'],
                                                 tick_spacing_list=self.buffer['tick_spacing_list'])
