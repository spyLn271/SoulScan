####################################
from src.DataFetcher import PoolMetadataFetcher, PoolMetadataConfigScheme
from src.Config import config
####################################


class RaydiumHybridAmmMetadata(PoolMetadataFetcher):
    RAYDIUM_HYBRID_AMM_URL = "https://api-v3.raydium.io/pools/info/list-v2?poolType=Standard&sortField=volume24h&sortType=desc&size=500"
    MARKET, VERSION = config.MARKETS.get('raydium_amm').values()

    def __init__(self):
        conf = PoolMetadataConfigScheme(market=self.MARKET, version=self.VERSION)
        super().__init__(conf)

    async def _metadata_fetcher(self):
        pools = {}
        async with self.session.get(self.RAYDIUM_HYBRID_AMM_URL) as response:
            if not response.status == 200:
                raise Exception(f"Error fetching metadata for {self.MARKET} {self.VERSION}. "
                                f"Response status: {response.status}")

            response_data = await response.json()
            is_success = response_data['success']
            if not is_success:
                raise Exception(f"Error fetching metadata for {self.MARKET} {self.VERSION}. "
                                f"Success is False (is_success: {is_success}).")

            data = response_data['data']['data']

        for pool in data:
            try:
                address = pool['id']
                tokenA = pool['mintA']
                tokenB = pool['mintB']
                day = pool['day']
                feeRate = pool['feeRate']
                tvl = float(pool['tvl'])
                if tvl < config.MIN_TVL: continue

                token0 = 'SOL' if tokenA['symbol'] == 'WSOL' else tokenA['symbol']
                decimals0 = tokenA['decimals']
                mint0 = tokenA['address']

                token1 = 'SOL' if tokenB['symbol'] == 'WSOL' else tokenB['symbol']
                decimals1 = tokenB['decimals']
                mint1 = tokenB['address']

                volume24h = float(day['volume'])
                if volume24h < config.MIN_VOL24: continue

                pools[address] = {
                    "token0": token0,
                    "token1": token1,
                    "mint0": mint0,
                    "mint1": mint1,
                    "decimals0": decimals0,
                    "decimals1": decimals1,
                    "feeRate": feeRate,
                    "volume24h": volume24h,
                    "dex": self.MARKET,
                    "version": self.VERSION,
                }
            except Exception as e:
                self.logger.error(f"Error parsing pool metadata for {self.MARKET} {self.VERSION}: {e}")
                continue

        if not pools:
            raise Exception(f"No valid pools found for {self.MARKET} {self.VERSION}.")

        return pools