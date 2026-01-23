import streamlit as st

COMMON_TOKENS = {
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    "SOL (Wrapped)": "So11111111111111111111111111111111111111112",
}

TOKEN_INFO = {
    "USDC": {
        "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "icon": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v/logo.png",
        "decimals": 6
    },
    "USDT": {
        "mint": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        "icon": "https://cryptologos.cc/logos/tether-usdt-logo.png",
        "decimals": 6,
    },
    "SOL": {
        "mint": "So11111111111111111111111111111111111111112",
        "icon": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png",
        "decimals": 9
    },
}

def init_session_state():
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
    if "tokens_page" not in st.session_state:
        st.session_state.tokens_page = 1
    if "quote_currency" not in st.session_state:
        st.session_state.quote_currency = "USDC"

def toggle_swap_direction():
    st.session_state.a_to_b = not st.session_state.a_to_b
    st.session_state.last_result = None
    st.session_state.show_results = False
    st.session_state.cached_results = None
    st.session_state.custom_sell_token = None
    st.session_state.custom_buy_token = None
