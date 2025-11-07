import json
import asyncio
from src import OrcaCLMM, Solana, MeteoraDLMM, MeteoraDAMMv2, RaydiumCLMM
from src.DEX.tools.helpers.struct_builder import StructBuilder


async def testSolana():
    async with Solana() as solana:
        addresses = ['3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv',]

        res = await solana.getMultipleAccounts(addresses, field=['data'], funcs={'data': lambda x: x[0]})
        data = res.get(addresses[0], [{}])[0].get('data')
        print(data)
        parsed_data = solana.translater.translate(data=data, market='raydium', name='PoolState')
        print(json.dumps(parsed_data, indent=4))

async def testOrcaCLMM():
    from src import WhirlpoolClmmScheme

    async with OrcaCLMM() as orcaCLMM:
        addresses = [
            '8KmNsjXFqaGCuajbHWN3K1W8fVW1NGZ9u4EUiP9EN1N7',
        ]

        data = await orcaCLMM.getBigBox(addresses=addresses,
                                        tick_spacing_list=[32896],
                                        current_tick_list=[-162547],
                                        af=True)
        print(WhirlpoolClmmScheme(**data.get(addresses[0])))
        # cache_data = await orcaCLMM.getCacheData(addresses=addresses, af=True)
        # print(json.dumps(cache_data, indent=4))
        # print(orcaCLMM.translater.structure_builder.StructCache)

async def testMeteoraDLMM():
    from src import MeteoraDlmmScheme
    async with MeteoraDLMM() as dlmm:
        # addresses = ['5rCf1DM8LjKTw4YqhnoLcngyZYeNnQqztScTogYHAS6',
        #              'tcQjxoHqrDjZAwBaWggZcaZhXvrard9VDvbuz2shsXH']
        # cache = await dlmm.getCacheData(addresses=addresses)
        # print(json.dumps(cache, indent=4))

        # ingredient = dlmm._create_calldata_for_LbPair(address='5rCf1DM8LjKTw4YqhnoLcngyZYeNnQqztScTogYHAS6',
        #                                               bin_id=-4209, bin_step=4)
        # print(ingredient)

        bigbox = await dlmm.getBigBox(addresses=['B1ajRc5TgtEpPHgP5Pzyb6YrHJ6TZWJ3mzoZs41sT8EF'],
                                      bin_id_list=[27])

        # print(json.dumps(bigbox, indent=4))
        print(MeteoraDlmmScheme(**bigbox.get('B1ajRc5TgtEpPHgP5Pzyb6YrHJ6TZWJ3mzoZs41sT8EF')))

async def testMeteoraDAMMv2():
    from src import MeteoraDammV2Scheme
    async with MeteoraDAMMv2() as dammv2:
        addresses = ['8Pm2kZpnxD3hoMmt4bjStX2Pw2Z9abpbHzZxMPqxPmie',
                     '8X5yDboAEtV1SeoZoG3issAc9zB6qGSe5ZCtJyUz2S5W']
        big_box = await dammv2.getBigBox(addresses=addresses)
        # print(json.dumps(big_box, indent=4))
        print(MeteoraDammV2Scheme(**big_box.get(addresses[0])))


async def testRaydiumCLMM():
    from src import RaydiumClmmScheme
    async with RaydiumCLMM() as clmm:
        addresses = ['3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv']
        data = await clmm.getBigBox(addresses=addresses, current_tick_list=[-18813],
        tick_spacing_list=[1])
        # print(json.dumps(data, indent=4))
        #
        # cache_data = await clmm.getCacheData(addresses=addresses)
        # print(json.dumps(cache_data, indent=4))
        data_first = RaydiumClmmScheme(**data.get(addresses[0]))
        print(data_first.PoolState.tick_spacing)


def testStructBuilder():
    builder = StructBuilder()
    builder.get_Struct_from_IDL(name='Pool', market='ammV2')




if __name__ == '__main__':
    asyncio.run(testRaydiumCLMM())
    # testStructBuilder()