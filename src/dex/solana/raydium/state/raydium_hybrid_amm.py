import os

####################################
from src.settings import config
from src.settings.config import SOLANA_FETCHER_LOG_FILE
from src.dex.tools.rpc.solana import Solana
from src.dex.tools.helpers.solana.translater import Translater
from src.logger_handler.logger import setup_logger, get_logger
from src.dex.solana.raydium.state.raydium_scheme import RaydiumBigBoxVaultAddressScheme
####################################




"""
1. AMM Pool Account
Fields to extract:
  - coin_vault: Pubkey        // Address of coin token vault
  - pc_vault: Pubkey          // Address of PC (quote) token vault  
  - fees.swap_fee_numerator: u64 = 25
  - fees.swap_fee_denominator: u64 = 10000  // 0.25% fee
  - state_data.need_take_pnl_coin: u64  // Reserved PnL in coin
  - state_data.need_take_pnl_pc: u64    // Reserved PnL in PC
  - status: u64               // Check if swaps enabled
  - open_orders: Pubkey       // Only if using V1 swaps (Which I will not do ha-ha-ha)
  
2. Token Vault Accounts (SPL Token Accounts)
  Coin Vault:
  - Address: amm.coin_vault
  - Field needed: amount (u64)

  PC Vault:
  - Address: amm.pc_vault
  - Field needed: amount (u64)
  
  
3. For V1 Swaps Only (Skip for V2) (I will skip this part)

  - Open Orders Account at amm.open_orders
  - Market Event Queue (for exact pending fills)
  - Market State
"""


class RaydiumHybridAMMTranslater(Translater):
    def __init__(self, logger):
        super().__init__(logger)

    def translate_AmmInfo(self, x: str) -> dict:
        try:
            parsed_data = self.translate(x, market="state", name="AmmInfo")
            return {
                "status": parsed_data["status"],
                "baseVault": parsed_data["baseVault"],
                "quoteVault": parsed_data["quoteVault"],
                "baseNeedTakePnl": parsed_data.get('baseNeedTakePnl', 0),
                "quoteNeedTakePnl": parsed_data.get('quoteNeedTakePnl', 0),
            }
        except Exception as e:
            self.logger.error(e)
            return {}

    def translate_SPL(self, x: str) -> dict:
        try:
            parsed_data = self.translate(x, market="state", name="SPLWallet")
            return {
                "mint": parsed_data["mint"],
                "amount": parsed_data["amount"],
            }
        except Exception as e:
            self.logger.error(e)
            return {}

class RaydiumHybridAMM(Solana):
    def __init__(self, SOLANA_RPC_ENDPOINT=config.SOLANA_RPC_ENDPOINT, logger_name='RaydiumHybridAMM',
                 logger_file="RaydiumHybridAMM.log"):
        super().__init__(SOLANA_RPC_ENDPOINT)
        setup_logger(logger_name=logger_name, log_file=SOLANA_FETCHER_LOG_FILE)

        self.logger = get_logger(logger_name=logger_name)
        self.translater = RaydiumHybridAMMTranslater(self.logger)

    @staticmethod
    def _create_calldata(addresses: dict[str, RaydiumBigBoxVaultAddressScheme]) -> list:
        calldata_list = []
        for address, vault_address_scheme in addresses.items():
            calldata_list.extend([address, vault_address_scheme.quoteVault, vault_address_scheme.baseVault])

        return calldata_list

    def _assemble_big_box_data(self, raw_data: dict, addresses: dict[str, RaydiumBigBoxVaultAddressScheme]) -> dict:
        final_assembled_pools = {}
        for address, vault_address_scheme in addresses.items():
            baseVault = vault_address_scheme.baseVault
            quoteVault = vault_address_scheme.quoteVault

            try:
                raw_baseVault_info = raw_data.get(baseVault, [{}])[0].get('data')
                if not raw_baseVault_info:
                    self.logger.error(f"BaseVault info for address {address} has no data")
                    continue
                baseVault_info = self.translater.translate_SPL(raw_baseVault_info)
                if not baseVault_info:
                    self.logger.error(f"BaseVault info for address {address} couldn't be translated")
                    continue

                raw_quoteVault_info = raw_data.get(quoteVault, [{}])[0].get('data')
                if not raw_quoteVault_info:
                    self.logger.error(f"QuoteVault info for address {address} has no data")
                    continue
                quoteVault_info = self.translater.translate_SPL(raw_quoteVault_info)
                if not quoteVault_info:
                    self.logger.error(f"QuoteVault info for address {address} couldn't be translated")
                    continue

                raw_BaseInfo = raw_data.get(address, [{}])[0].get('data')
                if not raw_BaseInfo:
                    self.logger.error(f"BaseInfo info for address {address} has no data")
                    continue
                BaseInfo = self.translater.translate_AmmInfo(raw_BaseInfo)
                if not BaseInfo:
                    self.logger.error(f"BaseInfo info for address {address} couldn't be translated")
                    continue

                final_assembled_pools[address] = {
                    "baseVault": baseVault_info,
                    "quoteVault": quoteVault_info,
                    "BaseInfo": BaseInfo,
                }

            except Exception as e:
                self.logger.error(f"Error in assembling big box data for address {address}: {e}")

        return final_assembled_pools

    def _assemble_cache_data(self, raw_data: dict) -> dict:
        processed_data = {}
        for address, data_list in raw_data.items():
            try:
                raw = data_list[0].get('data')
                if not raw:
                    self.logger.error(f"Cache data for address {address} has no data")
                    continue
                amm_info = self.translater.translate_AmmInfo(raw)
                if not amm_info:
                    self.logger.error(f"Cache data for address {address} couldn't be translated")
                    continue
                processed_data[address] = amm_info
            except Exception as e:
                self.logger.error(f"Error in processing cache data for address {address}: {e}")

        return processed_data

    async def getCacheData(self, addresses: list) -> dict:
        try:
            raw_data = await self.getMultipleAccounts(addresses=addresses, field=['data'],
                                                      funcs={'data': lambda x: x[0]})
            return self._assemble_cache_data(raw_data)
        except Exception as e:
            self.logger.error(e)
            return {}

    async def getBigBox(self, addresses: dict[str, RaydiumBigBoxVaultAddressScheme]) -> dict:
        try:
            calldata_list = self._create_calldata(addresses)
            raw_data = await self.getMultipleAccounts(addresses=calldata_list, field=['data'],
                                                      funcs={'data': lambda x: x[0]})

            return self._assemble_big_box_data(raw_data, addresses)
        except Exception as e:
            self.logger.error(e)
            return {}
