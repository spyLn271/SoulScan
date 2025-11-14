####################################
from src.DataFetcher import PoolMetadataFetcher, PoolMetadataConfigScheme
from src.Config import config
from src import Solana
####################################


class MeteoraDlmmMetadata(PoolMetadataFetcher):
    METEORA_URL = "https://dlmm-api.meteora.ag/pair/all?include_unknown=true"
    MARKET, VERSION = config.MARKETS.get('meteora_dlmm').values()

    def __init__(self):
        conf = PoolMetadataConfigScheme(market=self.MARKET, version=self.VERSION)
        super().__init__(conf)

    async def _get_decimals(self, target_mints: list) -> dict:
        decimals_dict = {}
        async with Solana(logger=self.logger) as solana:
            mints = await solana.getMultipleMintAccounts(target_mints)

        if not mints:
            raise Exception(f"No mints found for {target_mints}")

        for address, mint in mints.items():
            try:
                data = mint[0]['data']
                decimals = data['decimals']
                decimals_dict[address] = decimals
            except Exception as e:
                self.logger.error(e)
                continue

        if not decimals_dict:
            raise Exception(f"No decimals found for {mints}")

        return decimals_dict

    def _derive_final_result_dict(self, pools: dict, decimals_dict: dict) -> dict:
        final_result_dict = {}
        for address, pool in pools.items():
            try:
                mint0 = pool["mint0"]
                mint1 = pool["mint1"]

                decimals0 = decimals_dict[mint0]
                decimals1 = decimals_dict[mint1]
                final_result_dict[address] = {**pool, **{'decimals0': decimals0, "decimals1": decimals1}}
            except Exception as e:
                self.logger.error(e)
                continue

        if not final_result_dict:
            raise Exception(f"No valid pools found for {self.market} {self.version}.")

        return final_result_dict

    async def _metadata_fetcher(self):
        pools = {}
        target_mints = []
        async with self.session.get(self.METEORA_URL) as response:
            if not response.status == 200:
                raise Exception(f"Error fetching metadata for {self.market} {self.version}. "
                                f"Response status: {response.status}")

            response_data = await response.json()
            for pool in response_data:
                try:
                    is_blacklisted = pool["is_blacklisted"]
                    trade_volume_24h = pool["trade_volume_24h"]
                    if is_blacklisted:
                        continue
                    if trade_volume_24h < config.MIN_VOL24:
                        continue

                    address = pool["address"]
                    token0, token1 = pool["name"].split('-')
                    mint0 = pool["mint_x"]
                    mint1 = pool["mint_y"]

                    pools[address] = {
                        "token0": token0,
                        "token1": token1,
                        "mint0": mint0,
                        "mint1": mint1,
                        "is_blacklisted": is_blacklisted,
                        "volume24h": trade_volume_24h,
                        "dex": self.MARKET,
                        "version": self.VERSION,
                    }
                    if mint0 not in target_mints:
                        target_mints.append(mint0)
                    if mint1 not in target_mints:
                        target_mints.append(mint1)

                except Exception as e:
                    self.logger.error(f"Error parsing pool metadata for {self.market} {self.version}: {e}")
                    continue
        if not target_mints:
            raise Exception(f"No valid pools found for {self.market} {self.version}.")

        decimals_dict = await self._get_decimals(target_mints)
        if not decimals_dict:
            raise Exception(f"No decimals found for {self.market} {self.version}.")


        return self._derive_final_result_dict(pools, decimals_dict)