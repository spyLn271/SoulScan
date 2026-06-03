"""
OKX exchange implementation.
Sequential fetching with rate limiting.
"""
import hmac
import hashlib
import base64
import asyncio
from datetime import datetime, timezone
from typing import List
import aiohttp

from .base import BaseExchange, CoinEntry


class OkxExchange(BaseExchange):
    """OKX coin fetcher with HMAC-SHA256 + passphrase authentication."""

    def _get_timestamp(self) -> str:
        return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    def _sign(self, timestamp: str, method: str, request_path: str) -> str:
        message = timestamp + method + request_path
        mac = hmac.new(
            self.config.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode('utf-8')

    def _get_headers(self, request_path: str) -> dict:
        timestamp = self._get_timestamp()
        signature = self._sign(timestamp, "GET", request_path)
        return {
            "OK-ACCESS-KEY": self.config.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.config.passphrase,
            "Content-Type": "application/json"
        }

    async def fetch_all_coins(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        # Step 1: Get all currencies
        request_path = "/api/v5/asset/currencies"
        headers = self._get_headers(request_path)

        async with session.get(
            self.config.base_url + request_path,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as resp:
            data = await resp.json()

        if data.get("code") != "0":
            raise Exception(f"OKX API error: {data}")

        currencies = data["data"]
        self.logger.info(f"Found {len(currencies)} currency/chain entries")

        # Build lookup: coin -> list of chains
        coin_chains = {}
        for item in currencies:
            coin = item.get("ccy", "")
            chain = item.get("chain", "")
            if coin not in coin_chains:
                coin_chains[coin] = []
            coin_chains[coin].append(chain)

        unique_coins = list(coin_chains.keys())
        total = len(unique_coins)
        self.logger.info(f"Unique coins: {total}")

        # Step 2: Fetch deposit addresses sequentially
        results = []

        for i, coin in enumerate(unique_coins, 1):
            # Continue-on-error per coin: one failing token must not abort the whole
            # OKX fetch (this previously truncated OKX to a few hundred entries).
            try:
                request_path = f"/api/v5/asset/deposit-address?ccy={coin}"
                headers = self._get_headers(request_path)

                async with session.get(
                    self.config.base_url + request_path,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as resp:
                    if resp.status == 429:
                        self.logger.warning(f"Rate limited, waiting {self.config.rate_limit_wait}s...")
                        await asyncio.sleep(self.config.rate_limit_wait)
                        headers = self._get_headers(request_path)
                        async with session.get(
                            self.config.base_url + request_path,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                        ) as retry:
                            data = await retry.json()
                    else:
                        data = await resp.json()

                if data.get("code") == "0" and data.get("data"):
                    for addr_info in data["data"]:
                        results.append(CoinEntry(
                            coin=coin,
                            network=addr_info.get("chain", ""),
                            contract_address=addr_info.get("ctAddr", "") or ""
                        ))
                    if i % 50 == 0:
                        self.logger.info(f"[{i}/{total}] processed")
                else:
                    # Fallback: use chain info without contract address
                    for chain in coin_chains.get(coin, []):
                        results.append(CoinEntry(
                            coin=coin,
                            network=chain,
                            contract_address=""
                        ))
            except Exception as e:
                self.logger.warning(f"Failed to fetch deposit address for {coin}: {e}")

            await asyncio.sleep(self.config.request_delay)

        return results
