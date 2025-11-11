import json
import asyncio
from src import OrcaCLMM, Solana, MeteoraDLMM, MeteoraDAMMv2, RaydiumCLMM, RaydiumHybridAMM, WhirlpoolCacheClmmScheme
from src.DEX.tools.helpers.struct_builder import StructBuilder
from src.DEX.DEXes.Raydium.RaydiumScheme import RaydiumBigBoxVaultAddressScheme


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

        # data = await orcaCLMM.getBigBox(addresses=addresses,
        #                                 tick_spacing_list=[32896],
        #                                 current_tick_list=[-162547],
        #                                 af=True)
        # print(WhirlpoolClmmScheme(**data.get(addresses[0])))
        cache_data = await orcaCLMM.getCacheData(addresses=addresses, af=True)
        print(json.dumps(cache_data, indent=4))
        print(WhirlpoolCacheClmmScheme(**cache_data.get('8KmNsjXFqaGCuajbHWN3K1W8fVW1NGZ9u4EUiP9EN1N7')))


async def testMeteoraDLMM():
    from src import MeteoraDlmmScheme, MeteoraDlmmCacheScheme
    async with MeteoraDLMM() as dlmm:
        addresses = ['5rCf1DM8LjKTw4YqhnoLcngyZYeNnQqztScTogYHAS6']
        cache = await dlmm.getCacheData(addresses=addresses)
        print(json.dumps(cache, indent=4))
        print(MeteoraDlmmCacheScheme(**cache.get(addresses[0])).model_dump())

        # ingredient = dlmm._create_calldata_for_LbPair(address='5rCf1DM8LjKTw4YqhnoLcngyZYeNnQqztScTogYHAS6',
        #                                               bin_id=-4209, bin_step=4)
        # print(ingredient)

        # bigbox = await dlmm.getBigBox(addresses=['B1ajRc5TgtEpPHgP5Pzyb6YrHJ6TZWJ3mzoZs41sT8EF'],
        #                               bin_id_list=[27])
        #
        # # print(json.dumps(bigbox, indent=4))
        # print(MeteoraDlmmScheme(**bigbox.get('B1ajRc5TgtEpPHgP5Pzyb6YrHJ6TZWJ3mzoZs41sT8EF')))

async def testMeteoraDAMMv2():
    from src import MeteoraDammV2Scheme
    async with MeteoraDAMMv2() as dammv2:
        addresses = ['8Pm2kZpnxD3hoMmt4bjStX2Pw2Z9abpbHzZxMPqxPmie',
                     '8X5yDboAEtV1SeoZoG3issAc9zB6qGSe5ZCtJyUz2S5W']
        big_box = await dammv2.getBigBox(addresses=addresses)
        # print(json.dumps(big_box, indent=4))
        print(MeteoraDammV2Scheme(**big_box.get(addresses[0])))
        print('ok'if hasattr(dammv2, 'getBigBox') else 'no')
        print('ok'if hasattr(dammv2, 'getCacheData') else 'no')

async def testRaydiumCLMM():
    from src import RaydiumClmmScheme, RaydiumCacheClmmScheme
    async with RaydiumCLMM() as clmm:
        addresses = ['3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv']
        data = await clmm.getBigBox(addresses=addresses, current_tick_list=[-18813],
        tick_spacing_list=[1])
        # print(json.dumps(data, indent=4))
        #
        cache_data = await clmm.getCacheData(addresses=addresses)
        print(json.dumps(cache_data, indent=4))
        print(RaydiumCacheClmmScheme(**cache_data.get(addresses[0])))
        print('ok' if hasattr(clmm, 'getBigBox') else 'no')
        print('ok' if hasattr(clmm, 'getCacheData') else 'no')
        # data_first = RaydiumClmmScheme(**data.get(addresses[0]))
        # print(data_first.PoolState.tick_spacing)

async def testRaydiumAMM():
    from src import RaydiumHybridAmmCacheScheme, RaydiumHybridAmmScheme
    async with RaydiumHybridAMM() as amm:
        addresses = ["58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2"]
        cache = await amm.getCacheData(addresses=addresses)
        print(json.dumps(cache, indent=4))
        print(RaydiumHybridAmmCacheScheme(**cache.get(addresses[0])))

        address_dict = {
            "58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2": RaydiumBigBoxVaultAddressScheme(
                baseVault="DQyrAcCrDXQ7NeoqGgDCZwBvWDcYmFCjSb9JtteuvPpz",
                quoteVault="HLmqeL62xR1QoZ1HKKbXRrdN1p3phKpxRMb2VVopvBBz"
            )
        }

        data = await amm.getBigBox(addresses=address_dict)
        print(RaydiumHybridAmmScheme(**data.get(addresses[0])))



def testStructBuilder():
    builder = StructBuilder()
    builder.get_Struct_from_IDL(name='Pool', market='ammV2')




if __name__ == '__main__':
    asyncio.run(testRaydiumCLMM())
    # testStructBuilder()