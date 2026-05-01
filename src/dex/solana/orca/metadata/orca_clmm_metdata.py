####################################
from src.dex.solana.data_fetcher.api_clients.pool_medata_fetcher import PoolMetadataFetcher, PoolMetadataConfigScheme
from src.settings import config
####################################


class OrcaClmmMetadata(PoolMetadataFetcher):
    ORCA_BASE_URL = 'https://api.orca.so/v2/solana/pools?sortBy=volume24h&sortDirection=desc&hasWarning=false'
    ORCA_CLMM_URL = "https://api.orca.so/v2/solana/pools?sortBy=volume24h&sortDirection=desc&next=%s&hasWarning=false"

    CYCLE = 4
    MARKET, VERSION = config.MARKETS.get('orca_clmm').values()

    def __init__(self):
        conf = PoolMetadataConfigScheme(market=self.MARKET, version=self.VERSION)
        super().__init__(conf)

    async def _get_chunk_pool_metadata(self, pointer: str = None) -> tuple[dict, str]:
        pools = {}
        next_pointer: str
        url = self.ORCA_CLMM_URL % (pointer, ) if pointer else self.ORCA_BASE_URL

        async with self.session.get(url) as response:
            if not response.status == 200:
                raise Exception(f"Error fetching metadata for {self.MARKET} {self.VERSION}. "
                                f"Response status: {response.status}")
            response_data = await response.json()
            data = response_data['data']
            meta = response_data['meta']

            next_pointer = meta['cursor']['next']

            for pool in data:
                try:
                    address = pool['address']
                    feeRate = pool['feeRate']
                    poolType = pool['poolType']
                    adaptiveFeeEnabled = pool['adaptiveFeeEnabled']
                    if poolType != "whirlpool":
                        continue

                    if feeRate > 10_000:
                        continue

                    stats = pool['stats']
                    volume24h = float(stats["24h"]['volume'])
                    if volume24h < config.MIN_VOL24:
                        continue

                    tokenA = pool['tokenA']
                    tokenB = pool['tokenB']

                    token0 = tokenA['symbol']
                    decimals0 = tokenA['decimals']
                    mint0 = tokenA['address']

                    token1 = tokenB['symbol']
                    decimals1 = tokenB['decimals']
                    mint1 = tokenB['address']

                    pools[address] = {
                        "token0": token0,
                        "token1": token1,
                        "mint0": mint0,
                        "mint1": mint1,
                        "decimals0": decimals0,
                        "decimals1": decimals1,
                        "feeRate": feeRate,
                        "poolType": poolType,
                        "volume24h": volume24h,
                        'af': adaptiveFeeEnabled,
                        "dex": self.MARKET,
                        "version": self.VERSION,
                    }



                except Exception as e:
                    self.logger.error(f"Error parsing pool metadata for {self.MARKET} {self.VERSION}: {e}")
                    continue

        return pools, next_pointer


    async def _metadata_fetcher(self):
        pools = {}
        next_pointer = None


        for i in range(0, self.CYCLE):
            pool_data_chunk, next_pointer = await self._get_chunk_pool_metadata(pointer=next_pointer)
            pools.update(pool_data_chunk)

        if not pools:
            raise Exception(f"No valid pools found for {self.MARKET} {self.VERSION}.")

        return pools