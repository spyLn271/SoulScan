import aiohttp
import logging
import redis
import time

####################################
from src.Config.TargetPoolConfig import TargetPoolConfig
from src.Config import config
from src.LoggerHandler.logger import setup_logger
####################################


class TargetPoolFetcher:
    def __init__(self, logger_name='TargetPoolFetcher', log_file="TargetPoolFetcher.log"):
        super().__init__()

        self.session: aiohttp.ClientSession = None
        setup_logger(logger_name=logger_name, log_file=f'{config.LOG_MAIN_FOLDER}{log_file}')
        self.logger = logging.getLogger(logger_name)
        self.redis = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)

    async def __aenter__(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
            self.logger.info("TargetPoolFetcher session opened.")
        else:
            self.logger.warning("TargetPoolFetcher session already open.")
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.logger.info("TargetPoolFetcher session closed.")

    async def fetchTargetPool(self, TargetMarket: str):
        tpf_config = TargetPoolConfig(TargetMarket)
        url = tpf_config.get_url(TargetMarket)
        query = tpf_config.get_query(TargetMarket)
        func = tpf_config.get_process_func(TargetMarket)

        while True:
            try:
                async with self.session.get(url, params=query) as response:
                    response.raise_for_status()
                    data = await response.json()

                process_result = func(data, self.redis)

                if process_result['status']:
                    self.logger.info(f'Fetched {TargetMarket} pools successfully. Total: {process_result["LenData"]}\n'
                                     f'Sleeping for 24 hours.')
                    time.sleep(24 * 60 * 60)
                else:
                    self.logger.error(f'Error fetching {TargetMarket} pools. Error: {process_result["message"]}')
                    time.sleep(10)
                    continue

            except Exception as e:
                self.logger.error(f'Error fetching {TargetMarket} pools Error: {e}')
                time.sleep(10)