####################################
from src.DataFetcher import PoolMetadataFetcher, PoolMetadataConfigScheme
from src.Config import config
from src import Solana
####################################


class MeteoraDlmmMetadata(PoolMetadataFetcher):
    METEORA_URL = "https://dlmm.datapi.meteora.ag/pools?page=1&page_size=500"
    MARKET, VERSION = config.MARKETS.get('meteora_dlmm').values()

    def __init__(self):
        conf = PoolMetadataConfigScheme(market=self.MARKET, version=self.VERSION)
        super().__init__(conf)

    async def _metadata_fetcher(self):
        pools = {}
        target_mints = []
        async with self.session.get(self.METEORA_URL) as response:
            if not response.status == 200:
                raise Exception(f"Error fetching metadata for {self.market} {self.version}. "
                                f"Response status: {response.status}")

            response_data = await response.json()
            for pool in response_data.get("data", []):
                try:
                    is_blacklisted = pool["is_blacklisted"]
                    trade_volume_24h = pool["volume"]["24h"]
                    if is_blacklisted:
                        continue
                    if trade_volume_24h < config.MIN_VOL24:
                        continue

                    self.logger.info(f"Processing pool: {pool['address']}")
                    address = pool["address"]

                    token_x = pool["token_x"]
                    token_y = pool["token_y"]

                    token0 = token_x["symbol"]
                    token1 = token_y["symbol"]

                    mint0 = token_x["address"]
                    mint1 = token_y["address"]

                    decimals0 = token_x["decimals"]
                    decimals1 = token_y["decimals"]

                    pools[address] = {
                        "token0": token0,
                        "token1": token1,
                        "mint0": mint0,
                        "mint1": mint1,
                        "decimals0": decimals0,
                        "decimals1": decimals1,
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

        return pools