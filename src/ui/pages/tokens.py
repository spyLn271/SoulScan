import streamlit as st
import redis
from src.SoulEngine.SoulHelper import get_all_DEX_active_tokens, get_all_common_dict_of_tokens
from src.ui.api import get_tokens_detailed

def render_tokens_page(r: redis.Redis):
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
