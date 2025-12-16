import redis
import logging
import pydantic
import os
import time
import multiprocessing

####################################
from src.Config import config
from src.Config.GracefullShutDown import TerminateSignal, sigterm_handler
from src.SoulEngine.SoulHelper import (get_active_metadata,
                                       get_active_state,
                                       get_all_common_list_of_tokens,
                                       break_tasks_in_chunks)
from src.LoggerHandler.logger import setup_logger, get_logger
####################################

class ScannerConfig(pydantic.BaseModel):
    logger_name: str = "Scanner"
    logger_file: str = "Scanner.log"
    worker_number: int = 5
    sleep_interval: int = 10
    token_list_update_interval: int = 60

class Scanner:
    def __init__(self, conf: ScannerConfig):
        self.conf = conf

        setup_logger(logger_name=conf.logger_name, log_file=os.path.join(config.LOG_MAIN_FOLDER, conf.logger_file))
        self.logger = get_logger(conf.logger_name)

        self.logger.info(f"Scanner initialized. Config: {conf.model_dump()}")

        self.r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
        self.queue = multiprocessing.JoinableQueue()

        self.cache = {}

    def _get_target_tokens(self) -> list:
        cached_data: dict = self.cache.get('target_tokens', {})
        if cached_data:
            cached_time: int = cached_data.get('time', 0)
            cached_tokens: list = cached_data.get('tokens')

            if (cached_time + self.conf.token_list_update_interval > time.time() and
                    isinstance(cached_tokens, list)):
                return cached_tokens

        target_tokens = get_all_common_list_of_tokens(self.r)
        self.cache['target_tokens'] = {
            'time': time.time(),
            'tokens': target_tokens
        }

        return target_tokens




