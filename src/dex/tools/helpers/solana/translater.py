import base64
from typing import Literal

from construct import *

####################################
from src.dex.tools.helpers.solana.struct_builder import StructBuilder
####################################



class Translater:
    def __init__(self, logger):
        self.structure_builder = StructBuilder()
        self.ANCHOR_DISCRIMINATOR_SIZE_IN_HEX = 16
        self.ANCHOR_DISCRIMINATOR_SIZE_IN_BYTE = 8
        self.logger = logger
        self.known_discriminators = {
            "11d8f68ee1c7da38": "DynamicTickArray",
            "4561bdbe6e0742bb": "TickArray",
            "3f95d10ce1806309": "Whirlpool",
            "8bc283b38cb3e5f4": "Oracle",
            "210b3162b565b10d": "LbPair",
        }

    def __to_dict(self, obj) -> dict | list | int | str:
        if isinstance(obj, ListContainer):
            return [self.__to_dict(v) for v in obj]

        elif isinstance(obj, Container):
            try:
                return_data = {}
                for k, v in obj.items():
                    if k == "_io":
                        continue
                    return_data[k] = self.__to_dict(v)
                return return_data
            except AttributeError as e:
                return str(obj)

        else:
            return obj

    def __determine_name(self, data: hex):
        discriminator = str(data)[:self.ANCHOR_DISCRIMINATOR_SIZE_IN_HEX]
        name = self.known_discriminators.get(discriminator)
        if not name:
            raise Exception(f"Unknown discriminator: {discriminator}")

        return name

    def __translateSPLWallet(self, data: hex) -> dict:
        data_bytes = bytes.fromhex(data)
        return self.__to_dict(self.structure_builder.TokenAccount.parse(data_bytes))

    def __translateMintAccount(self, data: hex) -> dict:
        data_bytes = bytes.fromhex(data)
        return self.__to_dict(self.structure_builder.MintAccount.parse(data_bytes))

    def __translateDynamicTickArrayOrca(self, data: hex) -> dict:
        data_bytes = bytes.fromhex(data[self.ANCHOR_DISCRIMINATOR_SIZE_IN_HEX:])
        return self.structure_builder.DynamicTickArray.parse(data_bytes)

    def __translateRaydiumCLMMPoolState(self, data: hex) -> dict:
        data_bytes = bytes.fromhex(data[self.ANCHOR_DISCRIMINATOR_SIZE_IN_HEX:])
        parsed_data = self.structure_builder.PoolStateRaydium.parse(data_bytes)
        return self.__to_dict(parsed_data)

    def __translateRaydiumCLMMTickArray(self, data: hex) -> dict:
        data_bytes = bytes.fromhex(data[self.ANCHOR_DISCRIMINATOR_SIZE_IN_HEX:])
        parsed_data = self.structure_builder.TickArrayStateRaydium.parse(data_bytes)
        return self.__to_dict(parsed_data)

    def __translateRaydiumAMMInfo(self, data: hex) -> dict:
        data_bytes = bytes.fromhex(data)
        data_len = len(data_bytes)
        if data_len == 752:
            parsed_data = self.structure_builder.RaydiumAmmInfo.parse(data_bytes)
        elif data_len == 637:
            parsed_data = self.structure_builder.RaydiumAlternativeAmmInfo.parse(
                data_bytes[self.ANCHOR_DISCRIMINATOR_SIZE_IN_BYTE:])
        else:
            raise Exception(f"Unexpected data length: {data_len}")

        return self.__to_dict(parsed_data)

    def translate(self, data: str, market: Literal["state", "dlmm", "ammV2", "ammV1", "metadata"],
                  name: str = None) -> dict:
        try:
            data = base64.b64decode(data).hex() if isinstance(data, str) else None
            if not data:
                return {}

            if not name:
                name = self.__determine_name(data)

            if name == "SPLWallet":
                return self.__translateSPLWallet(data)
            elif name == "MintAccount":
                return self.__translateMintAccount(data)
            elif name == "DynamicTickArray":
                return self.__translateDynamicTickArrayOrca(data)
            elif name == "PoolState" and market == "state":
                return self.__translateRaydiumCLMMPoolState(data)
            elif name == "TickArray" and market == "state":
                return self.__translateRaydiumCLMMTickArray(data)
            elif name == "AmmInfo" and market == "state":
                return self.__translateRaydiumAMMInfo(data)



            data_bytes = bytes.fromhex(data[self.ANCHOR_DISCRIMINATOR_SIZE_IN_HEX:])
            structure = self.structure_builder.get_Struct_from_IDL(name=name, market=market)

            parsed_data = structure.parse(data_bytes)
            return self.__to_dict(parsed_data)
        except Exception as e:
            self.logger.error(f"Failed to translate account '{name}' for market '{market}': {e}")
            return {}