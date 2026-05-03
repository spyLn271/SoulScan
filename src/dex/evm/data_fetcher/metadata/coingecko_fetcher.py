import redis
import aiohttp
import asyncio
import json

##########################################
from src.logger_handler.logger import get_logger, setup_logger
from src.settings.config import (EVM_NATIVE_TOKEN_ADDRESSES,
                                 MARKETS,
                                 MIN_VOL24,
                                 MIN_TVL,
                                 REDIS_METADATA_KEY,
                                 DEX,
                                 Network,
                                 Version)
from src.dex.evm.type_dict import MetadataDict
from src.settings.config import get_config
from src.dex.evm.uniswap.state.v3 import UniswapV3
from src.dex.evm.uniswap.state.v4 import UniswapV4
##########################################

_config = get_config()

API_ENDPOINT = "https://api.geckoterminal.com/api/v2/networks/%s/dexes/%s/pools?include=base_token,quote_token&sort=h24_volume_usd_desc&page=%s"

# Since Sushi Swap and Pancake swap are direct fork of Uniswap protocols V2 and V3, they will be saved along uniswap
SUPPORTED_EVM_MARKETS: list[tuple[Network, DEX, str]] = [
    ("eth", "uniswap", "v2"),
    ("eth", "uniswap", "v3"),
    ("eth", "uniswap", "v4"),
    ("eth", "pancakeswap", "v2"),
    ("eth", "pancakeswap", "v3"),
    ("eth", "sushiswap", "v2"),
    ("eth", "sushiswap", "v3"),

    ("arbitrum", "uniswap", "v2"),
    ("arbitrum", "uniswap", "v3"),
    ("arbitrum", "uniswap", "v4"),
    ("arbitrum", "pancakeswap", "v2"),
    ("arbitrum", "pancakeswap", "v3"),
    ("arbitrum", "sushiswap", "v2"),
    ("arbitrum", "sushiswap", "v3"),

    ("base", "uniswap", "v2"),
    ("base", "uniswap", "v3"),
    ("base", "uniswap", "v4"),
    ("base", "pancakeswap", "v2"),
    ("base", "pancakeswap", "v3"),
    ("base", "sushiswap", "v2"),
    ("base", "sushiswap", "v3"),

    ("bsc", "uniswap", "v2"),
    ("bsc", "uniswap", "v3"),
    ("bsc", "uniswap", "v4"),
    ("bsc", "pancakeswap", "v2"),
    ("bsc", "pancakeswap", "v3"),
    ("bsc", "sushiswap", "v2"),
    ("bsc", "sushiswap", "v3"),
]

EVM_PARENT: dict[tuple[Network, DEX, str], tuple[Network, DEX, str]] = {
    ("eth", "pancakeswap", "v2"): ("eth", "uniswap", "v2"),
    ("eth", "pancakeswap", "v3"): ("eth", "uniswap", "v3"),
    ("eth", "sushiswap", "v2"): ("eth", "uniswap", "v2"),
    ("eth", "sushiswap", "v3"): ("eth", "uniswap", "v3"),

    ("arbitrum", "pancakeswap", "v2"): ("arbitrum", "uniswap", "v2"),
    ("arbitrum", "pancakeswap", "v3"): ("arbitrum", "uniswap", "v3"),
    ("arbitrum", "sushiswap", "v2"): ("arbitrum", "uniswap", "v2"),
    ("arbitrum", "sushiswap", "v3"): ("arbitrum", "uniswap", "v3"),

    ("base", "pancakeswap", "v2"): ("base", "uniswap", "v2"),
    ("base", "pancakeswap", "v3"): ("base", "uniswap", "v3"),
    ("base", "sushiswap", "v2"): ("base", "uniswap", "v2"),
    ("base", "sushiswap", "v3"): ("base", "uniswap", "v3"),

    ("bsc", "pancakeswap", "v2"): ("bsc", "uniswap", "v2"),
    ("bsc", "pancakeswap", "v3"): ("bsc", "uniswap", "v3"),
    ("bsc", "sushiswap", "v2"): ("bsc", "uniswap", "v2"),
    ("bsc", "sushiswap", "v3"): ("bsc", "uniswap", "v3"),
}

GECKO_DEX_IDS = {
    "eth": {
        "uniswap": {
            "v2": "uniswap_v2",
            "v3": "uniswap_v3",
            "v4": "uniswap-v4-ethereum",
        },
        "sushiswap": {
            "v2": "sushiswap",
            "v3": "sushiswap-v3-ethereum",
        },
        "pancakeswap": {
            "v2": "pancakeswap_ethereum",
            "v3": "pancakeswap-v3-ethereum",
        },
    },

    "arbitrum": {
        "uniswap": {
            "v2": "uniswap-v2-arbitrum",
            "v3": "uniswap_v3_arbitrum",
            "v4": "uniswap-v4-arbitrum",
        },
        "sushiswap": {
            "v2": "sushiswap_arbitrum",
            "v3": "sushiswap-v3-arbitrum",
        },
        "pancakeswap": {
            "v2": "pancakeswap-v2-arbitrum",
            "v3": "pancakeswap-v3-arbitrum",
        },
    },

    "base": {
        "uniswap": {
            "v2": "uniswap-v2-base",
            "v3": "uniswap-v3-base",
            "v4": "uniswap-v4-base",
        },
        "sushiswap": {
            "v2": "sushiswap-v2-base",
            "v3": "sushiswap-v3-base",
        },
        "pancakeswap": {
            "v2": "pancakeswap-v2-base",
            "v3": "pancakeswap-v3-base",
        },
    },

    "bsc": {
        "uniswap": {
            "v2": "uniswap-v2-bsc",
            "v3": "uniswap-bsc",
            "v4": "uniswap-v4-bsc",
        },
        "sushiswap": {
            "v2": "sushiswap_bsc",
            "v3": "sushiswap-v3-bsc",
        },
        "pancakeswap": {
            "v2": "pancakeswap_v2",
            "v3": "pancakeswap-v3-bsc",
        },
    },
}



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
    ):
        if not metadata:
            self.logger.warning(f"Skipping save for {market} {version}: empty metadata.")
            return

        try:
            self.logger.info(f"Saving metadata for {market} {version} to redis. "
                             f"Saving data length: {len(metadata)}.")
            self.r.set(REDIS_METADATA_KEY % (market, version), json.dumps(metadata))
            self.logger.info(f"Metadata for {market} {version} saved.")

        except Exception as e:
            self.logger.error(f"Error saving metadata for {market} {version}: {e}")

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

    async def _get_on_chain_metadata(
            self,
            network: Network,
            gecko_dex_id: str,
            dex: DEX,
            version: Version,
            res,
    ) -> dict:
        def get_all_pool_addresses(_res: list[dict]) -> list[str]:
            _pool_addresses: list[str] = []

            for _result in _res:
                if not isinstance(_result, dict):
                    self.logger.error(
                        f"Error fetching metadata for {gecko_dex_id} {network}: {_result}"
                    )
                    continue

                _data = _result.get("data", [])

                for _pool in _data:
                    try:
                        _pool_addresses.append(
                            _pool["attributes"]["address"].lower()
                        )
                    except Exception as e:
                        self.logger.error(f"Error parsing pool address: {e}")

            return _pool_addresses


        if version == "v2":
            if dex == "uniswap":
                on_chain_metadata = {
                    "fee_rate": 3000,
                    "tick_spacing": 0,
                }
            elif dex == "sushiswap":
                on_chain_metadata = {
                    "fee_rate": 3000,
                    "tick_spacing": 0,
                }
            elif dex == "pancakeswap":
                on_chain_metadata = {
                    "fee_rate": 2500,
                    "tick_spacing": 0,
                }
            else:
                raise Exception(f"Unknown dex: {dex}")

        elif version == "v3":
            uniV3 = UniswapV3(network=network, dex=dex)
            all_pool_addresses = get_all_pool_addresses(res)

            on_chain_metadata = await uniV3.fetch_metadata_initialization(all_pool_addresses)

        elif version == "v4":
            uniV4 = UniswapV4(network=network, dex=dex)
            all_pool_addresses = get_all_pool_addresses(res)

            on_chain_metadata = await uniV4.fetch_initialize_events(all_pool_addresses)

        else:
            raise Exception(f"Unknown version: {version}")


        return on_chain_metadata

    async def _fetch_pages(
            self,
            network: Network,
            gecko_dex_id: str,
    ):
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
            tasks = [
                asyncio.create_task(fetch_page(page))
                for page in range(1, 11)
            ]

            try:
                res = await asyncio.gather(*tasks)
                break

            except Exception as e:
                for task in tasks:
                    if not task.done():
                        task.cancel()

                await asyncio.gather(*tasks, return_exceptions=True)

                self.logger.error(f"Error fetching metadata for {gecko_dex_id} {network}: {e}")
                self.logger.info("Sleeping for 60 seconds.")
                await asyncio.sleep(60)


        return res

    async def fetch_metadata(
            self,
            network: Network,
            gecko_dex_id: str,
            dex: DEX,
            version: Version,
    ) -> dict[str, MetadataDict]:
        self.logger.info(f"Fetching metadata for {network} {dex} {version}...")

        market_metadata: dict[str, MetadataDict] = {}

        res = await self._fetch_pages(network, gecko_dex_id)

        on_chain_metadata = await self._get_on_chain_metadata(network, gecko_dex_id, dex, version, res)

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

                    pool_address = attributes["address"].lower()
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

                    if addr0 > addr1:
                        addr0, addr1 = addr1, addr0
                        token0, token1 = token1, token0
                        decimals0, decimals1 = decimals1, decimals0

                    network_native_token_alies = EVM_NATIVE_TOKEN_ADDRESSES[network]["alias"]
                    network_native_token_alies_addr = EVM_NATIVE_TOKEN_ADDRESSES[network]["alias_addresses"]

                    if token0 in network_native_token_alies and addr0 in network_native_token_alies_addr:
                        token0 = EVM_NATIVE_TOKEN_ADDRESSES[network]["symbol"]
                        addr0 = EVM_NATIVE_TOKEN_ADDRESSES[network]["address"]
                    elif token1 in network_native_token_alies and addr1 in network_native_token_alies_addr:
                        token1 = EVM_NATIVE_TOKEN_ADDRESSES[network]["symbol"]
                        addr1 = EVM_NATIVE_TOKEN_ADDRESSES[network]["address"]

                    if version == "v2":
                        fee_rate = on_chain_metadata["fee_rate"]
                        tick_spacing = on_chain_metadata["tick_spacing"]
                    else:
                        pool_on_chain_metadata = on_chain_metadata.get(pool_address)

                        if not pool_on_chain_metadata:
                            self.logger.warning(
                                f"No on-chain metadata found for pool {pool_address} "
                                f"{gecko_dex_id} {network}"
                            )
                            continue

                        fee_rate = pool_on_chain_metadata["fee_rate"]
                        tick_spacing = pool_on_chain_metadata["tick_spacing"]

                    if volume24h < MIN_VOL24 or tvl < MIN_TVL:
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
                        fee_rate=fee_rate,
                        tick_spacing=tick_spacing
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
                    network, dex, version = market

                    parent_market = EVM_PARENT.get(market, market)

                    gecko_dex_id = GECKO_DEX_IDS[network][dex][version]

                    metadata = await self.fetch_metadata(network, gecko_dex_id, dex, version)

                    evm_metadata.setdefault(parent_market, {}).update(metadata)

                    self.logger.info(f"Sleeping for 90 seconds. Because of rate limit of this bullshit coingecko api.")
                    await asyncio.sleep(90)

                for market, metadata in evm_metadata.items():
                    market_key = "_".join(market)
                    self._save_metadata(metadata, MARKETS[market_key]["market"], MARKETS[market_key]["version"])

            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                self.logger.info(f"Sleeping for 60 seconds.")
                await asyncio.sleep(60)

            self.logger.info(f"Sleeping for {_config.METADATA_FETCH_INTERVAL} seconds.")
            await asyncio.sleep(_config.METADATA_FETCH_INTERVAL)
