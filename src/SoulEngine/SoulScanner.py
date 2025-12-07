import redis
import json

####################################
from src.Config import config
from src.Config.GracefullShutDown import TerminateSignal, sigterm_handler
from src.SoulEngine.SmartRouter.OnlineSmartRouter import get_active_metadata, get_active_state
####################################

def get_all_active_tokens(redis_connection: redis.Redis):
    metadata = get_active_metadata(redis_connection)
    state = get_active_state(redis_connection)

    mapped_tokens = {}
    for pool, data in metadata.items():
        if not state.get(pool): continue

        mint0 = data.get('mint0')
        mint1 = data.get('mint1')
        decimals0 = data.get('decimals0')
        decimals1 = data.get('decimals1')
        token0 = data.get('token0')
        token1 = data.get('token1')

        if not mint0 or not mint1 or not decimals0 or not decimals1 or not token0 or not token1: continue

        if not mint0 in mapped_tokens:
            mapped_tokens[mint0] = {
                'decimals': decimals0,
                'symbol': token0
            }
        if not mint1 in mapped_tokens:
            mapped_tokens[mint1] = {
                'decimals': decimals1,
                'symbol': token1
            }

    return mapped_tokens