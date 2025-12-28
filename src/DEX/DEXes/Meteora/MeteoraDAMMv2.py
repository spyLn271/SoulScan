import os

####################################
from src.Config import config
from src.DEX.tools.rpc.Solana import Solana
from src.DEX.tools.helpers.translater import Translater
from src.LoggerHandler.logger import setup_logger, get_logger
####################################


"""
1) How does DAMM V2 works ?
2) How data is structured in DAMM v2 ?
3) What information do I need for further processing ?

1)
DAMM V2 is kind of concentrated liquidity pool, hard code restriction of max and min price, and Dynamic Fee.
DAMM v2 is a constant product AMM that operates between a sqrt_min_price and a sqrt_max_price. <- In doc
for example: 
    address: 8Pm2kZpnxD3hoMmt4bjStX2Pw2Z9abpbHzZxMPqxPmie
    bio:  Here the pools is SOL/USDC and restricted with price range between 70 and 440.
         Base fee is 0.04% and can be high due to Dynamic Fee.
The math is like in Uniswap V3 with sqrt_price and Liquidity.

2) All needed data is in pool ( name: Pool )

3) 
    a) Data for Dynamic Fee calculation
    b) Uniswap V3 data calculation
    
PS: No cache is needed
"""

class MeteoraDAMMv2Translater(Translater):
    def __init__(self, logger):
        super().__init__(logger)

    def translate_Pool(self, x: str) -> dict:
        try:
            parsed_data = self.translate(x, market="ammV2", name="Pool")
            base_fee = parsed_data["pool_fees"]["base_fee"]
            dynamic_fee = parsed_data["pool_fees"]["dynamic_fee"]
            liquidity = parsed_data["liquidity"]
            sqrt_min_price = parsed_data["sqrt_min_price"]
            sqrt_max_price = parsed_data["sqrt_max_price"]
            sqrt_price = parsed_data["sqrt_price"]

            del base_fee['padding_0']
            del base_fee['padding_1']
            del dynamic_fee['padding']

            pool_data = {
                "base_fee": base_fee,
                "dynamic_fee": dynamic_fee,
                "liquidity": liquidity,
                "sqrt_min_price": sqrt_min_price,
                "sqrt_max_price": sqrt_max_price,
                "sqrt_price": sqrt_price,
            }

            return pool_data
        except Exception as e:
            self.logger.error(e)
            return {}


class MeteoraDAMMv2(Solana):
    def __init__(self, SOLANA_RPC_ENDPOINT=config.SOLANA_RPC_ENDPOINT, logger_name='MeteoraDAMMv2',
                 logger_file="MeteoraDAMMv2.log"):
        super().__init__(SOLANA_RPC_ENDPOINT)

        setup_logger(logger_name=logger_name,
                     log_file=os.path.join(config.DATA_FETCHER_LOG_FOLDER, logger_file))
        self.translater = MeteoraDAMMv2Translater(logger=self.logger)
        self.logger = get_logger(logger_name)

    async def getBigBox(self, addresses: list) -> dict:
        try:
            def translate_func(x): return self.translater.translate_Pool(x[0])
            raw_data = await self.getMultipleAccounts(addresses=addresses, field=['data'],
                                                      funcs={'data': lambda x: translate_func(x)})
            processed_data = {}
            for address, data_list in raw_data.items():
                try:
                    processed_data[address] = data_list[0].get('data')
                except Exception as e:
                    self.logger.error(e)

            return processed_data


        except Exception as e:
            self.logger.error(e)
            return {}