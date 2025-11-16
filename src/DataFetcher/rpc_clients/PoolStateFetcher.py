import asyncio
import json
import redis
import pydantic
import time
from typing import Union, Type



####################################
from src.Config import config, DefaultMetadata
from src.LoggerHandler.logger import get_logger, setup_logger
from src.DataFetcher.rpc_clients import pfsException
from src import MeteoraDLMM, MeteoraDAMMv2, OrcaCLMM, RaydiumCLMM, RaydiumHybridAMM
####################################


class PoolStateConfigScheme(pydantic.BaseModel):
    error_sleep_time: int = 10
    cache_update_time: int = 5 * 60
    interval_sleep_time: int = 0
    market: str
    version: str
    logger_name: str = "PSF"
    logger_file: str = "PSF.log"
    provider: Union[
        Type[MeteoraDLMM],
        Type[MeteoraDAMMv2],
        Type[OrcaCLMM],
        Type[RaydiumCLMM],
        Type[RaydiumHybridAMM]
    ]

    provider_kwargs: dict = {}



class PoolStateFetcher:
    def __init__(self, conf: PoolStateConfigScheme):
        super().__init__()

        self.market = conf.market
        self.version = conf.version
        self.logger_name = conf.logger_name
        self.logger_file = conf.logger_file
        self.cache_update_time = conf.cache_update_time
        self.error_sleep_time = conf.error_sleep_time
        self.interval_sleep_time = conf.interval_sleep_time
        self.provider = conf.provider
        self.provider_kwargs = conf.provider_kwargs
        log_name = f"{self.market}_{self.version}"
        log_file = f"{config.LOG_MAIN_FOLDER}{self.market}_{self.version}_{self.logger_file}"
        setup_logger(logger_name=log_name, log_file=log_file)

        self.r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
        self.logger = get_logger(log_name)
        self.logger.info(f"PoolMetadataFetcher initialized for {self.market} {self.version}.")

        self.cache = {}
        self.buffer = {}


    def __save_state(self, pool_state: dict) -> bool:
        try:
            self.logger.info(f"Saving state for {self.market} {self.version} to redis. "
                             f"Saving data length: {len(pool_state)}.")
            self.r.set(config.POOLS_CURRENT_STATE_DICT_REDIS_KEY %
                       (self.market, self.version), json.dumps(pool_state))
            self.logger.info(f"State for {self.market} {self.version} saved.")
            return True
        except Exception as e:
            self.logger.error(f"Error saving state for {self.market} {self.version}: {e}")
            return False

    def __get_pool_metadata(self) -> dict:
        try:
            self.logger.info(f"Getting metadata for {self.market} {self.version} from redis.")
            raw = self.r.get(config.REDIS_METADATA_KEY % (self.market, self.version))

            if not isinstance(raw, str):
                self.logger.error(f"Metadata for {self.market} {self.version} not found.")
                return {}
            metadata = json.loads(raw)

            self.logger.info(f"Metadata for {self.market} {self.version} fetched.")
            return metadata
        except Exception as e:
            self.logger.error(f"Error getting metadata for {self.market} {self.version}: {e}")
            return {}

    def __get_default_metadata(self) -> dict:
        return DefaultMetadata.default_metadata.get(self.market, {}).get(self.version, {})

    def __get_metadata_and_addresses(self) -> tuple[dict, list]:
        metadata = self.__get_pool_metadata()
        if not metadata:
            self.logger.error(f"Metadata for {self.market} {self.version} not found.")
            self.logger.info(f"Getting default metadata for {self.market} {self.version}.")
            metadata = self.__get_default_metadata()
            if not metadata:
                raise pfsException.NoMetadataException(f"No metadata found for {self.market} {self.version}.")
            self.logger.info(f"Default metadata for {self.market} {self.version} fetched.")
        addresses = self.__get_pool_addresses(metadata)
        return metadata, addresses


    def __get_pool_addresses(self, metadata: dict) -> list:
        addresses = []
        for pool in metadata:
            addresses.append(pool)
        self.logger.info(f"Pool addresses for {self.market} {self.version} fetched. Length: {len(addresses)}.")
        return addresses

    # --- Abstract Methods for Subclasses ---
    async def _set_up_cache(self, provider_instance, metadata: dict, addresses: list) -> bool:
        raise pfsException.NoImplementationException("_set_up_cache not implemented.")

    async def _state_fetcher(self, provider_instance, metadata: dict, addresses: list) -> dict:
        raise pfsException.NoImplementationException("_state_fetcher not implemented.")

    async def main(self):
        last_cache_update_time = 0

        async with self.provider(**self.provider_kwargs) as provider_instance:
            while True:
                try:
                    if int(time.time()) - last_cache_update_time > self.cache_update_time:
                        if last_cache_update_time == 0:
                            self.logger.info(f"Initializing cache for {self.market} {self.version}.")
                        else:
                            self.logger.info(f"Cache expired. Updating cache for {self.market} {self.version}.")

                        metadata, addresses = self.__get_metadata_and_addresses()
                        is_cache_initialized = await self._set_up_cache(provider_instance, metadata, addresses)

                        if not is_cache_initialized:
                            self.logger.error("Cache initialization failed. Retrying...")
                            await asyncio.sleep(self.error_sleep_time)
                            continue

                        last_cache_update_time = int(time.time())
                        self.logger.info(f"Cache updated. Next update in {self.cache_update_time} seconds.")

                    pool_state = await self._state_fetcher(provider_instance, metadata, addresses)

                    if not self.__save_state(pool_state):
                        raise Exception("Error saving state to Redis.")

                    if self.interval_sleep_time:
                        self.logger.info(f"Sleeping for {self.interval_sleep_time} seconds.")
                        await asyncio.sleep(self.interval_sleep_time)

                except pfsException.NoMetadataException as e:
                    self.logger.error(f"No metadata found for {self.market} {self.version} ({e}).")
                    break
                except pfsException.NoImplementationException as e:
                    self.logger.error(f"No implementation found for {self.market} {self.version} ({e}).")
                    break
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    await asyncio.sleep(self.error_sleep_time)
