"""
Canonicalization for the CEX contract-address resolver.

The resolver builds `cex:contract_index` keyed as ``{network}:{address}`` so that
the same token on the same chain collapses to ONE key across all exchanges, while
chain-native assets (which CEXes report with an empty contract address) and their
wrapped forms map to a single canonical address per chain.

Two normalizations live here:

1. NETWORK NAME → canonical network.
   Every exchange names networks differently (eth = "ETH"/"ERC20"/"ARBEVM"...,
   solana = "SOL"/"SOLANA"...). For the 5 networks SoulScan supports
   (eth, base, arbitrum, bsc, solana) we map the per-exchange aliases to the
   canonical SoulScan name. Networks OUTSIDE that set are KEPT (not dropped) and
   keyed by a slugified version of the exchange's raw network string, so coverage
   is never lost — see ``canonical_network()``.

2. NATIVE / WRAPPED address.
   EVM: native asset and its wrapped token both resolve to the chain's canonical
   native address ``0x0000…0000`` (per-chain, so ETH-on-eth and BNB-on-bsc do NOT
   collide — the key is ``eth:0x0…`` vs ``bsc:0x0…``).
   Solana: native SOL (empty address from CEXes) resolves to the Wrapped-SOL mint
   ``So111…112``.

EVM_NATIVE_TOKEN_ADDRESSES below is COPIED from src/settings/config.py on purpose
(NOT imported): importing config.py instantiates Config() which hard-requires the
DEX env vars, and the lean cex branch must stay DEX-env-independent. If you change
the table in one place, change it in the other.
"""
import re
from typing import Dict, Optional

# SoulScan-supported networks: Network = Literal["eth","base","arbitrum","bsc","solana"]
SUPPORTED_NETWORKS = ("eth", "base", "arbitrum", "bsc", "solana")

# Wrapped-SOL mint — the canonical address for native SOL on Solana.
WSOL_MINT = "So11111111111111111111111111111111111111112"
# EVM canonical native sentinel.
EVM_NATIVE_ADDRESS = "0x0000000000000000000000000000000000000000"

# --- COPIED from src/settings/config.py (keep in sync; do NOT import it) ---
EVM_NATIVE_TOKEN_ADDRESSES = {
    "eth": {
        "symbol": "ETH",
        "address": "0x0000000000000000000000000000000000000000",
        "alias": ["WETH"],
        "alias_addresses": ["0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"],
    },
    "arbitrum": {
        "symbol": "ETH",
        "address": "0x0000000000000000000000000000000000000000",
        "alias": ["WETH"],
        "alias_addresses": ["0x82af49447d8a07e3bd95bd0d56f35241523fbab1"],
    },
    "base": {
        "symbol": "ETH",
        "address": "0x0000000000000000000000000000000000000000",
        "alias": ["WETH"],
        "alias_addresses": ["0x4200000000000000000000000000000000000006"],
    },
    "bsc": {
        "symbol": "BNB",
        "address": "0x0000000000000000000000000000000000000000",
        "alias": ["WBNB"],
        "alias_addresses": ["0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"],
    },
}

# Per-exchange / common network-name aliases -> canonical SoulScan network.
# Built from the live network vocabularies observed in cex:data:* (binance,
# gateio, bingx, bitget, coinex, htx, kucoin, okx). All keys are matched
# case-insensitively (see canonical_network()).
_NETWORK_ALIASES: Dict[str, str] = {
    # ----- ethereum mainnet -----
    "eth": "eth", "ethereum": "eth", "erc20": "eth", "eth-erc20": "eth",
    # ----- bsc -----
    "bsc": "bsc", "bep20": "bsc", "bnb": "bsc", "binance-smart-chain": "bsc",
    "bnb smart chain": "bsc", "bep20(bsc)": "bsc",  # lbank chain string
    "bsc_bnb": "bsc",  # bitmart
    # ----- base -----
    "base": "base", "baseevm": "base", "base-base": "base",
    "base mainnet": "base",  # lbank chain string (NOT "base goerli"/testnets)
    "base-eth": "base",  # bitmart (Base chain)
    # ----- arbitrum (one) -----
    "arbitrum": "arbitrum", "arbevm": "arbitrum", "arbitrumone": "arbitrum",
    "arbitrum one": "arbitrum", "arb": "arbitrum", "arbitrum-arbitrum one": "arbitrum",
    "arbi": "arbitrum",  # bitmart / bybit (Arbitrum One; NOT Arbitrum Nova)
    # ----- solana -----
    "sol": "solana", "solana": "solana", "sol-solana": "solana",
}

# Wrapped-token address -> canonical EVM network (so a wrapped address resolves
# to that chain's native key). Lowercased.
_WRAPPED_ADDR_TO_NET: Dict[str, str] = {}
for _net, _info in EVM_NATIVE_TOKEN_ADDRESSES.items():
    for _wa in _info.get("alias_addresses", []):
        _WRAPPED_ADDR_TO_NET[_wa.lower()] = _net


def _slug(s: str) -> str:
    """Slugify an arbitrary network string for use as a key segment: lowercase,
    spaces/() stripped to single tokens. Keeps it stable and collision-resistant
    enough for the long tail of unsupported networks."""
    return "".join(ch for ch in s.lower().strip() if ch.isalnum() or ch in ("-", "_", ".")) or "unknown"


def canonical_network(raw_network: str) -> str:
    """Map an exchange's raw network string to a canonical key segment.

    Returns one of SUPPORTED_NETWORKS for recognized chains; otherwise returns a
    slug of the raw string (prefixed ``x-``) so unsupported networks are still
    saved and self-describing. Never returns empty.
    """
    if not raw_network:
        return "x-unknown"
    key = raw_network.strip().lower()
    if key in _NETWORK_ALIASES:
        return _NETWORK_ALIASES[key]
    # Verbose "Name(TOKEN)" forms (e.g. mexc 'Ethereum(ERC20)', 'BNB Smart Chain(BEP20)',
    # 'Solana(SOL)', 'Arbitrum One(ARB)'): try the outer name and the inner token against
    # the alias table. Only known alias keys match, so 'Polygon(MATIC)'/'Tron(TRC20)' stay x-*.
    if "(" in key and key.endswith(")"):
        outer = key[:key.index("(")].strip()
        inner = key[key.index("(") + 1:-1].strip()
        if outer in _NETWORK_ALIASES:
            return _NETWORK_ALIASES[outer]
        if inner in _NETWORK_ALIASES:
            return _NETWORK_ALIASES[inner]
    return f"x-{_slug(raw_network)}"


def is_supported_network(canonical: str) -> bool:
    return canonical in SUPPORTED_NETWORKS


def _normalize_evm_address(addr: str) -> str:
    """Lowercase a 42-char 0x EVM address; return others unchanged.

    Case-insensitive on the `0x` prefix — some exchanges return `0X…` and the
    address may arrive upper/mixed case; all must collapse to one canonical form."""
    if len(addr) == 42 and addr[:2].lower() == "0x":
        return addr.lower()
    return addr


# Address-format validation. Some exchanges return malformed/truncated addresses
# (notably OKX, whose deposit-address `ctAddr` is masked to the last 6 chars of the
# real address). Such stubs must NOT become index keys: the engine queries the REAL
# address and would never find them, and the junk key also pollutes price-matching.
_EVM_ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
# base58 (Bitcoin alphabet — no 0/O/I/l); Solana mints are ~32-44 chars.
_B58_ALPHABET = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")


def _is_valid_evm_address(addr: str) -> bool:
    """True iff addr is a well-formed 42-char 0x-prefixed hex EVM address."""
    return bool(_EVM_ADDR_RE.match(addr))


def _is_valid_solana_address(addr: str) -> bool:
    """True iff addr looks like a base58 Solana mint (32-44 base58 chars)."""
    return 32 <= len(addr) <= 44 and all(c in _B58_ALPHABET for c in addr)


def canonical_address(canonical_net: str, raw_address: str, coin: str = "") -> Optional[str]:
    """Resolve the canonical address for an (network, address[, coin]) triple.

    - Solana: empty address + native SOL coin -> WSOL mint; WSOL mint stays itself.
    - EVM supported chains: empty address (native) OR a known wrapped-token address
      -> that chain's native sentinel 0x0000…0000; other addresses lowercased.
    - Unsupported networks: empty address -> None (nothing to key on); otherwise
      the address verbatim (EVM-lowercased if it looks like one).

    Returns None when there is no usable address (caller should skip the entry).
    """
    addr = (raw_address or "").strip()

    if canonical_net == "solana":
        if not addr:
            # native SOL (and only native) -> WSOL mint
            return WSOL_MINT if coin.upper() in ("SOL", "WSOL") else None
        if not _is_valid_solana_address(addr):
            return None  # malformed/truncated mint (e.g. OKX 6-char stub) -> drop
        return addr  # SPL mint, case-sensitive — keep as-is

    if canonical_net in EVM_NATIVE_TOKEN_ADDRESSES:  # eth/base/arbitrum/bsc
        if not addr:
            # Native (ETH/BNB) or its wrapped alias with no address -> native sentinel.
            # Any OTHER address-less token can't be keyed and must NOT collapse onto the
            # native 0x0 key (that pollutes it) -> drop. Mirrors the Solana guard above.
            return EVM_NATIVE_ADDRESS if coin.upper() in native_symbols(canonical_net) else None
        low = _normalize_evm_address(addr)
        if not _is_valid_evm_address(low):
            return None  # malformed/truncated address (e.g. OKX 6-char stub) -> drop
        if low in _WRAPPED_ADDR_TO_NET and _WRAPPED_ADDR_TO_NET[low] == canonical_net:
            return EVM_NATIVE_ADDRESS  # wrapped form collapses to native
        return low

    # unsupported / non-EVM-non-Solana network
    if not addr:
        return None
    return _normalize_evm_address(addr)


# Some exchanges (verified: only htx) report chain-native assets with a BLANK
# network AND empty address. Map the SoulScan-native coins to their home chain so
# they aren't lost. Non-SoulScan natives (BTC/XRP/ADA/...) are kept under an
# ``x-<coin>`` key with a ``native`` sentinel address instead of being dropped.
NATIVE_COIN_HOME_CHAIN = {"ETH": "eth", "BNB": "bsc", "SOL": "solana"}


def _strip_coin_prefix(network: str, coin: str) -> str:
    """Some exchanges encode the chain as ``{COIN}-{CHAIN}`` / ``{COIN}_{CHAIN}`` (OKX:
    'AXS-ERC20', 'ANIME-Arbitrum One'; coinex: 'AAVE_BSC'). Strip a leading coin prefix so
    the chain part can be canonicalized. Returns the chain part, or the original network if
    it doesn't start with the coin."""
    if not network or not coin:
        return network
    cu, nu = coin.upper(), network.upper()
    for sep in ("-", "_"):
        pref = cu + sep
        if nu.startswith(pref) and len(network) > len(pref):
            return network[len(pref):]
    return network


def resolve_entry(raw_network: str, raw_address: str, coin: str):
    """Resolve a raw exchange (network, address, coin) entry to a canonical
    ``(network, address)`` pair for the index, or None to skip.

    Handles the blank-network native case: when the exchange gives no network and
    no address (so it's the base-chain asset), the coin determines the chain —
    ETH/BNB/SOL map to eth/bsc/solana; any other such native is kept under
    ``x-<coin>`` with a ``native`` address sentinel.
    """
    net = canonical_network(raw_network)
    # Full string wasn't a known chain — some exchanges prefix the chain with the coin
    # ('AXS-ERC20', 'AAVE_BSC'). Strip the coin and retry (full string tried first so an
    # explicit alias like 'BASE-ETH'->base wins over stripping to 'ETH').
    if net.startswith("x-"):
        stripped = _strip_coin_prefix(raw_network, coin)
        if stripped != raw_network:
            net = canonical_network(stripped)
    addr = (raw_address or "").strip()

    # Blank network (-> x-unknown) with no address: treat the coin as a native.
    if net == "x-unknown" and not addr and coin:
        home = NATIVE_COIN_HOME_CHAIN.get(coin.upper())
        if home:
            net = home  # falls through to canonical_address -> chain native sentinel
        else:
            return (f"x-{_slug(coin)}", "native")  # non-SoulScan native, kept

    ca = canonical_address(net, addr, coin)
    if not ca:
        return None
    return (net, ca)


def make_index_key(canonical_net: str, canonical_addr: str) -> str:
    """The cex:contract_index hash field: ``{network}:{address}``."""
    return f"{canonical_net}:{canonical_addr}"


def native_symbols(canonical_net: str) -> set:
    """Wallet-coin symbols (native + wrapped) that denote a chain's NATIVE asset.

    Used by the back-fill witness map: a chain's native key (``{net}:0x000…0`` or
    ``solana:<WSOL mint>``) is registered under all of these so a back-fill source
    that names the native ``SOL`` still matches when the only native producer filed
    it as wallet-coin ``WSOL`` (native wallet-coin naming is the least consistent
    field across CEXes). Returns an empty set for non-native-bearing networks.
    """
    if canonical_net == "solana":
        return {"SOL", "WSOL"}
    info = EVM_NATIVE_TOKEN_ADDRESSES.get(canonical_net)
    if not info:
        return set()
    syms = {info["symbol"].upper()}
    syms.update(a.upper() for a in info.get("alias", []))
    return syms


# Quote assets the orderbook side trades against (must match producer/config.py
# ACCEPTABLE_QUOTE_ASSETS). Kept local so the checker stays import-light.
QUOTE_ASSETS = ("USDT", "USDC")


def resolve_tradable_base(market_symbols: set, coin: str) -> Optional[str]:
    """Return the tradable BASE symbol for ``coin`` on an exchange, or None.

    ``market_symbols`` is the set of that exchange's tradable symbols (the FIELD
    names of its ``spot-market-data:{exchange}`` hash). A coin is tradable iff
    ``{coin}{quote}`` exists for some accepted quote.

    Case-insensitive: some exchanges store market-data symbols lowercase (htx) while
    the order-book streams are uppercase; we match case-insensitively and always
    return the canonical UPPERCASE base, which is what the order-book stream keys use
    (``stream:orderbook:{ex}:spot:{BASE}{QUOTE}``).

    Why a plain set (not Redis here): keeps this helper pure/testable; the caller
    loads the hash keys once per exchange and passes the set in.
    """
    if not coin:
        return None
    c = coin.upper()
    upper_symbols = {s.upper() for s in market_symbols}
    for q in QUOTE_ASSETS:
        if f"{c}{q}" in upper_symbols:
            return c
    return None


def split_stream_symbol(suffix: str):
    """Split an order-book stream suffix ``{BASE}{QUOTE}`` into ``(BASE, QUOTE)`` by
    stripping a trailing accepted quote (``ETHUSDT`` -> ``("ETH","USDT")``). Returns
    ``(suffix.upper(), "")`` if it doesn't end in a known quote — used by the price-match
    layer to enumerate a producer's tradable bases from its stream keys."""
    s = suffix.upper()
    for q in QUOTE_ASSETS:
        if s.endswith(q) and len(s) > len(q):
            return s[:-len(q)], q
    return s, ""
