import logging
import json
import redis
from solders.pubkey import Pubkey as SolanaPubkey

####################################
from src.settings import config
from src.dex.tools.helpers.solana.translater import Translater
####################################


class Helper:
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
        self.translater = Translater(self.logger)


    @staticmethod
    def _get_address_chunk(addresses, chunk_size=100) -> list:
        return [addresses[i:i + chunk_size] for i in range(0, len(addresses), chunk_size)]

    def _getPoolsList(self, dex, protocol) -> list:
        pools_list = []
        data = self.r.get(config.REDIS_METADATA_KEY % (dex, protocol))
        for pool in json.loads(data):
            pools_list.append(pool)

        return pools_list

    @staticmethod
    def findProgramDerivedAddress(seeds: list[bytes], program_id: SolanaPubkey) -> str:
        pda, bump = SolanaPubkey.find_program_address(seeds, program_id)
        return str(pda)

    def findPDAs(self, seeds: list, program_id: list | SolanaPubkey) -> list:
        PDAs = []
        for i, seed in enumerate(seeds):
            try:
                PDA = self.findProgramDerivedAddress(seed,
                                                     program_id[i] if isinstance(program_id, list) else program_id)
                PDAs.append(PDA)
            except Exception as e:
                self.logger.error(f"Error finding PDA for seed {seed}: {e}")
                continue

        return PDAs


if __name__ == "__main__":
    helper = Helper()
    raw_data = 'Edj2juHH2jgAIPn/Zv6K3LmdnNR3lqghHrvycJBo3wpaZrnbBbrqjDyBpAMAAAAAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGhifI7DwAAAAAAAAAAAAAAoYnyOw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
    print(json.dumps(helper.translater.translate(raw_data, market="metadata"), indent=4))
    start_index = -450560
    address = '7w3hpYQ1WkNU5CEGhLWxoB7iNFD6WdmxkvHRYrdQKPia'
    seed = [b"tick_array", bytes(SolanaPubkey.from_string(address)), str(start_index).encode()]
    print(helper.findProgramDerivedAddress(seed, SolanaPubkey.from_string(config.ORCA_CLMM_PROGRAM_ID)))
