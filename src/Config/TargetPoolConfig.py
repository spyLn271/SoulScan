import redis
import json

####################################
from src.Config import config
####################################

class TargetPoolConfig:
    def __init__(self, target_market):
        self.TARGET_POOLS_PAYLOAD = {
            'MeteoraDLMM': {'url': 'https://dlmm-api.meteora.ag/pair/all',
                            'func': lambda data, r: TargetPoolConfig.__MeteoraDLMMProcessFunc(data, r)},
            'MeteoraDAMMV2': {'url': 'https://dammv2-api.meteora.ag/pools?limit=1000',
                              'query': {'order': 'desc'},
                              'func': lambda data, r: TargetPoolConfig.__MeteoraDAMMV2ProcessFunc(data, r)}
        }

    def get_process_func(self, target_market):
        return self.TARGET_POOLS_PAYLOAD[target_market]['func']

    def get_url(self, target_market):
        return self.TARGET_POOLS_PAYLOAD[target_market]['url']

    def get_query(self, target_market):
        return self.TARGET_POOLS_PAYLOAD[target_market].get('query')

    @staticmethod
    def __MeteoraDLMMProcessFunc(data, r: redis) -> dict:
        redis_key = config.REDIS_METADATA_KEY % ('Meteora', 'DLMM')
        pools = {}

        if not isinstance(data, list):
            return {'status': False, 'LenData': len(pools), 'message': 'Invalid data format'}

        for pair in data:
            try:
                address = pair.get('address')
                token0, token1 = pair.get('name').split('-')
                address0, address1 = pair.get('mint_x'), pair.get('mint_y')
                reserve0, reserve1 = pair.get('reserve_x'), pair.get('reserve_y')
                bin_step = pair.get('bin_step')
                base_fee_percentage = pair.get('base_fee_percentage')
                max_fee_percentage = pair.get('max_fee_percentage')
                volume24 = pair.get('trade_volume_24h', 0)

                if volume24 < 10_000:
                    continue

                pools[address] = {
                    'token0': token0,
                    'token1': token1,
                    'address0': address0,
                    'address1': address1,
                    'reserve0': reserve0,
                    'reserve1': reserve1,
                    'bin_step': bin_step,
                    'base_fee_percentage': base_fee_percentage,
                    'max_fee_percentage': max_fee_percentage,
                    'volume24': volume24,
                }
            except Exception as e:
                continue

        if len(pools) > 0:
            r.set(redis_key, json.dumps(pools))
            return {'status': True, 'LenData': len(pools), 'message': 'Data fetched successfully'}
        else:
            return {'status': False, 'LenData': len(pools), 'message': 'No data found'}

    @staticmethod
    def __MeteoraDAMMV2ProcessFunc(data: dict, r: redis):
        redis_key = config.REDIS_METADATA_KEY % ('Meteora', 'DAMMV2')
        filtered_pools = {}

        if not isinstance(data, dict):
            return {'status': False, 'LenData': len(data), 'message': 'Invalid data format'}

        pools = data.get('data', [])
        if not isinstance(pools, list):
            return {'status': False, 'LenData': len(pools), 'message': 'No pools found in data'}

        for pool in pools:
            try:
                address = pool.get('pool_address')
                pool_type = pool.get('pool_type')
                token0, token1 = pool.get('pool_name').split('-')
                address0, address1 = pool.get('token_a_mint'), pool.get('token_b_mint')
                reserve0, reserve1 = pool.get('token_a_vault'), pool.get('token_b_vault')
                base_fee_percentage = pool.get('base_fee')
                dynamic_fee = pool.get('dynamic_fee')
                volume24 = pool.get('volume24h', 0)

                if volume24 < 10_000:
                    continue

                filtered_pools[address] = {
                    'token0': token0,
                    'token1': token1,
                    'address0': address0,
                    'address1': address1,
                    'reserve0': reserve0,
                    'reserve1': reserve1,
                    'pool_type': pool_type,
                    'base_fee_percentage': base_fee_percentage,
                    'dynamic_fee': dynamic_fee,
                }
            except Exception as e:
                continue

        if len(pools) > 0:
            r.set(redis_key, json.dumps(filtered_pools))
            return {'status': True, 'LenData': len(pools), 'message': 'Data fetched successfully'}
        else:
            return {'status': False, 'LenData': len(pools), 'message': 'No data found'}