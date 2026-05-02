import asyncio

####################################
from src.dex.solana.data_fetcher.api_clients.pool_medata_fetcher import PoolMetadataFetcher, PoolMetadataConfigScheme
from src.settings import config
from src.dex.tools.rpc.solana import Solana
####################################


class MeteoraDammV2Metadata(PoolMetadataFetcher):
    METEORA_DAMM_V2_URL = "https://dammv2-api.meteora.ag/pools?tokens_verified=true&order_by=volume24h&order=desc&limit=100&offset=%s"
    OFFSET = 100
    CYCLE = 3
    MARKET, VERSION = config.MARKETS.get('meteora_dammV2').values()


    def __init__(self):
        conf = PoolMetadataConfigScheme(market=self.MARKET, version=self.VERSION)
        super().__init__(conf)

    @staticmethod
    def _combine_unique(a, b):
        return list(set(a) | set(b))

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

    async def _get_chunk_pool_metadata(self, offset) -> tuple[dict, list]:
        pool_data_chunk = {}
        target_mints = []
        async with self.session.get(self.METEORA_DAMM_V2_URL % (offset, )) as response:
            if not response.status == 200:
                raise Exception(f"Error fetching metadata for {self.market} {self.version}. "
                                f"Response status: {response.status}")

            response_data = await response.json()
            data = response_data['data']

            for pool in data:
                try:
                    address = pool['pool_address']
                    token0 = pool['token_a_symbol']
                    token1 = pool['token_b_symbol']
                    mint0 = pool['token_a_mint']
                    mint1 = pool['token_b_mint']
                    volume24h = pool['volume24h']

                    if volume24h < config.MIN_VOL24:
                        continue

                    pool_data_chunk[address] = {
                        'token0': token0,
                        'token1': token1,
                        'mint0': mint0,
                        'mint1': mint1,
                        "volume24h": volume24h,
                        'dex': self.MARKET,
                        'version': self.VERSION,
                    }
                    if mint0 not in target_mints:
                        target_mints.append(mint0)
                    if mint1 not in target_mints:
                        target_mints.append(mint1)

                except Exception as e:
                    self.logger.error(f"Error parsing pool metadata for {self.market} {self.version}: {e}")
                    continue
        return pool_data_chunk, target_mints

    async def _metadata_fetcher(self):
        pools = {}
        target_mints = []
        tasks = [self._get_chunk_pool_metadata(self.OFFSET * i) for i in range(0, self.CYCLE)]

        results = await asyncio.gather(*tasks)

        for result in results:
            pool_data_chunk, mint_list = result
            pools.update(pool_data_chunk)
            target_mints = self._combine_unique(target_mints, mint_list)

        decimals_dict = await self._get_decimals(target_mints)
        if not decimals_dict:
            raise Exception(f"No decimals found for {target_mints}")

        return self._derive_final_result_dict(pools, decimals_dict)