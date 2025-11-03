from solders.pubkey import Pubkey as SolanaPubkey
import base64

####################################
from src.Config import config
from src.DEX.tools.rpc.Solana import Solana
from src.DEX.tools.helpers.translater import Translater
from src.LoggerHandler.logger import setup_logger, get_logger
####################################




class MeteoraDAMMv2(Solana):
    def __init__(self, SOLANA_RPC_ENDPOINT=config.SOLANA_RPC_ENDPOINT, logger_name='MeteoraDAMMv2',
                 logger_file="MeteoraDAMMv2.log"):
        super().__init__(SOLANA_RPC_ENDPOINT)

        setup_logger(logger_name=logger_name, log_file=f"{config.LOG_MAIN_FOLDER}{logger_file}")
        self.logger = get_logger(logger_name)
