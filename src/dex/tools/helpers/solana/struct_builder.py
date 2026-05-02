from construct import *
from typing import *
import base58
import pydantic

####################################
from src.dex.tools.helpers.solana import IDLs
from src.dex.tools.helpers.solana.types import (Int128ul, Int128sl, Bool, DynamicTickArray,
                                                PoolStateRaydium, TickArrayStateRaydium, RaydiumAmmInfo,
                                                RaydiumAlternativeAmmInfo)
####################################

class IDLScheme(pydantic.BaseModel):
    fields: list[dict]
    type: str

class PubKey(Adapter):
    def __init__(self):
        super().__init__(Bytes(32))

    def _decode(self, obj, context, path):
        return base58.b58encode(obj).decode()

    def _encode(self, obj, context, path):
        return base58.b58decode(obj)

class StructBuilder:
    def __init__(self):
        super().__init__()

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
            'metadata': ('defined',),
            'dlmm': ('defined', 'name'),
            'ammV2': ('defined', 'name'),
        }

        self.merging = {
            'metadata': ('types', 'accounts'),
            'dlmm': ('types',),
            'ammV2': ('types',),
        }

        self.StructCache: Dict[str, Struct] = {}
        self.sterilized_idl: Dict[str, Dict[str, IDLScheme]] = {}

        self.idls = IDLs.idls


        self.TokenAccount = Struct(
            "mint" / PubKey(),
            "owner" / PubKey(),
            "amount" / Int64ul,
            "delegate_option" / Int32ul,
            "delegate" / self.SolanaPubkey,
            "state" / Int8ul,
            "is_native_option" / Int32ul,
            "is_native" / Int64ul,
            "delegated_amount" / Int64ul,
            "close_authority_option" / Int32ul,
            "close_authority" / self.SolanaPubkey,
        )

        self.MintAccount = Struct(
            "mint_authority_option" / Int32ul,
            "mint_authority" / self.SolanaPubkey,
            "supply" / Int64ul,
            "decimals" / Int8ul,
            "is_initialized" / Bool(),
            "freeze_authority_option" / Int32ul,
            "freeze_authority" / self.SolanaPubkey,
        )

        self.DynamicTickArray = DynamicTickArray()
        self.PoolStateRaydium = PoolStateRaydium
        self.TickArrayStateRaydium = TickArrayStateRaydium
        self.RaydiumAmmInfo = RaydiumAmmInfo
        self.RaydiumAlternativeAmmInfo = RaydiumAlternativeAmmInfo


    def _sterilize_idl(self, idl: dict, merging: tuple, market: str) -> Dict[str, IDLScheme]:
        if market in self.sterilized_idl:
            return self.sterilized_idl[market]

        sterilized_idl: Dict[str, IDLScheme] = {}

        for key in merging:
            for value in idl[key]:
                type = value.get('type', {}).get('kind')

                if type == 'struct':
                    sterilized_idl[value['name']] = IDLScheme(fields=value.get('type', {}).get('fields'),
                                                              type=type)

                elif type == 'enum':
                    sterilized_idl[value['name']] = IDLScheme(fields=value.get('type', {}).get('variants'),
                                                              type=type)

        self.sterilized_idl[market] = sterilized_idl
        return sterilized_idl

    @staticmethod
    def _get_reference_type(typedef: dict, definition: tuple) -> str:
        cur = typedef
        for key in definition:
            cur = cur.get(key, {})
        if not isinstance(cur, str):
            raise Exception("Failed to resolve type: {typedef}")
        return cur

    def _create_struct(self, idl_name: str, sterilized_idl: Dict[str, IDLScheme], definition: tuple[str]) -> Struct | Any:
        target_fields = sterilized_idl.get(idl_name)
        if not target_fields: raise Exception(f"Struct {idl_name} not found in IDL.")

        fields, type = target_fields.fields, target_fields.type
        if type == 'enum':
            return self._create_enum(idl_name=idl_name, sterilized_idl=sterilized_idl, definition=definition)

        struct_fields = []
        for field in fields:
            field_name = field.get('name')
            field_type = field.get('type', {})

            if isinstance(field_type, dict) and not field_type.get('array'):
                if field_type.get('vec'):
                    target_idl_name = self._get_reference_type(field_type.get('vec'), definition)
                else:
                    target_idl_name = self._get_reference_type(field_type, definition)
                sub_struct = self._create_struct(target_idl_name, sterilized_idl, definition)
                struct_fields.append((field_name, sub_struct))

            elif isinstance(field_type, dict) and field_type.get('array'):
                array_type = field_type.get('array')[0]
                array_length = field_type.get('array')[1]

                if isinstance(array_type, dict):
                    target = self._get_reference_type(array_type, definition)
                    sub_struct = self._create_struct(target, sterilized_idl, definition)
                    struct_fields.append((field_name, Array(array_length, sub_struct)))
                elif isinstance(array_type, str):
                    struct_fields.append((field_name, Array(array_length, self.type_dict[array_type])))
                else:
                    raise Exception(f"Failed to parse array type: {array_type}")

            else:
                struct_fields.append((field_name, self.type_dict[field_type]))

        return Struct(*[name / field for name, field in struct_fields])

    def _create_enum(self, idl_name: str, sterilized_idl: Dict[str, IDLScheme], definition: tuple[str]) -> Switch | Any:
        target_fields = sterilized_idl.get(idl_name)
        if not target_fields: raise Exception(f"Struct {idl_name} not found in IDL.")

        variants, type = target_fields.fields, target_fields.type
        if type == 'struct':
            return self._create_struct(idl_name=idl_name, sterilized_idl=sterilized_idl, definition=definition)

        cases = {}
        for i, variant in enumerate(variants):
            variant_name = variant.get('name')
            variant_fields = variant.get('fields')
            if not variant_fields:
                cases[i] = variant_name / Pass
                continue

            for variant_field in variant_fields:
                if isinstance(variant_field, dict):
                    target_idl_name = self._get_reference_type(variant_field, definition)
                    sub_struct = self._create_struct(target_idl_name, sterilized_idl, definition)
                    cases[i] = variant_name / sub_struct
                elif isinstance(variant_field, str):
                    cases[i] = variant_name / self.type_dict[variant_field]
                else:
                    raise Exception(f"Failed to parse variant field: {variant_field}")

        return Switch(self.type_dict['u8'], cases)

    def get_Struct_from_IDL(self, name: str, market: str) -> Struct:
        if self.StructCache.get(name):
            return self.StructCache.get(name)

        sterilized_idl = self._sterilize_idl(idl=self.idls.get(market),
                                             merging=self.merging.get(market),
                                             market=market)

        fields, type = sterilized_idl.get(name).fields, sterilized_idl.get(name).type
        if type == 'struct':
            self.StructCache[name] = self._create_struct(idl_name=name, sterilized_idl=sterilized_idl,
                                                         definition=self.definition.get(market))
        elif type == 'enum':
            self.StructCache[name] = self._create_enum(idl_name=name, sterilized_idl=sterilized_idl,
                                                       definition=self.definition.get(market))
        else:
            raise Exception(f"Failed to parse type: {type}")

        return self.StructCache[name]


def explore_construct(construct_obj: Any, indent: int = 0):
    indent_str = "    " * indent

    if not isinstance(construct_obj, Construct):
        print(f"{indent_str}{repr(construct_obj)}")
        return

    if isinstance(construct_obj, Renamed):
        print(f"{indent_str}Field: '{construct_obj.name}'")
        explore_construct(construct_obj.subcon, indent + 1)
        return

    class_name = construct_obj.__class__.__name__
    name = construct_obj.name or f"<{class_name}>"
    print(f"{indent_str}▶ {name} ({class_name})")


    if isinstance(construct_obj, Struct):
        print(f"{indent_str}  Fields:")
        for subcon in construct_obj.subcons:
            explore_construct(subcon, indent + 1)

    elif isinstance(construct_obj, Switch):
        print(f"{indent_str}  Switching on:")
        explore_construct(construct_obj.keyfunc, indent + 1)

        print(f"{indent_str}  Cases:")
        for key, case_parser in construct_obj.cases.items():
            print(f"{indent_str}    - Case {key}:")
            explore_construct(case_parser, indent + 2)

    elif isinstance(construct_obj, Array):
        count = construct_obj.count
        print(f"{indent_str}  Count: {count}")
        print(f"{indent_str}  Element Type:")
        explore_construct(construct_obj.subcon, indent + 1)

    elif isinstance(construct_obj, Adapter):
        if construct_obj.subcon:
            print(f"{indent_str}  Wraps:")
            explore_construct(construct_obj.subcon, indent + 1)

if __name__ == '__main__':
    sb = StructBuilder()
    struct = sb.get_Struct_from_IDL(name='TickArray', market='metadata')
    explore_construct(struct)
