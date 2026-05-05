import aiohttp
import asyncio
import json
import redis
import pydantic

####################################
from src.settings import config
from src.settings.config import get_config, Network, METADATA_LOG_FILE
from src.logger_handler.logger import get_logger, setup_logger
####################################

class PoolMetadataConfigScheme(pydantic.BaseModel):
    error_sleep_time: int = 10
    fetching_sleep_time: int = get_config().METADATA_FETCH_INTERVAL
    market: str
    version: str
    network: Network = "solana"
    logger_name: str = "PMF"
    logger_file: str = "PMF.log"


class PoolMetadataFetcher:
    def __init__(self, conf: PoolMetadataConfigScheme):
        super().__init__()

        self.market = conf.market
        self.version = conf.version
        self.network = conf.network
        self.logger_name = conf.logger_name
        self.logger_file = conf.logger_file
        self.error_sleep_time = conf.error_sleep_time
        self.fetching_sleep_time = conf.fetching_sleep_time
        log_name = f"{self.market}_{self.version}_metadata"
        setup_logger(logger_name=log_name, log_file=METADATA_LOG_FILE)


        self.r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
        self.logger = get_logger(log_name)
        self.session: aiohttp.ClientSession
        self._is_session_open = False
        self.logger.info(f"PoolMetadataFetcher initialized for {self.market} {self.version}.")

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
            await self.session.close()
            self.logger.info("PoolMetadataFetcher session closed.")
        else:
            self.logger.warning("PoolMetadataFetcher session already closed.")


    def _save_metadata(self, metadata: dict) -> bool:
        try:
            self.logger.info(f"Saving metadata for {self.network} {self.market} {self.version} to redis. "
                             f"Saving data length: {len(metadata)}.")
            self.r.set(config.REDIS_METADATA_KEY % (self.network, self.market, self.version), json.dumps(metadata))
            self.logger.info(f"Metadata for {self.market} {self.version} saved.")
            return True
        except Exception as e:
            self.logger.error(f"Error saving metadata for {self.market} {self.version}: {e}")
            return False


    async def _metadata_fetcher(self) -> dict:
        raise Exception("metadata_fetcher not implemented.")

    async def main(self):
        while True:
            try:
                metadata = await self._metadata_fetcher()
                is_metadata_saved = self._save_metadata(metadata)
                if is_metadata_saved:
                    self.logger.info(f"Metadata for {self.market} {self.version} fetched and saved.")
                    self.logger.info(f"Sleeping for {self.fetching_sleep_time} seconds.")
                    await asyncio.sleep(self.fetching_sleep_time)
                else:
                    self.logger.error(f"Error saving metadata for {self.market} {self.version}.")
                    raise Exception("Error saving metadata.")
            except Exception as e:
                self.logger.error(f"Error fetching metadata for {self.market} {self.version}: {e}")
                self.logger.info(f"Sleeping for {self.error_sleep_time} seconds.")
                await asyncio.sleep(self.error_sleep_time)