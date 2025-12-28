import streamlit as st
import redis
import aiohttp
import asyncio
from src.SoulEngine.SmartRouter import SmartRouter
from src.SoulEngine.SmartRouter.OnlineSmartRouter import get_active_metadata, get_active_state

st.set_page_config(page_title="SoulScan", layout="wide")

st.title("🔮 SoulScan")

# Common token addresses
COMMON_TOKENS = {
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "SOL (Wrapped)": "So11111111111111111111111111111111111111112",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
}

TOKEN_DECIMALS = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": 6,  # USDC
    "So11111111111111111111111111111111111111112": 9,  # SOL
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": 6,  # USDT
}

r = redis.Redis(decode_responses=True)

JUPITER_API_KEY = "5c2df4a8-f56d-447e-8354-4ed9d3368b84"


async def get_jupiter_quote(input_mint: str, output_mint: str, amount: int, swap_mode: str = "ExactIn") -> dict:
    """
    Fetch quote from Jupiter Quote API
    https://dev.jup.ag/docs/swap/get-quote
    """
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


col1, col2 = st.columns(2)

with col1:
    st.subheader("Input Parameters")

    base_mint_option = st.selectbox(
        "Base Token (or enter custom)",
        ["Custom"] + list(COMMON_TOKENS.keys()),
        index=0
    )

    if base_mint_option == "Custom":
        base_mint = st.text_input("Base Mint Address", placeholder="Enter token mint address")
    else:
        base_mint = COMMON_TOKENS[base_mint_option]
        st.code(base_mint, language=None)

    quote_mint_option = st.selectbox(
        "Quote Token",
        ["USDC"],
        index=0
    )

    if quote_mint_option == "Custom":
        quote_mint = st.text_input("Quote Mint Address", placeholder="Enter token mint address")
    else:
        quote_mint = COMMON_TOKENS[quote_mint_option]
        st.code(quote_mint, language=None)

with col2:
    st.subheader("Swap Configuration")

    delta_amount = st.number_input("Delta Amount", min_value=0.0, value=1.0, step=0.1)
    decimals = st.number_input("Token Decimals", min_value=0, max_value=18, value=6, step=1)
    output_decimals = st.number_input("Output Token Decimals", min_value=0, max_value=18, value=6, step=1)

    amount_specified_is_input = st.checkbox("Amount Specified is Input", value=True)
    a_to_b = st.checkbox("A to B (Base to Quote)", value=True)

st.divider()

raw_amount = int(delta_amount * 10 ** decimals)
st.write(f"**Raw Amount (atomic):** `{raw_amount:,}`")

if st.button("🚀 Execute Swap Calculation", type="primary", use_container_width=True):
    if not base_mint:
        st.error("Please enter a base mint address")
    elif not quote_mint:
        st.error("Please enter a quote mint address")
    else:
        result_col1, result_col2 = st.columns(2)

        with result_col1:
            st.subheader("SoulScan")
            with st.spinner("Calculating swap..."):
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
                        st.success("✅ SmartRouter Success")

                        smart_router_output = result.get("result", 0)
                        smart_router_human = smart_router_output / (10 ** output_decimals)

                        st.metric("Output Amount", f"{smart_router_human:,.6f}")
                        st.write(f"**Route:** `{' → '.join(result.get('route', []))[:50]}...`" if result.get(
                            'route') else "No route")

                        with st.expander("Full Response"):
                            st.json(result)
                    else:
                        st.error(f"❌ SmartRouter Failed: {result.get('message', 'Unknown error')}")
                        smart_router_output = 0
                        smart_router_human = 0
                        st.json(result)

                except redis.ConnectionError:
                    st.error("Failed to connect to Redis. Make sure Redis is running.")
                    smart_router_output = 0
                    smart_router_human = 0
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.exception(e)
                    smart_router_output = 0
                    smart_router_human = 0

        with result_col2:
            st.subheader("Jupiter")
            with st.spinner("Fetching Jupiter quote..."):
                if a_to_b:
                    jup_input = base_mint
                    jup_output = quote_mint
                else:
                    jup_input = quote_mint
                    jup_output = base_mint

                swap_mode = "ExactIn" if amount_specified_is_input else "ExactOut"

                jup_result = run_jupiter_quote(
                    input_mint=jup_input,
                    output_mint=jup_output,
                    amount=raw_amount,
                    swap_mode=swap_mode
                )

                if jup_result.get("success"):
                    st.success("✅ Jupiter Success")

                    jup_data = jup_result.get("data", {})

                    if amount_specified_is_input:
                        jupiter_output = int(jup_data.get("outAmount", 0))
                    else:
                        jupiter_output = int(jup_data.get("inAmount", 0))

                    jupiter_human = jupiter_output / (10 ** output_decimals)

                    st.metric("Output Amount", f"{jupiter_human:,.6f}")

                    route_plan = jup_data.get("routePlan", [])
                    if route_plan:
                        dexes = [step.get("swapInfo", {}).get("label", "?") for step in route_plan]
                        st.write(f"**Route:** `{' → '.join(dexes)}`")

                    with st.expander("Full Response"):
                        st.json(jup_data)
                else:
                    st.error(f"❌ Jupiter Failed: {jup_result.get('error', 'Unknown error')}")
                    jupiter_output = 0
                    jupiter_human = 0

        st.divider()
        st.subheader("Comparison")

        try:
            if smart_router_human > 0 and jupiter_human > 0:
                diff = smart_router_human - jupiter_human
                diff_pct = (diff / jupiter_human) * 100
                diff_pct = diff_pct if amount_specified_is_input else -diff_pct

                comp_col1, comp_col2, comp_col3 = st.columns(3)

                with comp_col1:
                    st.metric("SmartRouter Output", f"{smart_router_human:,.6f}")

                with comp_col2:
                    st.metric("Jupiter Output", f"{jupiter_human:,.6f}")

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
                    st.warning(f"Jupiter is **better** than your SmartRouter by {abs(diff_pct):.4f}%")
                else:
                    st.info("✅ Results are nearly identical (within 0.1%)")
            else:
                st.warning("Cannot compare - one or both calculations failed")
        except Exception as e:
            st.error(f"Comparison error: {e}")

