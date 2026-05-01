####################################
from src.settings import config
from src.dex.solana.data_fetcher.rpc_clients.pool_state_fetcher import PoolStateFetcher, PoolStateConfigScheme
from src.dex.solana.meteora.state.meteora_dlmm import MeteoraDLMM
####################################


class MeteoraDlmmState(PoolStateFetcher):
    MARKET, VERSION = config.MARKETS.get('meteora_dlmm').values()

    def __init__(self):
        conf = PoolStateConfigScheme(market=self.MARKET,
                                     version=self.VERSION,
                                     provider=MeteoraDLMM,
                                     cache_update_time=4 * 60)
        super().__init__(conf)

    async def _set_up_cache(self, provider_instance: MeteoraDLMM, metadata: dict, addresses: list) -> bool:
        cache_data = await provider_instance.getCacheData(addresses)
        if not cache_data:
            return False

        self.cache = cache_data

        validated_addresses, bin_id_list = self._get_bin_id_and_validated_addresses_list(addresses)
        self.buffer['bin_id_list'] = bin_id_list
        self.buffer['validated_addresses'] = validated_addresses
        return True

    def _get_bin_id_and_validated_addresses_list(self, addresses: list) -> tuple[list, list]:
        bin_id_list = []
        validated_addresses = []
        for address in addresses:
            active_id = self.cache.get(address, {}).get('active_id')
            if not isinstance(active_id, int):
                self.logger.warning(f"No active_id found for {address}. Skipping.")
                continue

            validated_addresses.append(address)
            bin_id_list.append(active_id)

        return validated_addresses, bin_id_list



    async def _state_fetcher(self, provider_instance: MeteoraDLMM, metadata: dict, addresses: list) -> dict:
        validated_addresses = self.buffer.get('validated_addresses', [])
        bin_id_list = self.buffer.get('bin_id_list', [])
        if not validated_addresses or not bin_id_list:
            return {}

        state_data = await provider_instance.getBigBox(validated_addresses, bin_id_list)
        return state_data