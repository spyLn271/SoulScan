import asyncio
import json
import redis
import pydantic
import time



####################################
from src.Config import config
from src.LoggerHandler.logger import get_logger, setup_logger
from src import MeteoraDLMM, MeteoraDAMMv2, OrcaCLMM, RaydiumCLMM, RaydiumHybridAMM
####################################


class PoolStateConfigScheme(pydantic.BaseModel):
    error_sleep_time: int = 10
    cache_update_time: int = 5 * 60
    market: str
    version: str
    logger_name: str = "PSF"
    logger_file: str = "PSF.log"
    provider: MeteoraDLMM | MeteoraDAMMv2 | OrcaCLMM | RaydiumCLMM | RaydiumHybridAMM



class PoolStateFetcher:
    def __init__(self, conf: PoolStateConfigScheme):
        super().__init__()

        self.market = conf.market
        self.version = conf.version
        self.logger_name = conf.logger_name
        self.logger_file = conf.logger_file
        self.cache_update_time = conf.cache_update_time
        self.error_sleep_time = conf.error_sleep_time
        self.provider = conf.provider
        log_name = f"{self.market}_{self.version}"
        log_file = f"{config.LOG_MAIN_FOLDER}{self.market}_{self.version}_{self.logger_file}"
        setup_logger(logger_name=log_name, log_file=log_file)

        self.r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
        self.logger = get_logger(log_name)
        self.logger.info(f"PoolMetadataFetcher initialized for {self.market} {self.version}.")

        self.cache = {}


    def _save_state(self, pool_state: dict) -> bool:
        try:
            self.logger.info(f"Saving state for {self.market} {self.version} to redis. "
                             f"Saving data length: {len(pool_state)}.")
            self.r.set(config.REDIS_METADATA_KEY % (self.market, self.version), json.dumps(pool_state))
            self.logger.info(f"State for {self.market} {self.version} saved.")
            return True
        except Exception as e:
            self.logger.error(f"Error saving state for {self.market} {self.version}: {e}")
            return False

    def _get_pool_metadata(self) -> dict:
        try:
            self.logger.info(f"Getting metadata for {self.market} {self.version} from redis.")
            metadata = json.loads(self.r.get(config.REDIS_METADATA_KEY % (self.market, self.version)))
            self.logger.info(f"Metadata for {self.market} {self.version} fetched.")
            return metadata
        except Exception as e:
            self.logger.error(f"Error getting metadata for {self.market} {self.version}: {e}")
            raise Exception("Error getting metadata.")

    def _get_default_metadata(self) -> dict:
        pass

    def _get_default_state(self) -> tuple[dict, list]:
        metadata = self._get_pool_metadata()
        if not metadata:
            self.logger.error(f"Metadata for {self.market} {self.version} not found.")
            self.logger.info(f"Getting default metadata for {self.market} {self.version}.")
            metadata = self._get_default_metadata()
            self.logger.info(f"Default metadata for {self.market} {self.version} fetched.")
        addresses = self._get_pool_addresses(metadata)
        return metadata, addresses


    def _get_pool_addresses(self, metadata: dict) -> list:
        addresses = []
        for pool in metadata:
            addresses.append(pool)
        self.logger.info(f"Pool addresses for {self.market} {self.version} fetched. Length: {len(addresses)}.")
        return addresses

    async def _set_up_cache(self, provider_instance, metadata: dict, addresses: list) -> bool:
        raise Exception("set_up_cache not implemented.")

    async def _state_fetcher(self, provider_instance, metadata: dict, addresses: list) -> dict:
        raise Exception("state_fetcher not implemented.")

    async def main(self):
        metadata, addresses = self._get_default_state()
        await self._set_up_cache(self.provider, metadata, addresses)
        last_cache_update_time = time.time()

        while True:
            try:
                if time.time() - last_cache_update_time > self.cache_update_time:
                    metadata, addresses = self._get_default_state()
                    await self._set_up_cache(self.provider, metadata, addresses)
                    last_cache_update_time = time.time()
                pool_state = await self._state_fetcher(self.provider, metadata, addresses)
                is_state_saved = self._save_state(pool_state)
                if not is_state_saved:
                    raise Exception("Error saving state.")

            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(self.error_sleep_time)
