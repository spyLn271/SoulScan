####################################
from src.settings import config
from src.dex.solana.data_fetcher.rpc_clients.pool_state_fetcher import PoolStateFetcher, PoolStateConfigScheme
from src.dex.solana.meteora.state.meteora_damm_v2 import MeteoraDAMMv2
####################################


class MeteoraDammV2State(PoolStateFetcher):
    MARKET, VERSION = config.MARKETS.get('meteora_dammV2').values()

    def __init__(self):
        conf = PoolStateConfigScheme(market=self.MARKET,
                                     version=self.VERSION,
                                     provider=MeteoraDAMMv2,
                                     cache_update_time=10 * 60,
                                     interval_sleep_time=1)
        super().__init__(conf)


    async def _set_up_cache(self, provider_instance, metadata: dict, addresses: list) -> bool:
        return True

    async def _state_fetcher(self, provider_instance: MeteoraDAMMv2, metadata: dict, addresses: list) -> dict:
        state_data = await provider_instance.getBigBox(addresses=addresses)
        return state_data