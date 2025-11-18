####################################
from src.Config import config
from src.DataFetcher import PoolStateFetcher, PoolStateConfigScheme
from src import RaydiumHybridAMM, RaydiumBigBoxVaultAddressScheme
####################################


class RaydiumAmmState(PoolStateFetcher):
    MARKET, VERSION = config.MARKETS.get('raydium_amm').values()

    def __init__(self):
        conf = PoolStateConfigScheme(market=self.MARKET,
                                     version=self.VERSION,
                                     provider=RaydiumHybridAMM,
                                     cache_update_time=10 * 60,
                                     interval_sleep_time=1)
        super().__init__(conf)



    async def _set_up_cache(self, provider_instance: RaydiumHybridAMM, metadata: dict, addresses: list) -> bool:
        cache_data = await provider_instance.getCacheData(addresses=addresses)

        if not cache_data:
            return False

        self.buffer['addresses'] = {}
        for address, data in cache_data.items():
            baseVault = data.get('baseVault')
            quoteVault = data.get('quoteVault')
            if not baseVault or not quoteVault:
                continue

            self.buffer['addresses'][address] = RaydiumBigBoxVaultAddressScheme(
                baseVault=baseVault,
                quoteVault=quoteVault
            )
        if not self.buffer['addresses']: return False

        return True




    async def _state_fetcher(self, provider_instance: RaydiumHybridAMM, metadata: dict, addresses: list) -> dict:
        return await provider_instance.getBigBox(addresses=self.buffer['addresses'])

