import streamlit as st
import redis
from src.SoulEngine.SmartRouter import SmartRouter
from src.SoulEngine.SmartRouter.OnlineSmartRouter import get_active_metadata, get_active_state

st.set_page_config(page_title="SoulScan", layout="wide")

st.title("SoulScan")

# Common token addresses
COMMON_TOKENS = {
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "SOL (Wrapped)": "So11111111111111111111111111111111111111112",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
}

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

    amount_specified_is_input = st.checkbox("Amount Specified is Input", value=True)
    a_to_b = st.checkbox("A to B (Base to Quote)", value=True)

st.divider()

st.write(f"**Raw Amount:** {delta_amount * 10 ** decimals:,.0f}")

if st.button("Execute Swap Calculation", type="primary", use_container_width=True):
    if not base_mint:
        st.error("Please enter a base mint address")
    elif not quote_mint:
        st.error("Please enter a quote mint address")
    else:
        with st.spinner("Connecting to Redis and calculating swap..."):
            try:
                r = redis.Redis(decode_responses=True)

                metadata = get_active_metadata(r)
                state = get_active_state(r)

                smart_router = SmartRouter(metadata=metadata, state=state)

                result = smart_router.ExactSwap(
                    base_mint=base_mint,
                    quote_mint=quote_mint,
                    delta_amount=delta_amount * 10 ** decimals,
                    amount_specified_is_input=amount_specified_is_input,
                    a_to_b=a_to_b
                )

                st.success("Swap calculation completed!")
                st.subheader("Result")
                st.json(result)

            except redis.ConnectionError:
                st.error("Failed to connect to Redis. Make sure Redis is running.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.exception(e)
