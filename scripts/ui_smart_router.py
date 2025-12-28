import streamlit as st
import redis
import aiohttp
import asyncio
from src.SoulEngine.SmartRouter import SmartRouter
from src.SoulEngine.SmartRouter.OnlineSmartRouter import get_active_metadata, get_active_state

st.set_page_config(page_title="SoulScan", layout="wide", page_icon="👻")

st.title("👻 SoulScan")

COMMON_TOKENS = {
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "SOL (Wrapped)": "So11111111111111111111111111111111111111112",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
}

TOKEN_DECIMALS = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": 6,
    "So11111111111111111111111111111111111111112": 9,
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": 6,
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
    "USDT": {
        "mint": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        "icon": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB/logo.png",
        "decimals": 6
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
    .swap-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 20px;
        padding: 24px;
        border: 1px solid #0f3460;
    }
    .token-box {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }
    .swap-label {
        color: #888;
        font-size: 14px;
        margin-bottom: 8px;
    }
    .token-display {
        font-size: 24px;
        font-weight: bold;
    }
    div[data-testid="stNumberInput"] input {
        font-size: 24px !important;
        font-weight: bold !important;
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


_, swap_col, _ = st.columns([1, 2, 1])

with swap_col:
    st.markdown("### Swap")

    with st.expander("⚙️ Settings", expanded=True):
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
                    format="%.6f",
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
                    format_func=lambda x: f"◎ {x}" if x == "SOL" else (f"$ {x}" if x == "USDT" else x),
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
                    format="%.6f",
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
                f"**Route:** `{' → '.join(result.get('route', []))[:50]}...`" if result.get('route') else "No route")
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
