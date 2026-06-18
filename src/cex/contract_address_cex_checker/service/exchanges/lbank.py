"""
LBank exchange implementation (cross-exchange back-fill source).

LBank's public API exposes NO on-chain contract addresses — only (assetCode, chain)
pairs. This fetcher returns those pairs as ADDRESS-LESS CoinEntry objects; the
rebuild step (Phase 2 of redis_client.rebuild_contract_index) attaches LBank's
tradable tokens to the addresses OTHER exchanges resolved, matched by (chain, coin),
gated by a witness threshold. LBank therefore never creates index keys on its own.

Sources:
- PRIMARY  `/v2/withdrawConfigs.do` — one bulk call; fields `assetCode`, `chain`.
  Deprecated ("offline soon"), so on failure/empty we fall back to:
- FALLBACK `/v2/assetConfigs.do?assetCode=X` — recommended, per-asset; fields
  `assetCode`, `chainName`. Driven by the traded-asset list from
  `/v2/currencyPairs.do` (so only assets LBank actually lists are queried).

`assetCode` is lowercase from LBank; it is upper-cased for `coin`. The chain string
(`chain`/`chainName`, e.g. "erc20", "bep20(bsc)", "base mainnet", "arbitrum one") is
passed through verbatim to `canonical.canonical_network` for mapping.
"""
import asyncio
from typing import Iterable, List, Tuple

import aiohttp

from .base import BaseExchange, CoinEntry


class LbankExchange(BaseExchange):
    """LBank fetcher — emits (coin, network) pairs with EMPTY contract addresses."""

    async def fetch_all_coins(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        entries = await self._fetch_withdraw_configs(session)
        if entries:
            self.logger.info(
                "LBank: %d (assetCode, chain) pairs from withdrawConfigs", len(entries)
            )
            return entries

        self.logger.warning(
            "LBank withdrawConfigs unavailable/empty; falling back to per-asset assetConfigs"
        )
        entries = await self._fetch_asset_configs(session)
        if entries:
            self.logger.info(
                "LBank: %d (assetCode, chain) pairs from assetConfigs fallback", len(entries)
            )
            return entries

        # Both sources empty: raise so fetch_with_retry retries and the updater keeps
        # LBank's last-good snapshot rather than blanking it (LBank always lists assets).
        raise RuntimeError("LBank produced 0 (assetCode, chain) pairs from both endpoints")

    async def _get_json(self, session: aiohttp.ClientSession, url: str):
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None)

    @staticmethod
    def _ok(payload) -> bool:
        """LBank wraps responses as {"result": "true"/true, "data": [...]}."""
        return isinstance(payload, dict) and str(payload.get("result")).lower() == "true"

    async def _fetch_withdraw_configs(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        try:
            payload = await self._get_json(
                session, f"{self.config.base_url}/v2/withdrawConfigs.do"
            )
        except Exception as e:
            self.logger.warning("LBank withdrawConfigs fetch failed: %s", e)
            return []
        if not self._ok(payload):
            return []
        return self._to_entries(
            (it.get("assetCode"), it.get("chain"))
            for it in (payload.get("data") or [])
            if isinstance(it, dict)
        )

    async def _fetch_asset_configs(self, session: aiohttp.ClientSession) -> List[CoinEntry]:
        # 1) discover the traded assets (base side of each "base_quote" pair)
        try:
            pairs_payload = await self._get_json(
                session, f"{self.config.base_url}/v2/currencyPairs.do"
            )
        except Exception as e:
            self.logger.error("LBank currencyPairs fetch failed: %s", e)
            return []
        if not self._ok(pairs_payload):
            return []
        bases = sorted({
            p.split("_", 1)[0]
            for p in (pairs_payload.get("data") or [])
            if isinstance(p, str) and "_" in p
        })

        # 2) per-asset chain config (throttled by request_delay)
        pairs: List[Tuple] = []
        for asset in bases:
            url = f"{self.config.base_url}/v2/assetConfigs.do?assetCode={asset}"
            try:
                payload = await self._get_json(session, url)
            except Exception as e:
                self.logger.debug("LBank assetConfigs(%s) failed: %s", asset, e)
                continue
            if self._ok(payload):
                for it in (payload.get("data") or []):
                    if isinstance(it, dict):
                        pairs.append((it.get("assetCode") or asset, it.get("chainName")))
            if self.config.request_delay:
                await asyncio.sleep(self.config.request_delay)
        return self._to_entries(pairs)

    @staticmethod
    def _to_entries(pairs: Iterable[Tuple]) -> List[CoinEntry]:
        """Build deduped address-less CoinEntry list from (assetCode, chain) pairs."""
        seen = set()
        out: List[CoinEntry] = []
        for asset_code, chain in pairs:
            if not asset_code or not chain:
                continue
            coin = str(asset_code).upper()
            network = str(chain)
            dedup = (coin, network.lower())
            if dedup in seen:
                continue
            seen.add(dedup)
            out.append(CoinEntry(coin=coin, network=network, contract_address=""))
        return out
