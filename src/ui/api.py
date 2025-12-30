import aiohttp
import asyncio
import redis

JUPITER_API_KEY = "5c2df4a8-f56d-447e-8354-4ed9d3368b84"

async def get_jupiter_quote(input_mint: str, output_mint: str, amount: int, swap_mode: str = "ExactIn") -> dict:
    url = "https://api.jup.ag/swap/v1/quote"
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": str(int(amount)),
        "swapMode": swap_mode,
        "slippageBps": 50,
    }
    headers = {
        "x-api-key": JUPITER_API_KEY,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "data": data}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
    except asyncio.TimeoutError:
        return {"success": False, "error": "Request timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_jupiter_quote(input_mint: str, output_mint: str, amount: int, swap_mode: str = "ExactIn") -> dict:
    return asyncio.run(get_jupiter_quote(input_mint, output_mint, amount, swap_mode))


async def search_token_async(mint: str) -> dict | None:
    url = "https://api.jup.ag/ultra/v1/search"
    params = {"query": mint}
    headers = {"x-api-key": JUPITER_API_KEY}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        token = data[0]
                        return {
                            "mint": token.get("id"),
                            "name": token.get("name"),
                            "symbol": token.get("symbol"),
                            "decimals": token.get("decimals"),
                            "icon": token.get("icon"),
                        }
    except:
        pass
    return None


def search_token_info(mint: str) -> dict | None:
    return asyncio.run(search_token_async(mint))


async def search_token_jupiter_async(mint: str, session: aiohttp.ClientSession) -> dict | None:
    """Search for a single token by mint address using Jupiter v2 search API"""
    url = "https://api.jup.ag/tokens/v2/search"
    params = {"query": mint}
    headers = {"x-api-key": JUPITER_API_KEY}

    try:
        async with session.get(url, headers=headers, params=params, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                if data and isinstance(data, list):
                    for token in data:
                        if token.get('id') == mint:
                            return token
                    if len(data) > 0:
                        return data[0]
    except Exception as e:
        pass
    return None


async def get_tokens_detailed_async(mints: list[str]) -> list:
    """Fetch detailed token stats from Jupiter tokens v2 search API with concurrent requests"""
    if not mints:
        return []

    results = []

    async with aiohttp.ClientSession() as session:
        tasks = [search_token_jupiter_async(mint, session) for mint in mints[:20]]
        results = await asyncio.gather(*tasks)

    return [r for r in results if r is not None]


def get_tokens_detailed(mints: list[str]) -> list:
    return asyncio.run(get_tokens_detailed_async(mints))
