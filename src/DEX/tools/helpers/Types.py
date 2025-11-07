from construct import *
import base58
from io import BytesIO




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
        return base58.b58encode(obj).decode()

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

class DynamicTickArray(Adapter):
    TICK_ARRAY_SIZE = 88
    UNINITIALIZED_LEN = 1
    INITIALIZED_LEN = 113

    def __init__(self):
        super().__init__(GreedyBytes)

    def _decode(self, obj, context, path):
        stream = BytesIO(obj)

        start_tick_index = Int32sl.parse_stream(stream)
        whirlpool = PubKey().parse_stream(stream)
        tick_bitmap = Int128ul().parse_stream(stream)

        ticks = []
        for i in range(self.TICK_ARRAY_SIZE):
            is_initialized = (tick_bitmap & (1 << i)) != 0

            if is_initialized:
                discriminator = Int8ul.parse_stream(stream)
                if discriminator != 1: raise Exception("Invalid tick data")

                tick_data = {
                    'initialized': True,
                    'liquidityNet': Int128sl().parse_stream(stream),
                    'liquidityGross': Int128ul().parse_stream(stream),
                    'feeGrowthOutsideA': Int128ul().parse_stream(stream),
                    'feeGrowthOutsideB': Int128ul().parse_stream(stream),
                    'reward_growths_outside': [
                        Int128ul().parse_stream(stream),
                        Int128ul().parse_stream(stream),
                        Int128ul().parse_stream(stream)
                    ]
                }
                ticks.append(tick_data)
            else:
                discriminator = Int8ul.parse_stream(stream)
                if discriminator != 0: raise Exception("Invalid tick data")

                ticks.append({
                    'initialized': False,
                    'liquidityNet': 0,
                    'liquidityGross': 0,
                    'feeGrowthOutsideA': 0,
                    'feeGrowthOutsideB': 0,
                    'reward_growths_outside': [0, 0, 0]
                })

        return {
            'start_tick_index': start_tick_index,
            'whirlpool': whirlpool,
            'tick_bitmap': tick_bitmap,
            'ticks': ticks
        }

    def _encode(self, obj, context, path):
        stream = BytesIO()

        stream.write(Int32sl.build(obj['start_tick_index']))
        stream.write(PubKey().build(obj['whirlpool']))
        stream.write(Int128ul().build(obj['tick_bitmap']))

        for tick in obj['ticks']:
            if tick['initialized']:
                stream.write(Int8ul.build(1))
                stream.write(Int128sl().build(tick['liquidity_net']))
                stream.write(Int128ul().build(tick['liquidity_gross']))
                stream.write(Int128ul().build(tick['fee_growth_outside_a']))
                stream.write(Int128ul().build(tick['fee_growth_outside_b']))
                for reward in tick['reward_growths_outside']:
                    stream.write(Int128ul().build(reward))
            else:
                stream.write(Int8ul.build(0))

        return stream.getvalue()


__RewardInfoStruct = Struct(
    "reward_state" / Int8ul,
    "open_time" / Int64ul,
    "end_time" / Int64ul,
    "last_update_time" / Int64ul,
    "emissions_per_second_x64" / Int128ul(),
    "reward_total_emissioned" / Int64ul,
    "reward_claimed" / Int64ul,
    "token_mint" / PubKey(),
    "token_vault" / PubKey(),
    "authority" / PubKey(),
    "reward_growth_global_x64" / Int128ul(),
)

PoolStateRaydium = Struct(
    "bump" / Array(1, Int8ul),
    "amm_config" / PubKey(),
    "owner" / PubKey(),
    "token_mint_0" / PubKey(),
    "token_mint_1" / PubKey(),
    "token_vault_0" / PubKey(),
    "token_vault_1" / PubKey(),
    "observation_key" / PubKey(),
    "mint_decimals_0" / Int8ul,
    "mint_decimals_1" / Int8ul,
    "tick_spacing" / Int16ul,
    "liquidity" / Int128ul(),
    "sqrt_price_x64" / Int128ul(),
    "tick_current" / Int32sl,
    "padding3" / Int16ul,
    "padding4" / Int16ul,
    "fee_growth_global_0_x64" / Int128ul(),
    "fee_growth_global_1_x64" / Int128ul(),
    "protocol_fees_token_0" / Int64ul,
    "protocol_fees_token_1" / Int64ul,
    "swap_in_amount_token_0" / Int128ul(),
    "swap_out_amount_token_1" / Int128ul(),
    "swap_in_amount_token_1" / Int128ul(),
    "swap_out_amount_token_0" / Int128ul(),
    "status" / Int8ul,
    "padding" / Array(7, Int8ul),
    "reward_infos" / Array(3, __RewardInfoStruct),
    "tick_array_bitmap" / Array(16, Int64ul),
    "total_fees_token_0" / Int64ul,
    "total_fees_claimed_token_0" / Int64ul,
    "total_fees_token_1" / Int64ul,
    "total_fees_claimed_token_1" / Int64ul,
    "fund_fees_token_0" / Int64ul,
    "fund_fees_token_1" / Int64ul,
    "open_time" / Int64ul,
    "recent_epoch" / Int64ul,
    "padding1" / Array(24, Int64ul),
    "padding2" / Array(32, Int64ul),
)



__TickState = Struct(
    "tick" / Int32sl,
    "liquidity_net" / Int128sl(),
    "liquidity_gross" / Int128ul(),
    "fee_growth_outside_0_x64" / Int128ul(),
    "fee_growth_outside_1_x64" / Int128ul(),
    "reward_growths_outside_x64" / Array(3, Int128ul()),
    "padding" / Array(13, Int32ul)
)

TickArrayStateRaydium = Struct(
    "pool_id" / PubKey(),
    "start_tick_index" / Int32sl,
    "ticks" / Array(60, __TickState),
    "initialized_tick_count" / Int8ul,
    "recent_epoch" / Int64ul,
    "padding" / Array(107, Int8ul),
)