from construct import *
from typing import *
import base64
import logging
import base58
import json
import redis


####################################
from src.Config import IDLs, config
####################################

class Int128ul(Adapter):
    def __init__(self):
        super().__init__(Bytes(16))

    def _decode(self, obj, context, path):
        return int.from_bytes(obj, 'little',)

    def _encode(self, obj, context, path):
        if not isinstance(obj, int):
            raise Exception("value is not an integer")
        return obj.to_bytes(16, 'little')

class Int128sl(Adapter):
    def __init__(self):
        super().__init__(Bytes(16))

    def _decode(self, obj, context, path):
        return int.from_bytes(obj, 'little', signed=True)

    def _encode(self, obj, context, path):
        if not isinstance(obj, int):
            raise Exception("value is not an integer")
        return obj.to_bytes(16, 'little', signed=True)

class PubKey(Adapter):
    def __init__(self):
        super().__init__(Bytes(32))

    def _decode(self, obj, context, path):
        return base58.b58encode(obj).decode('utf-8')

    def _encode(self, obj, context, path):
        return base58.b58decode(obj)

class Bool(Adapter):
    def __init__(self):
        super().__init__(Bytes(1))

    def _decode(self, obj, context, path):
        parsed = Int8ul.parse(obj)
        return bool(parsed)

    def _encode(self, obj, context, path):
        if not isinstance(obj, bool):
            raise Exception("value is not a boolean")
        return Int8ul.build(1 if obj else 0)


class Helper:
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)

        self.SolanaPubkey = PubKey()
        self.bool = Bool()
        self.u8 = Int8ul
        self.u16 = Int16ul
        self.u32 = Int32ul
        self.u64 = Int64ul
        self.i32 = Int32sl
        self.i64 = Int64sl
        self.i128 = Int128sl()
        self.u128 = Int128ul()
        self.type_dict = {
            'u128': self.u128,
            'u64': self.u64,
            'u32': self.u32,
            'u16': self.u16,
            'u8': self.u8,
            'i32': self.i32,
            'i64': self.i64,
            'i128': self.i128,
            'publicKey': self.SolanaPubkey,
            'pubkey': self.SolanaPubkey,
            'bool': self.bool,
        }

        self.definition = {
            'orca': ('defined', ),
            'dlmm': ('defined', 'name'),
        }

        self.merging = {
            'orca': ('types', 'accounts'),
            'dlmm': ('types', ),
        }

        self.StructCache = {}

        self.idls = IDLs.idls

        COption_Pubkey = Struct(
            "option" / Int32ul,
            "value" / If(this.option == 1, PubKey())
        )

        COption_U64 = Struct(
            "option" / Int32ul,
            "value" / If(this.option == 1, Int64ul)
        )

        self.TokenAccount = Struct(
            "mint" / PubKey(),
            "owner" / PubKey(),
            "amount" / Int64ul,
            "delegate" / COption_Pubkey,
            "state" / Int8ul,
            "is_native" / COption_U64,
            "delegated_amount" / Int64ul,
            "close_authority" / COption_Pubkey
        )

    @staticmethod
    def _get_address_chunk(addresses, chunk_size=100) -> list:
        return [addresses[i:i + chunk_size] for i in range(0, len(addresses), chunk_size)]

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

    @staticmethod
    def __resolve_type(typedef, keys) -> str:
        cur = typedef
        for k in keys:
            cur = cur.get(k, {})
        if not isinstance(cur, str):
            raise Exception(f"Failed to resolve type: {typedef}")
        return cur

    def getStructFromIDL(self, idl: dict, target_name: str, definition: tuple, merging: tuple) -> Struct:
        sterilized_types = {}
        for key in merging:
            for value in idl[key]:
                if value.get('type', {}).get('kind') == 'struct':
                    sterilized_types[value['name']] = value.get('type', {}).get('fields')

        if not sterilized_types.get(target_name):
            raise Exception(f"Struct {target_name} not found in IDL.")

        def buildStruct(name: str) -> Struct:
            struct_fields = []
            for field in sterilized_types[name]:
                field_type = field.get('type')
                field_name = field.get('name')

                if isinstance(field_type, dict) and not field_type.get('array') and not field_type.get('vec'):
                    target = self.__resolve_type(field_type, definition)
                    struct_fields.append((field_name, buildStruct(target)))

                elif isinstance(field_type, dict) and not field_type.get('array') and field_type.get('vec'):
                    target = self.__resolve_type(field_type.get('vec'), definition)
                    struct_fields.append((field_name, buildStruct(target)))

                elif isinstance(field_type, dict) and field_type.get('array'):
                    array_type = field_type.get('array')[0]
                    array_length = field_type.get('array')[1]

                    if isinstance(array_type, dict):
                        target = self.__resolve_type(array_type, definition)
                        struct_fields.append((field_name, Array(array_length, buildStruct(target))))
                    elif isinstance(array_type, str):
                        struct_fields.append((field_name, Array(array_length, self.type_dict[array_type])))
                    else:
                        raise Exception(f"Failed to parse array type: {array_type}")

                else:
                    struct_fields.append((field_name, self.type_dict[field_type]))

            return Struct(*[name / field for name, field in struct_fields])

        return buildStruct(target_name)

    def translate(self, data: str, type_name: str, market: str) -> dict:
        idl = self.idls.get(market)
        if not idl: raise Exception(f"IDLS for {market} not found.")

        try:
            data = base64.b64decode(data).hex() if isinstance(data, str) else None
            if not data:
                return {}

            data_bytes = bytes.fromhex(data[16:])
            structure = self.StructCache.get(type_name)
            if not structure:
                structure = self.getStructFromIDL(idl=idl, target_name=type_name,
                                                  definition=self.definition[market], merging=self.merging[market])
                self.StructCache[type_name] = structure

            parsed_data = structure.parse(data_bytes)
            return self.__to_dict(parsed_data)
        except Exception as e:
            self.logger.error(e)
            return {}

    def translateSPLWallet(self, data) -> dict:
        data = base64.b64decode(data).hex() if isinstance(data, str) else None
        if not data:
            return {}

        data_bytes = bytes.fromhex(data)

        return self.__to_dict(self.TokenAccount.parse(data_bytes))

    def getPoolsList(self, dex, protocol) -> list:
        pools_list = []
        data = self.r.get(config.REDIS_METADATA_KEY % (dex, protocol))
        for pool in json.loads(data):
            pools_list.append(pool)

        return pools_list

    def findProgramDerivedAddress(self, seeds: list, bump: int, program_id: str) -> str:
        pass
