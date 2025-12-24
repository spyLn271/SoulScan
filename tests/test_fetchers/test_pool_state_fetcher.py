import json
import asyncio
from solders.pubkey import Pubkey as SolanaPubkey
from src.Config import config
from src import OrcaCLMM, Solana, MeteoraDLMM, MeteoraDAMMv2, RaydiumCLMM, RaydiumHybridAMM
from src.DEX.tools.helpers.struct_builder import StructBuilder
from src.DEX.DEXes.Raydium.RaydiumScheme import RaydiumBigBoxVaultAddressScheme



async def testSolana():
    async with Solana() as solana:
        target_address = '8GkHvtX21hVUWSWbAXDzBeGf7P4ShgNLJi45WUiYnDrc'
        start_index = ((41072 // (config.TICK_ARRAY_SIZE_RAYDIUM_CLMM * 1)) *
                (config.TICK_ARRAY_SIZE_RAYDIUM_CLMM * 1))
        print(start_index)
        program_id = SolanaPubkey.from_string("CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK")
        pda = solana.findProgramDerivedAddress([
            b"tick_array", bytes(SolanaPubkey.from_string(target_address)),
            start_index.to_bytes(4, signed=True)], program_id)
        print(pda)


async def testOrcaCLMM():
    from src import WhirlpoolClmmScheme

    async with OrcaCLMM() as orcaCLMM:
        addresses = [
            "9RqDTfwCx2SgxsvKpspQHc38HUo3B6hRd3oR9JR966Ps"
        ]

        data = await orcaCLMM.getBigBox(addresses=addresses,
                                        tick_spacing_list=[1],
                                        current_tick_list=[-2],
                                        af_list=[False])
        print(json.dumps(data, indent=4))

        # cache_data = await orcaCLMM.getCacheData(addresses=addresses)
        # print(json.dumps(cache_data, indent=4))



async def testMeteoraDLMM():
    from src import MeteoraDlmmCacheScheme
    async with MeteoraDLMM() as dlmm:
        addresses = ['5rCf1DM8LjKTw4YqhnoLcngyZYeNnQqztScTogYHAS6']
        cache = await dlmm.getCacheData(addresses=addresses)
        print(json.dumps(cache, indent=4))
        print(MeteoraDlmmCacheScheme(**cache.get(addresses[0])).model_dump())

        # ingredient = dlmm._create_calldata_for_LbPair(address='5rCf1DM8LjKTw4YqhnoLcngyZYeNnQqztScTogYHAS6',
        #                                               bin_id=-4209, bin_step=4)
        # print(ingredient)

        bigbox = await dlmm.getBigBox(addresses=['5rCf1DM8LjKTw4YqhnoLcngyZYeNnQqztScTogYHAS6'],
                                      bin_id_list=[-4863])

        print(json.dumps(bigbox, indent=4))

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
        print(json.dumps(data, indent=4))

        cache_data = await clmm.getCacheData(addresses=addresses)
        print(json.dumps(cache_data, indent=4))
        print(RaydiumCacheClmmScheme(**cache_data.get(addresses[0])))
        data_first = RaydiumClmmScheme(**data.get(addresses[0]))
        print(data_first)

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
        print(json.dumps(data, indent=4))
        print(RaydiumHybridAmmScheme(**data.get(addresses[0])))



def testStructBuilder():
    builder = StructBuilder()
    builder.get_Struct_from_IDL(name='Pool', market='ammV2')

async def testMeteoraDlmmState():
    from src.DataFetcher.rpc_clients.Meteora.MeteoraDlmmState import MeteoraDlmmState
    dlmm_state = MeteoraDlmmState()
    await dlmm_state.main()


async def testMeteoraDammV2State():
    from src.DataFetcher.rpc_clients.Meteora.MeteoraDammV2State import MeteoraDammV2State
    dammv2_state = MeteoraDammV2State()
    await dammv2_state.main()


async def testOrcaCLMMState():
    from src.DataFetcher.rpc_clients.Orca.OrcaClmmState import OrcaClmmState
    orcaCLMM_state = OrcaClmmState()
    await orcaCLMM_state.main()

async def testRaydiumAmmState():
    from src.DataFetcher.rpc_clients.Raydium.RaydiumAmmState import RaydiumAmmState
    raydiumAmm_state = RaydiumAmmState()
    await raydiumAmm_state.main()

async def testRaydiumClmmState():
    from src.DataFetcher.rpc_clients.Raydium.RaydiumClmmState import RaydiumClmmState
    raydiumClmm_state = RaydiumClmmState()
    await raydiumClmm_state.main()

def bootstrap(func: callable):
    asyncio.run(func())

def run_all_state_fetchers():
    import multiprocessing
    pool = multiprocessing.Pool(processes=4)
    pool.map(bootstrap, [testMeteoraDlmmState, testOrcaCLMMState, testRaydiumAmmState, testRaydiumClmmState])



if __name__ == '__main__':
    bootstrap(testOrcaCLMMState)