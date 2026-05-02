import redis
import aiohttp
import asyncio
import json

##########################################
from src.logger_handler.logger import get_logger, setup_logger
from src.settings.config import (SUPPORTED_EVM_MARKETS,
                                 EVM_NATIVE_TOKEN_ADDRESSES,
                                 EVM_PARENT,
                                 MARKETS,
                                 MIN_VOL24,
                                 GECKO_DEX_IDS,
                                 REDIS_METADATA_KEY)
from src.dex.evm.data_fetcher.metadata.metadata import MetadataDict
from src.settings.config import get_config
##########################################

_config = get_config()

API_ENDPOINT = "https://api.geckoterminal.com/api/v2/networks/%s/dexes/%s/pools?include=base_token,quote_token&sort=h24_volume_usd_desc&page=%s"

class CoingeckoEvmFetcher:
    def __init__(self):
        setup_logger(
            log_file=f"{_config.DATA_FETCHER_LOG_FOLDER}/coingecko_evm_fetcher.log",
            logger_name="coingecko_evm_fetcher"
        )

        self.logger = get_logger("coingecko_evm_fetcher")

        self.session: aiohttp.ClientSession
        self._is_session_open = False

        self.r = redis.Redis(host=_config.REDIS.HOST, port=_config.REDIS.PORT)


    async def __aenter__(self):
        if not self._is_session_open:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            self._is_session_open = True
            self.logger.info("PoolMetadataFetcher session opened.")
        else:
            self.logger.warning("PoolMetadataFetcher session already open.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._is_session_open:
            self._is_session_open = False
            await self.session.close()
            self.logger.info("PoolMetadataFetcher session closed.")
        else:
            self.logger.warning("PoolMetadataFetcher session already closed.")


    def _save_metadata(
            self,
            metadata: dict,
            market: str,
            version: str
    ) -> bool:
        if not metadata:
            self.logger.error(f"No metadata found for {market} {version}.")
            return False

        try:
            self.logger.info(f"Saving metadata for {market} {version} to redis. "
                             f"Saving data length: {len(metadata)}.")
            self.r.set(REDIS_METADATA_KEY % (market, version), json.dumps(metadata))
            self.logger.info(f"Metadata for {market} {version} saved.")
            return True
        except Exception as e:
            self.logger.error(f"Error saving metadata for {market} {version}: {e}")
            return False

    def _normalize_included(
            self,
            included: list
    ) -> dict:
        normalized_included = {}

        for data in included:
            try:
                _id = data.get("id")
                attributes = data.get("attributes", {})
                normalized_included[_id] = attributes

            except Exception as e:
                self.logger.error(f"Error normalizing included data({data}): {e}")

        return normalized_included

    async def fetch_metadata(
            self,
            network: str,
            gecko_dex_id: str,
            dex: str,
            version: str,
    ) -> dict[str, MetadataDict]:

        headers = {"x-cg-pro-api-key": _config.COINGECKO_API}
        async def fetch_page(_page: int):
            url = API_ENDPOINT % (network, gecko_dex_id, _page)

            async with self.session.get(url=url, headers=headers) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(
                        f"Error fetching metadata for {gecko_dex_id} {network}. "
                        f"Page: {_page}. Status: {response.status}. Body: {text[:500]}"
                    )

                return await response.json()


        while True:
            tasks = [fetch_page(page) for page in range(1, 11)]

            try:
                res = await asyncio.gather(*tasks)
                break

            except Exception as e:
                for task in tasks:
                    if isinstance(task, asyncio.Task):
                        task.cancel()

                await asyncio.gather(*tasks, return_exceptions=True)

                self.logger.error(f"Error fetching metadata for {gecko_dex_id} {network}: {e}")
                self.logger.info(f"Sleeping for 60 seconds.")
                await asyncio.sleep(60)


        market_metadata: dict[str, MetadataDict] = {}
        for result in res:
            if not isinstance(result, dict):
                self.logger.error(f"Error fetching metadata for {gecko_dex_id} {network}: {result}")
                continue

            data = result.get("data", [])
            included = self._normalize_included(result.get("included", []))
            for pool in data:
                try:
                    attributes = pool["attributes"]
                    relationships = pool["relationships"]

                    pool_address = attributes["address"]
                    volume24h = float(attributes["volume_usd"]["h24"])
                    tvl = float(attributes["reserve_in_usd"])

                    base_token_id = relationships["base_token"]["data"]["id"]
                    quote_token_id = relationships["quote_token"]["data"]["id"]

                    token0 = included[base_token_id]["symbol"]
                    decimals0 = int(included[base_token_id]["decimals"])
                    addr0 = included[base_token_id]["address"].lower()

                    token1 = included[quote_token_id]["symbol"]
                    decimals1 = int(included[quote_token_id]["decimals"])
                    addr1 = included[quote_token_id]["address"].lower()

                    network_native_token_alies = EVM_NATIVE_TOKEN_ADDRESSES[network]["alias"]
                    network_native_token_alies_addr = EVM_NATIVE_TOKEN_ADDRESSES[network]["alias_addresses"]

                    if token0 in network_native_token_alies and addr0 in network_native_token_alies_addr:
                        token0 = EVM_NATIVE_TOKEN_ADDRESSES[network]["symbol"]
                        addr0 = EVM_NATIVE_TOKEN_ADDRESSES[network]["address"]
                    elif token1 in network_native_token_alies and addr1 in network_native_token_alies_addr:
                        token1 = EVM_NATIVE_TOKEN_ADDRESSES[network]["symbol"]
                        addr1 = EVM_NATIVE_TOKEN_ADDRESSES[network]["address"]


                    if volume24h < MIN_VOL24:
                        continue

                    market_metadata[pool_address] = MetadataDict(
                        token0=token0,
                        token1=token1,
                        decimals0=decimals0,
                        decimals1=decimals1,
                        mint0=addr0,
                        mint1=addr1,
                        volume24h=volume24h,
                        tvl=tvl,
                        dex=dex,
                        version=version,
                    )

                except Exception as e:
                    self.logger.error(f"Error parsing metadata for {gecko_dex_id} {network}: {e}")
                    continue

        self.logger.info(f"Fetched metadata for {gecko_dex_id} {network}. Length: {len(market_metadata)}.")

        return market_metadata


    async def main(self):
        while True:
            try:
                evm_metadata = {}

                for market in SUPPORTED_EVM_MARKETS:
                    network, dex, version = market.split("_")

                    parent_market = EVM_PARENT.get(market, market)

                    gecko_dex_id = GECKO_DEX_IDS[network][dex][version]

                    self.logger.info(f"Fetching metadata for {market}...")

                    metadata = await self.fetch_metadata(network, gecko_dex_id, dex, version)

                    evm_metadata.setdefault(parent_market, {}).update(metadata)

                    self.logger.info(f"Sleeping for 90 seconds. Because of rate limit of this bullshit coingecko api.")
                    await asyncio.sleep(90)

                for market, metadata in evm_metadata.items():
                    self._save_metadata(metadata, MARKETS[market]["market"], MARKETS[market]["version"])

            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                self.logger.info(f"Sleeping for 1800 seconds.")
                await asyncio.sleep(1800)