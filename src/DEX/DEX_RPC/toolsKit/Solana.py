import aiohttp
import asyncio
import time
import tenacity

####################################
from src.Config import config
from src.DEX.DEX_RPC.toolsKit.helper import Helper
####################################





class Solana(Helper):
    def __init__(self, SOLANA_RPC_ENDPOINT=config.SOLANA_RPC_ENDPOINT):
        super().__init__()

        self.SOLANA_RPC_ENDPOINT = SOLANA_RPC_ENDPOINT
        self.session: aiohttp.ClientSession
        self._is_session_open = False

    async def __aenter__(self):
        if not self._is_session_open:
            self.session = aiohttp.ClientSession()
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
    async def RPC_call(self, method: str, address: str | list, commitment: dict = None) -> bytes | None:
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

        async with self.session.post(self.SOLANA_RPC_ENDPOINT, json=payload, timeout=20) as response:
            response.raise_for_status()
            return await response.json()

    async def getMultipleAccounts(self, addresses: list, field: list = None, funcs: dict = None) -> dict:
        return_data = {}
        chunk_index = 0
        funcs = {} if funcs is None else funcs
        field = 'all' if field is None else field
        funcs.update({'default': lambda x: x})

        address_chunks = self._get_address_chunk(addresses)

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
                    address = original_chunk[i]
                    return_data[address] = {}

                    if isinstance(field, list):
                        for field_name in field:
                            func = funcs.get(field_name, funcs['default'])
                            return_data[address][field_name] = func(
                                value.get(field_name) if isinstance(value, dict) else None)
                    else:
                        return_data[address] = value

            chunk_index += 1
        self.logger.info(f"Data processing took {time.time() - start_time} seconds.")

        return return_data

    async def getMultipleSPLAccountsBalance(self, addresses: list) -> dict:
        field = ['data', 'lamports']
        funcs = {'data': lambda x: self.translateSPLWallet(x[0])}
        return await self.getMultipleAccounts(addresses, field, funcs)