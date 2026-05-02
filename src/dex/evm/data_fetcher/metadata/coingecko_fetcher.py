import redis
import aiohttp
import asyncio
import json
from typing import Literal
from web3 import Web3
from web3.eth.eth import ChecksumAddress

##########################################
from src.logger_handler.logger import get_logger, setup_logger
from src.settings.config import (EVM_NATIVE_TOKEN_ADDRESSES,
                                 MARKETS,
                                 MIN_VOL24,
                                 REDIS_METADATA_KEY,
                                 DEX,
                                 Network)
from src.dex.evm.data_fetcher.metadata.metadata import MetadataDict
from src.settings.config import get_config
from src.dex.evm.uniswap.state.v3 import UniswapV3
from src.dex.evm.uniswap.state.v4 import UniswapV4
##########################################

_config = get_config()

API_ENDPOINT = "https://api.geckoterminal.com/api/v2/networks/%s/dexes/%s/pools?include=base_token,quote_token&sort=h24_volume_usd_desc&page=%s"

"""
https://api.geckoterminal.com/api/v2/networks/eth/dexes/uniswap_v2/pools?include=base_token,quote_token&sort=h24_volume_usd_desc&page=1
"""

# Since Sushi Swap and Pancake swap are direct fork of Uniswap protocols V2 and V3, they will be saved along uniswap
SUPPORTED_EVM_MARKETS = [
    "eth_uniswap_v2",
    "eth_uniswap_v3",
    "eth_uniswap_v4",
    "eth_pancakeswap_v2",
    "eth_pancakeswap_v3",
    "eth_sushiswap_v2",
    "eth_sushiswap_v3",

    "arbitrum_uniswap_v2",
    "arbitrum_uniswap_v3",
    "arbitrum_uniswap_v4",
    "arbitrum_pancakeswap_v2",
    "arbitrum_pancakeswap_v3",
    "arbitrum_sushiswap_v2",
    "arbitrum_sushiswap_v3",

    "base_uniswap_v2",
    "base_uniswap_v3",
    "base_uniswap_v4",
    "base_pancakeswap_v2",
    "base_pancakeswap_v3",
    "base_sushiswap_v2",
    "base_sushiswap_v3",

    "bsc_uniswap_v2",
    "bsc_uniswap_v3",
    "bsc_uniswap_v4",
    "bsc_pancakeswap_v2",
    "bsc_pancakeswap_v3",
    "bsc_sushiswap_v2",
    "bsc_sushiswap_v3",
]

EVM_PARENT = {
    "eth_pancakeswap_v2": "eth_uniswap_v2",
    "eth_pancakeswap_v3": "eth_uniswap_v3",
    "eth_sushiswap_v2": "eth_uniswap_v2",
    "eth_sushiswap_v3": "eth_uniswap_v3",

    "arbitrum_pancakeswap_v2": "arbitrum_uniswap_v2",
    "arbitrum_pancakeswap_v3": "arbitrum_uniswap_v3",
    "arbitrum_sushiswap_v2": "arbitrum_uniswap_v2",
    "arbitrum_sushiswap_v3": "arbitrum_uniswap_v3",

    "base_pancakeswap_v2": "base_uniswap_v2",
    "base_pancakeswap_v3": "base_uniswap_v3",
    "base_sushiswap_v2": "base_uniswap_v2",
    "base_sushiswap_v3": "base_uniswap_v3",

    "bsc_pancakeswap_v2": "bsc_uniswap_v2",
    "bsc_pancakeswap_v3": "bsc_uniswap_v3",
    "bsc_sushiswap_v2": "bsc_uniswap_v2",
    "bsc_sushiswap_v3": "bsc_uniswap_v3",
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
            network: Network,
            gecko_dex_id: str,
            dex: DEX,
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


        market_metadata: dict[str, MetadataDict] = {}

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

            on_chain_metadata = uniV3.fetch_metadata_initialization(all_pool_addresses)

        elif version == "v4":
            uniV4 = UniswapV4(network=network, dex=dex)
            all_pool_addresses = get_all_pool_addresses(res)

            on_chain_metadata = uniV4.fetch_initialize_events(all_pool_addresses)

        else:
            raise Exception(f"Unknown version: {version}")



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
                self.logger.info(f"Sleeping for 60 seconds.")
                await asyncio.sleep(60)

            self.logger.info(f"Sleeping for 1800 seconds.")
            await asyncio.sleep(1800)
