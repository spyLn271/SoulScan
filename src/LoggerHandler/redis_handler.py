import logging, redis, json
from src.Config import config

LOG_STREAM_KEY = "log_stream"
MAX_STREAM_LENGTH = 10000

class RedisHandler(logging.Handler):
    def __init__(self, host=config.REDIS_HOST, port=config.REDIS_PORT):
        super().__init__()
        self.redis_client = redis.Redis(host=host, port=port, db=0, decode_responses=True)
        self.redis_client.ping()

    def emit(self, record):
        try:
            log_entry = {
                'name': record.name,
                'level': record.levelname,
                'message': record.getMessage(),
                'timestamp': record.created
            }
            self.redis_client.xadd(
                LOG_STREAM_KEY,
                {'log_data': json.dumps(log_entry)},
                maxlen=MAX_STREAM_LENGTH
            )
        except Exception:
            self.handleError(record)