import json
import asyncio
from src.DataFetcher.api_clients.Meteora.MeteoraDlmmMetadata import MeteoraDlmmMetadata
from src.DataFetcher.api_clients.Meteora.MeteoraDammV2Metadata import MeteoraDammV2Metadata
from src.DataFetcher.api_clients.Orca.OrcaClmmMetada import OrcaClmmMetadata
from src.DataFetcher.api_clients.Raydium.RaydiumClmmMetadata import RaydiumClmmMetadata
from src.DataFetcher.api_clients.Raydium.RaydiumHybridAmmMetadata import RaydiumHybridAmmMetadata


async def testMeteoraDlmmMetadata():
    async with MeteoraDlmmMetadata() as dlmm:
        await dlmm.main()

async def testMeteoraDammV2Metadata():
    async with MeteoraDammV2Metadata() as dammv2:
        await dammv2.main()

async def testOrcaCLMMMetadata():
    async with OrcaClmmMetadata() as orcaCLMM:
        await orcaCLMM.main()

async def testRaydiumClmmMetadata():
    async with RaydiumClmmMetadata() as raydiumCLMM:
        await raydiumCLMM.main()

async def testRaydiumHybridAmmMetadata():
    async with RaydiumHybridAmmMetadata() as raydiumHybridAmm:
        await raydiumHybridAmm.main()



if __name__ == '__main__':
    asyncio.run(testRaydiumHybridAmmMetadata())