import streamlit as st
from streamlit_option_menu import option_menu
import redis
import aiohttp
import asyncio
from src.SoulEngine.SmartRouter import SmartRouter
from src.SoulEngine.SoulHelper import get_active_metadata, get_active_state, get_all_DEX_active_tokens, \
    get_all_common_dict_of_tokens

st.set_page_config(page_title="SoulScan", layout="wide", page_icon="👻")

COMMON_TOKENS = {
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "SOL (Wrapped)": "So11111111111111111111111111111111111111112",
}

TOKEN_DECIMALS = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": 6,
    "So11111111111111111111111111111111111111112": 9,
}

r = redis.Redis(decode_responses=True)

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


TOKEN_INFO = {
    "USDC": {
        "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "icon": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v/logo.png",
        "decimals": 6
    },
    "SOL": {
        "mint": "So11111111111111111111111111111111111111112",
        "icon": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png",
        "decimals": 9
    },
}


def token_display(token_name):
    """Display token with icon and name inline"""
    if token_name in TOKEN_INFO:
        icon_url = TOKEN_INFO[token_name]["icon"]
        return f'<img src="{icon_url}" width="24" style="vertical-align:middle; margin-right:8px;"/><span style="font-size:20px; font-weight:bold;">{token_name}</span>'
    return token_name


st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    [data-testid="stSidebar"] {
        border-radius: 0 20px 20px 0;
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
        border-right: 1px solid rgba(79, 70, 229, 0.3);
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0;
    }
    [data-testid="stSidebar"] .css-1d391kg,
    [data-testid="stSidebar"] .st-emotion-cache-1gwvy71,
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
    .sidebar-brand {
        padding: 1.5rem 1rem;
        text-align: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 1rem;
    }
    .sidebar-brand h1 {
        color: #fff;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }
    .sidebar-brand .ghost-icon {
        font-size: 2rem;
        animation: float 3s ease-in-out infinite;
    }
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">
            <h1>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 8px;">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="#a78bfa"/>
                </svg>
                SoulScan
            </h1>
        </div>
    """, unsafe_allow_html=True)

    page = option_menu(
        menu_title=None,
        options=["Swap", "Tokens"],
        icons=["arrow-left-right", "coin"],
        default_index=0,
        orientation="vertical",
        styles={
            "container": {
                "padding": "0.5rem",
                "background-color": "transparent",
            },
            "icon": {
                "color": "#a78bfa",
                "font-size": "20px",
            },
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "0.25rem 0",
                "padding": "0.75rem 1rem",
                "border-radius": "10px",
                "color": "rgba(255, 255, 255, 0.8)",
                "background-color": "transparent",
                "--hover-color": "rgba(167, 139, 250, 0.1)",
            },
            "nav-link-selected": {
                "background": "linear-gradient(90deg, rgba(79, 70, 229, 0.8) 0%, rgba(139, 92, 246, 0.6) 100%)",
                "color": "#ffffff",
                "font-weight": "600",
                "box-shadow": "0 4px 15px rgba(79, 70, 229, 0.4)",
            },
            "menu-title": {
                "display": "none",
            }
        }
    )

    st.markdown("<div style='height: 200px;'></div>", unsafe_allow_html=True)

    st.markdown("""
        <div style="text-align: center; padding: 1rem; border-top: 1px solid rgba(255,255,255,0.1);">
            <p style="color: rgba(255,255,255,0.4); font-size: 0.8rem; margin: 0;">
                Powered by SoulEngine
            </p>
            <p style="color: rgba(255,255,255,0.3); font-size: 0.7rem; margin: 0.25rem 0 0 0;">
                v1.0.0
            </p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0f0f1a 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        color: #ffffff !important;
    }
    h1 { font-size: 2.5rem !important; }
    h2 { font-size: 2rem !important; }
    h3 {
        font-size: 1.5rem !important;
        background: linear-gradient(90deg, #a78bfa 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    p, span, label, div {
        color: rgba(255, 255, 255, 0.9);
    }

    [data-testid="stVerticalBlock"] > div:has(> [data-testid="stContainer"]) {
        background: transparent;
    }
    div[data-testid="stContainer"] {
        background: linear-gradient(145deg, rgba(26, 26, 46, 0.9) 0%, rgba(22, 33, 62, 0.9) 100%);
        border: 1px solid rgba(167, 139, 250, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    [data-testid="stExpander"] {
        background: linear-gradient(145deg, rgba(15, 15, 26, 0.95) 0%, rgba(22, 33, 62, 0.95) 100%) !important;
        border: 1px solid rgba(167, 139, 250, 0.2) !important;
        border-radius: 12px !important;
        overflow: hidden;
    }
    [data-testid="stExpander"] > div:first-child {
        background: transparent !important;
        border: none !important;
    }
    [data-testid="stExpander"] summary {
        color: #a78bfa !important;
        font-weight: 600 !important;
        padding: 1rem !important;
    }
    [data-testid="stExpander"] summary:hover {
        color: #c4b5fd !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        background: rgba(10, 10, 15, 0.8) !important;
        padding: 1rem !important;
        border-top: 1px solid rgba(167, 139, 250, 0.1) !important;
    }

    pre {
        background: rgba(10, 10, 15, 0.9) !important;
        border: 1px solid rgba(167, 139, 250, 0.15) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        color: #e2e8f0 !important;
        font-size: 0.85rem !important;
        overflow-x: auto !important;
    }
    [data-testid="stJson"] {
        background: transparent !important;
    }
    [data-testid="stJson"] > div {
        background: rgba(10, 10, 15, 0.9) !important;
        border: 1px solid rgba(167, 139, 250, 0.15) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }

    .stButton > button[kind="primary"],
    button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4) !important;
    }
    .stButton > button[kind="primary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.6) !important;
    }
    .stButton > button[kind="secondary"],
    button[data-testid="stBaseButton-secondary"] {
        background: rgba(167, 139, 250, 0.1) !important;
        color: #a78bfa !important;
        border: 1px solid rgba(167, 139, 250, 0.3) !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button[kind="secondary"]:hover,
    button[data-testid="stBaseButton-secondary"]:hover {
        background: rgba(167, 139, 250, 0.2) !important;
        border-color: rgba(167, 139, 250, 0.5) !important;
    }
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: rgba(15, 15, 26, 0.8) !important;
        border: 1px solid rgba(167, 139, 250, 0.2) !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        font-size: 1.1rem !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.3s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #a78bfa !important;
        box-shadow: 0 0 0 2px rgba(167, 139, 250, 0.2) !important;
    }
    div[data-testid="stNumberInput"] input {
        font-size: 1.75rem !important;
        font-weight: 600 !important;
        background: transparent !important;
        border: none !important;
        color: #ffffff !important;
    }
    .stSelectbox > div > div {
        background: rgba(15, 15, 26, 0.8) !important;
        border: 1px solid rgba(167, 139, 250, 0.2) !important;
        border-radius: 10px !important;
    }
    .stSelectbox > div > div:hover {
        border-color: rgba(167, 139, 250, 0.4) !important;
    }
    .stRadio > div {
        background: rgba(15, 15, 26, 0.5);
        border-radius: 10px;
        padding: 0.5rem;
    }
    .stRadio > div > label {
        color: rgba(255, 255, 255, 0.8) !important;
    }

    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(26, 26, 46, 0.6) 0%, rgba(22, 33, 62, 0.6) 100%);
        border: 1px solid rgba(167, 139, 250, 0.15);
        border-radius: 12px;
        padding: 1rem;
    }
    [data-testid="stMetricLabel"] {
        color: rgba(255, 255, 255, 0.6) !important;
        font-size: 0.9rem !important;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricDelta"] svg {
        display: none;
    }

    .stSuccess {
        background: linear-gradient(90deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.05) 100%) !important;
        border-left: 4px solid #10b981 !important;
        border-radius: 8px !important;
    }
    .stError {
        background: linear-gradient(90deg, rgba(239, 68, 68, 0.15) 0%, rgba(239, 68, 68, 0.05) 100%) !important;
        border-left: 4px solid #ef4444 !important;
        border-radius: 8px !important;
    }
    .stWarning {
        background: linear-gradient(90deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%) !important;
        border-left: 4px solid #f59e0b !important;
        border-radius: 8px !important;
    }
    .stInfo {
        background: linear-gradient(90deg, rgba(59, 130, 246, 0.15) 0%, rgba(59, 130, 246, 0.05) 100%) !important;
        border-left: 4px solid #3b82f6 !important;
        border-radius: 8px !important;
    }

    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent 0%, rgba(167, 139, 250, 0.3) 50%, transparent 100%) !important;
        margin: 1.5rem 0 !important;
    }

    code {
        background: rgba(15, 15, 26, 0.8) !important;
        border: 1px solid rgba(167, 139, 250, 0.2) !important;
        border-radius: 6px !important;
        padding: 0.25rem 0.5rem !important;
        color: #a78bfa !important;
        font-size: 0.85rem !important;
    }

    .stSpinner > div {
        border-top-color: #a78bfa !important;
    }

    .token-row {
        background: rgba(26, 26, 46, 0.4);
        border-radius: 10px;
        padding: 0.75rem;
        margin: 0.25rem 0;
        transition: all 0.2s ease;
    }
    .token-row:hover {
        background: rgba(167, 139, 250, 0.1);
        transform: translateX(4px);
    }

    .swap-card {
        background: linear-gradient(145deg, rgba(26, 26, 46, 0.95) 0%, rgba(22, 33, 62, 0.95) 100%);
        border-radius: 24px;
        padding: 2rem;
        border: 1px solid rgba(167, 139, 250, 0.2);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    }
    .token-box {
        background: rgba(15, 15, 26, 0.6);
        border-radius: 16px;
        padding: 1.25rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(167, 139, 250, 0.1);
        transition: all 0.3s ease;
    }
    .token-box:hover {
        border-color: rgba(167, 139, 250, 0.3);
        background: rgba(15, 15, 26, 0.8);
    }
    .swap-label {
        color: rgba(255, 255, 255, 0.5);
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .token-display {
        font-size: 1.75rem;
        font-weight: 700;
        color: #ffffff;
    }

    .stCaption, [data-testid="stCaptionContainer"] {
        color: rgba(255, 255, 255, 0.5) !important;
    }

    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(15, 15, 26, 0.5);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(167, 139, 250, 0.3);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(167, 139, 250, 0.5);
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    .animate-fade-in {
        animation: fadeIn 0.5s ease-out;
    }
</style>
""", unsafe_allow_html=True)

if "a_to_b" not in st.session_state:
    st.session_state.a_to_b = True
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_result_token" not in st.session_state:
    st.session_state.last_result_token = None
if "show_results" not in st.session_state:
    st.session_state.show_results = False
if "cached_results" not in st.session_state:
    st.session_state.cached_results = None
if "custom_sell_token" not in st.session_state:
    st.session_state.custom_sell_token = None
if "custom_buy_token" not in st.session_state:
    st.session_state.custom_buy_token = None


def toggle_swap_direction():
    st.session_state.a_to_b = not st.session_state.a_to_b
    st.session_state.last_result = None
    st.session_state.show_results = False
    st.session_state.cached_results = None
    st.session_state.custom_sell_token = None
    st.session_state.custom_buy_token = None


if page == "Tokens":
    st.markdown("### Active Tokens")

    token_filter = st.radio(
        "Filter Tokens",
        ["All DEX Active Tokens", "Common Tokens (CEX Listed)"],
        horizontal=True
    )

    if "tokens_page" not in st.session_state:
        st.session_state.tokens_page = 1

    try:
        with st.spinner("Loading tokens from pools..."):
            if token_filter == "All DEX Active Tokens":
                tokens = get_all_DEX_active_tokens(r)
                st.info(f"Found **{len(tokens)}** active tokens from DEX pools")
            else:
                tokens = get_all_common_dict_of_tokens(r)
                st.info(f"Found **{len(tokens)}** common tokens (listed on CEX)")

        if tokens:
            search = st.text_input("Search by symbol or mint address", placeholder="e.g. SOL or So11111...")

            if search:
                filtered_tokens = {
                    mint: data for mint, data in tokens.items()
                    if search.lower() in data.get('symbol', '').lower() or search.lower() in mint.lower()
                }
            else:
                filtered_tokens = tokens

            sorted_mints = sorted(filtered_tokens.keys(), key=lambda m: filtered_tokens[m].get('symbol', '').upper())

            tokens_per_page = 20
            total_tokens = len(sorted_mints)
            total_pages = max(1, (total_tokens + tokens_per_page - 1) // tokens_per_page)

            if st.session_state.tokens_page > total_pages:
                st.session_state.tokens_page = 1


            start_idx = (st.session_state.tokens_page - 1) * tokens_per_page
            end_idx = start_idx + tokens_per_page
            page_mints = sorted_mints[start_idx:end_idx]

            detailed_lookup = {}
            with st.spinner("Fetching token details..."):
                detailed_tokens = get_tokens_detailed(page_mints)
                if detailed_tokens:
                    for t in detailed_tokens:
                        if t and isinstance(t, dict) and t.get('id'):
                            detailed_lookup[t['id']] = t

            st.markdown("---")
            header_cols = st.columns([1, 2, 2, 2, 2, 3])
            with header_cols[0]:
                st.markdown("**#**")
            with header_cols[1]:
                st.markdown("**Token**")
            with header_cols[2]:
                st.markdown("**Price**")
            with header_cols[3]:
                st.markdown("**24h Change**")
            with header_cols[4]:
                st.markdown("**TVL / Volume 24h**")
            with header_cols[5]:
                st.markdown("**Mint Address**")
            st.markdown("---")

            for idx, mint in enumerate(page_mints):
                base_data = filtered_tokens[mint]
                detail = detailed_lookup.get(mint, {})

                row_cols = st.columns([1, 2, 2, 2, 2, 3])

                with row_cols[0]:
                    row_num = start_idx + idx + 1
                    icon_url = detail.get('icon', '')
                    if icon_url:
                        st.image(icon_url, width=32)
                    else:
                        st.markdown(f"**{row_num}**")

                with row_cols[1]:
                    name = detail.get('name', base_data.get('symbol', 'Unknown'))
                    symbol = detail.get('symbol', base_data.get('symbol', '???'))
                    decimals = detail.get('decimals', base_data.get('decimals', '?'))

                    is_verified = detail.get('isVerified', False)
                    if is_verified:
                        verified_badge = """
                            <span style='color: #1d9bf0; font-size: 1.2em; margin-left: 4px; vertical-align: text-bottom;'>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.6.154-.435.238-.905.238-1.4 0-2.21-1.71-3.998-3.818-3.998-.47 0-.92.084-1.336.25C14.818 2.415 13.51 1.5 12 1.5s-2.816.917-3.437 2.25c-.415-.165-.866-.25-1.336-.25-2.11 0-3.818 1.79-3.818 4 0 .495.083.965.238 1.4-1.272.65-2.147 2.018-2.147 3.6 0 1.495.782 2.798 1.942 3.486-.02.17-.032.34-.032.514 0 2.21 1.708 4 3.818 4 .47 0 .92-.086 1.335-.25.62 1.334 1.926 2.25 3.437 2.25 1.512 0 2.818-.916 3.437-2.25.415.163.865.248 1.336.248 2.11 0 3.818-1.79 3.818-4 0-.174-.012-.344-.033-.513 1.158-.687 1.943-1.99 1.943-3.484zm-6.616-3.334l-4.334 6.5c-.145.217-.382.334-.625.334-.143 0-.288-.04-.416-.126l-.115-.094-2.415-2.415c-.293-.293-.293-.768 0-1.06s.768-.294 1.06 0l1.77 1.767 3.825-5.74c.23-.345.696-.436 1.04-.207.346.23.44.696.21 1.04z" />
                                </svg>
                            </span>
                        """
                    else:
                        verified_badge = ""

                    st.markdown(f"**{symbol}**{verified_badge}", unsafe_allow_html=True)
                    st.caption(f"{name[:20]}{'...' if len(name) > 20 else ''}")

                with row_cols[2]:
                    usd_price = detail.get('usdPrice', 0)
                    if usd_price:
                        if usd_price >= 1:
                            st.markdown(f"**${usd_price:,.2f}**")
                        elif usd_price >= 0.0001:
                            st.markdown(f"**${usd_price:.6f}**")
                        else:
                            st.markdown(f"**${usd_price:.10f}**")
                    else:
                        st.markdown("—")

                with row_cols[3]:
                    stats_24h = detail.get('stats24h', {})
                    price_change = stats_24h.get('priceChange', 0)
                    if price_change:
                        if price_change >= 0:
                            st.markdown(f":green[↑ **+{price_change:.2f}%**]")
                        else:
                            st.markdown(f":red[↓ **{price_change:.2f}%**]")
                    else:
                        st.markdown("—")

                with row_cols[4]:
                    liquidity = detail.get('liquidity', 0)
                    volume_24h = 0
                    if stats_24h:
                        volume_24h = stats_24h.get('buyVolume', 0) + stats_24h.get('sellVolume', 0)

                    tvl_str = "—"
                    vol_str = "—"

                    if liquidity:
                        if liquidity >= 1_000_000:
                            tvl_str = f"${liquidity / 1_000_000:.2f}M"
                        elif liquidity >= 1_000:
                            tvl_str = f"${liquidity / 1_000:.1f}K"
                        else:
                            tvl_str = f"${liquidity:.0f}"

                    if volume_24h:
                        if volume_24h >= 1_000_000:
                            vol_str = f"${volume_24h / 1_000_000:.2f}M"
                        elif volume_24h >= 1_000:
                            vol_str = f"${volume_24h / 1_000:.1f}K"
                        else:
                            vol_str = f"${volume_24h:.0f}"

                    st.markdown(f"TVL: {tvl_str}")
                    st.caption(f"Vol: {vol_str}")

                with row_cols[5]:
                    st.code(mint, language=None)

                st.markdown("<hr style='margin: 2px 0; border: none; border-top: 1px solid #333;'>",
                            unsafe_allow_html=True)

            st.markdown("")
            col_prev, col_info, col_next = st.columns([1, 2, 1])

            with col_prev:
                if st.button("◀ Prev", key="prev_bottom", disabled=st.session_state.tokens_page <= 1,
                             use_container_width=True):
                    st.session_state.tokens_page -= 1
                    st.rerun()

            with col_info:
                st.markdown(
                    f"""
                        <div style='text-align: center; padding: 8px;'>
                            Page <b>{st.session_state.tokens_page}</b> of <b>{total_pages}</b> ({total_tokens} tokens)
                        </div>
                    """,
                    unsafe_allow_html=True
                )

            with col_next:
                if st.button("Next ▶", key="next_bottom", disabled=st.session_state.tokens_page >= total_pages,
                             use_container_width=True):
                    st.session_state.tokens_page += 1
                    st.rerun()
        else:
            st.warning("No tokens found. Make sure Redis is running and pools are loaded.")

    except redis.ConnectionError:
        st.error("Failed to connect to Redis. Make sure Redis is running.")
    except Exception as e:
        st.error(f"Error loading tokens: {str(e)}")
        st.exception(e)

elif page == "Swap":
    _, swap_col, _ = st.columns([1, 2, 1])

    with swap_col:
        st.markdown("### Swap")

        with st.expander("⚙ Settings", expanded=True):
            swap_mode_option = st.radio(
                "Swap Mode",
                ["Exact Input", "Exact Output"],
                horizontal=True,
                help="ExactIn: you specify how much to pay. ExactOut: you specify how much to receive."
            )
            amount_specified_is_input = (swap_mode_option == "Exact Input")

        if st.session_state.a_to_b:
            sell_token_options = ["Custom"] + [k for k in TOKEN_INFO.keys() if k != "USDC"]
            default_sell_idx = 1
        else:
            sell_token_options = None

        if st.session_state.a_to_b:
            buy_token_options = None
        else:
            buy_token_options = ["Custom"] + [k for k in TOKEN_INFO.keys() if k != "USDC"]
            default_buy_idx = 1

        with st.container(border=True):
            st.caption("You Pay")
            pay_col1, pay_col2 = st.columns([2, 1])

            with pay_col1:
                if amount_specified_is_input:
                    delta_amount = st.number_input(
                        "Amount",
                        min_value=0.0,
                        value=1.0,
                        step=0.1,
                        label_visibility="collapsed",
                        key="pay_amount"
                    )
                else:
                    if st.session_state.last_result is not None and not amount_specified_is_input:
                        st.markdown(f"#### {st.session_state.last_result:,.6f}")
                        st.caption("SoulScan estimate")
                    else:
                        st.markdown("#### —")
                        st.caption("Calculated")

            with pay_col2:
                if st.session_state.a_to_b:
                    sell_choice = st.selectbox(
                        "Token",
                        sell_token_options,
                        index=default_sell_idx,
                        format_func=lambda x: f"◎ {x}" if x == "SOL" else x,
                        label_visibility="collapsed",
                        key="sell_token"
                    )
                    if sell_choice == "Custom":
                        custom_mint = st.text_input("Mint", placeholder="Enter mint address", key="custom_sell_mint")
                        if custom_mint and len(custom_mint) > 30:
                            if st.session_state.custom_sell_token is None or st.session_state.custom_sell_token.get(
                                    "mint") != custom_mint:
                                with st.spinner("Looking up token..."):
                                    token_info = search_token_info(custom_mint)
                                    if token_info:
                                        st.session_state.custom_sell_token = token_info
                                    else:
                                        st.error("Token not found. Using default.")
                                        st.session_state.custom_sell_token = None

                            if st.session_state.custom_sell_token:
                                t = st.session_state.custom_sell_token
                                st.markdown(
                                    f'<img src="{t["icon"]}" width="20" style="vertical-align:middle; border-radius:50%;"/> **{t["symbol"]}**',
                                    unsafe_allow_html=True)
                                base_mint = t["mint"]
                                input_decimals = t["decimals"]
                            else:
                                base_mint = TOKEN_INFO["SOL"]["mint"]
                                input_decimals = TOKEN_INFO["SOL"]["decimals"]
                        else:
                            base_mint = TOKEN_INFO["SOL"]["mint"]
                            input_decimals = TOKEN_INFO["SOL"]["decimals"]
                    else:
                        base_mint = TOKEN_INFO[sell_choice]["mint"]
                        input_decimals = TOKEN_INFO[sell_choice]["decimals"]
                else:
                    st.markdown(token_display("USDC"), unsafe_allow_html=True)
                    input_decimals = 6

        _, btn_col, _ = st.columns([3, 1, 3])
        with btn_col:
            st.button("⇅", on_click=toggle_swap_direction, use_container_width=True,
                      help="Switch swap direction", type="secondary")

        with st.container(border=True):
            st.caption("You Receive")
            recv_col1, recv_col2 = st.columns([2, 1])

            with recv_col1:
                if not amount_specified_is_input:
                    delta_amount = st.number_input(
                        "Amount",
                        min_value=0.0,
                        value=1.0,
                        step=0.1,
                        label_visibility="collapsed",
                        key="recv_amount"
                    )
                else:
                    if st.session_state.last_result is not None and amount_specified_is_input:
                        st.markdown(f"#### {st.session_state.last_result:,.6f}")
                        st.caption("SoulScan estimate")
                    else:
                        st.markdown("#### —")
                        st.caption("Calculated")

            with recv_col2:
                if st.session_state.a_to_b:
                    st.markdown(token_display("USDC"), unsafe_allow_html=True)
                    quote_mint = TOKEN_INFO["USDC"]["mint"]
                    output_decimals = 6
                else:
                    buy_choice = st.selectbox(
                        "Token",
                        buy_token_options,
                        index=default_buy_idx,
                        format_func=lambda x: f"◎ {x}" if x == "SOL" else (f"$ {x}" if x == "USDT" else x),
                        label_visibility="collapsed",
                        key="buy_token"
                    )
                    if buy_choice == "Custom":
                        custom_mint = st.text_input("Mint", placeholder="Enter mint address", key="custom_buy_mint")
                        if custom_mint and len(custom_mint) > 30:
                            if st.session_state.custom_buy_token is None or st.session_state.custom_buy_token.get(
                                    "mint") != custom_mint:
                                with st.spinner("Looking up token..."):
                                    token_info = search_token_info(custom_mint)
                                    if token_info:
                                        st.session_state.custom_buy_token = token_info
                                    else:
                                        st.error("Token not found. Using default.")
                                        st.session_state.custom_buy_token = None

                            if st.session_state.custom_buy_token:
                                t = st.session_state.custom_buy_token
                                st.markdown(
                                    f'<img src="{t["icon"]}" width="20" style="vertical-align:middle; border-radius:50%;"/> **{t["symbol"]}**',
                                    unsafe_allow_html=True)
                                base_mint = t["mint"]
                                output_decimals = t["decimals"]
                            else:
                                base_mint = TOKEN_INFO["SOL"]["mint"]
                                output_decimals = TOKEN_INFO["SOL"]["decimals"]
                        else:
                            base_mint = TOKEN_INFO["SOL"]["mint"]
                            output_decimals = TOKEN_INFO["SOL"]["decimals"]
                    else:
                        base_mint = TOKEN_INFO[buy_choice]["mint"]
                        output_decimals = TOKEN_INFO[buy_choice]["decimals"]
                    quote_mint = TOKEN_INFO["USDC"]["mint"]

        if amount_specified_is_input:
            decimals = input_decimals
        else:
            decimals = output_decimals

        a_to_b = st.session_state.a_to_b
        raw_amount = int(delta_amount * 10 ** decimals)

        st.markdown("")

        if st.button("Compare Routes", type="primary", use_container_width=True):
            if not base_mint:
                st.error("Please enter a base mint address")
            elif not quote_mint:
                st.error("Please enter a quote mint address")
            else:
                with st.spinner("Calculating..."):
                    try:
                        metadata = get_active_metadata(r)
                        state = get_active_state(r)
                        smart_router = SmartRouter(metadata=metadata, state=state)

                        result = smart_router.ExactSwap(
                            base_mint=base_mint,
                            quote_mint=quote_mint,
                            delta_amount=raw_amount,
                            amount_specified_is_input=amount_specified_is_input,
                            a_to_b=a_to_b
                        )

                        if result.get("success"):
                            smart_router_output = result.get("result", 0)
                            if amount_specified_is_input:
                                result_decimals = output_decimals
                            else:
                                result_decimals = input_decimals
                            smart_router_human = smart_router_output / (10 ** result_decimals)
                            st.session_state.last_result = smart_router_human
                        else:
                            smart_router_human = 0

                        if a_to_b:
                            jup_input = base_mint
                            jup_output = quote_mint
                        else:
                            jup_input = quote_mint
                            jup_output = base_mint

                        swap_mode = "ExactIn" if amount_specified_is_input else "ExactOut"
                        jup_result = run_jupiter_quote(jup_input, jup_output, raw_amount, swap_mode)

                        if jup_result.get("success"):
                            jup_data = jup_result.get("data", {})
                            if amount_specified_is_input:
                                jupiter_output = int(jup_data.get("outAmount", 0))
                                jup_result_decimals = output_decimals
                            else:
                                jupiter_output = int(jup_data.get("inAmount", 0))
                                jup_result_decimals = input_decimals
                            jupiter_human = jupiter_output / (10 ** jup_result_decimals)
                        else:
                            jupiter_human = 0
                            jup_data = {}

                        st.session_state.cached_results = {
                            "smart_router": {"result": result, "human": smart_router_human},
                            "jupiter": {"result": jup_result, "data": jup_data, "human": jupiter_human},
                            "amount_specified_is_input": amount_specified_is_input
                        }
                        st.session_state.show_results = True
                        st.rerun()

                    except redis.ConnectionError:
                        st.error("Failed to connect to Redis. Make sure Redis is running.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        st.exception(e)

    if st.session_state.show_results and st.session_state.cached_results:
        cached = st.session_state.cached_results
        smart_router_human = cached["smart_router"]["human"]
        jupiter_human = cached["jupiter"]["human"]
        result = cached["smart_router"]["result"]
        jup_result = cached["jupiter"]["result"]
        jup_data = cached["jupiter"]["data"]
        amount_specified_is_input = cached["amount_specified_is_input"]

        result_label = "Output Amount" if amount_specified_is_input else "Input Amount"

        result_col1, result_col2 = st.columns(2)

        with result_col1:
            st.subheader("SoulScan")
            if result.get("success"):
                st.success("SmartRouter Success")
                st.metric(result_label, f"{smart_router_human:,.6f}")
                st.write(
                    f"**Route:** `{' → '.join(result.get('route', []))[:50]}...`" if result.get(
                        'route') else "No route")
                with st.expander("Full Response"):
                    st.json(result)
            else:
                st.error(f"SmartRouter Failed: {result.get('message', 'Unknown error')}")
                st.json(result)

        with result_col2:
            st.subheader("Jupiter")
            if jup_result.get("success"):
                st.success("Jupiter Success")
                st.metric(result_label, f"{jupiter_human:,.6f}")
                route_plan = jup_data.get("routePlan", [])
                if route_plan:
                    dexes = [step.get("swapInfo", {}).get("label", "?") for step in route_plan]
                    st.write(f"**Route:** `{' → '.join(dexes)}`")
                with st.expander("Full Response"):
                    st.json(jup_data)
            else:
                st.error(f"Jupiter Failed: {jup_result.get('error', 'Unknown error')}")

        st.divider()
        st.subheader("Comparison")

        if smart_router_human > 0 and jupiter_human > 0:
            diff = smart_router_human - jupiter_human
            diff = diff if amount_specified_is_input else -diff
            diff_pct = (diff / jupiter_human) * 100

            comp_col1, comp_col2, comp_col3 = st.columns(3)

            with comp_col1:
                st.metric("SoulScan", f"{smart_router_human:,.6f}")

            with comp_col2:
                st.metric("Jupiter", f"{jupiter_human:,.6f}")

            with comp_col3:
                delta_color = "normal" if abs(diff_pct) < 0.1 else ("inverse" if diff_pct < 0 else "normal")
                st.metric(
                    "Difference",
                    f"{diff:+,.6f}",
                    delta=f"{diff_pct:+.4f}%",
                    delta_color=delta_color
                )

            if diff_pct > 0.1:
                st.success(f"SoulScan is **better** than Jupiter by {diff_pct:.4f}%!")
            elif diff_pct < -0.1:
                st.warning(f"Jupiter is **better** than SoulScan by {abs(diff_pct):.4f}%")
            else:
                st.info("Results are nearly identical (within 0.1%)")
        else:
            st.warning("Cannot compare - one or both calculations failed")
