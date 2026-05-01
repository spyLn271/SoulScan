import aiohttp
import asyncio
import time
import tenacity
from solders.pubkey import Pubkey as SolanaPubkey

####################################
from src.settings import config
from src.dex.tools.helpers.solana.helper import Helper
####################################





class Solana(Helper):
    def __init__(self, SOLANA_RPC_ENDPOINT=config.SOLANA_RPC_ENDPOINT, logger=None):
        super().__init__()
        self.logger = logger if logger else self.logger

        self.SOLANA_RPC_ENDPOINT = SOLANA_RPC_ENDPOINT
        self.session: aiohttp.ClientSession
        self._is_session_open = False

    async def __aenter__(self):
        if not self._is_session_open:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            self._is_session_open = True
            self.logger.info("Solana session opened.")
        else:
            self.logger.warning("Solana session already open.")
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._is_session_open:
            await self.session.close()
            self.logger.info("Solana session closed.")
        else:
            self.logger.warning("Solana session already closed.")

    @tenacity.retry(wait=tenacity.wait_fixed(1), stop=tenacity.stop_after_attempt(3))
    async def RPC_call(self, method: str, address: str | list, commitment: dict = None) -> dict:
        if not commitment:
            commitment = {"encoding": "base64"}

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": [
                address,
                commitment
            ]
        }

        try:
            async with self.session.post(self.SOLANA_RPC_ENDPOINT, json=payload, timeout=20) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            self.logger.error(f"Error calling RPC method {method} for address {address}: {e}")
            raise e

    async def getMultipleAccounts(self, addresses: list,
                                  field: list = None, funcs: dict = None) -> dict[str, list[dict]]:
        return_data = {}
        chunk_index = 0
        funcs = {} if funcs is None else funcs
        field = 'all' if field is None else field
        funcs.update({'default': lambda x: x})

        address_chunks = self._get_address_chunk(addresses)
        self.logger.info(f"Calling RPC for {len(addresses)} addresses in {len(address_chunks)} chunks.")

        tasks = [self.RPC_call("getMultipleAccounts", chunk) for chunk in address_chunks]

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        self.logger.info(f"RPC call took {time.time() - start_time} seconds.")

        start_time = time.time()
        for result in results:
            original_chunk = address_chunks[chunk_index]

            if isinstance(result, Exception):
                self.logger.error(f"RPC chunk failed: {result}. Marking {len(original_chunk)} addresses as failed.")
            else:
                values = result.get('result', {}).get('value', []) if isinstance(result, dict) else []

                for i, value in enumerate(values):
                    try:
                        address = original_chunk[i]

                        if isinstance(field, list):
                            processed_fields = {}
                            for field_name in field:
                                func = funcs.get(field_name, funcs['default'])
                                raw_field_data = func(value.get(field_name)) if isinstance(value, dict) else None
                                processed_fields[field_name] = raw_field_data
                            return_data.setdefault(address, []).append(processed_fields)
                        else:
                            return_data.setdefault(address, []).append(value)
                    except Exception as e:
                        self.logger.error(f"Error processing address {original_chunk[i]}: {e}")
                        continue

            chunk_index += 1
        self.logger.info(f"Data processing took {time.time() - start_time} seconds.")

        return return_data

    async def getMultipleSPLAccountsBalance(self, addresses: list) -> dict:
        field = ['data', 'lamports']
        funcs = {'data': lambda x: self.translater.translate(x[0], market='oracle', name='SPLWallet')}
        return await self.getMultipleAccounts(addresses, field, funcs)

    async def getMultiplePDAs(self, seeds: list, program_id: list | SolanaPubkey,
                              type_name: str, market: str, funcs: callable = None) -> dict:
        return_data: dict
        if isinstance(program_id, list) and len(program_id) != len(seeds):
            raise Exception("program_id and seeds must have the same length.")

        PDAs = self.findPDAs(seeds, program_id)
        field = ['data']
        funcs = {'data': lambda x: self.translater.translate(
            data=x[0],
            name=type_name,
            market=market
        )} if funcs is None else funcs

        return_data = await self.getMultipleAccounts(PDAs, field, funcs)

        return return_data

    async def getMultipleMintAccounts(self, addresses: list) -> dict:
        field = ['data']
        funcs = {'data': lambda x: self.translater.translate(x[0], market='ammV2', name='MintAccount')}
        return await self.getMultipleAccounts(addresses, field, funcs)
