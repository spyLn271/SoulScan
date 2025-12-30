import streamlit as st
import redis
from src.ui.styles import apply_styles
from src.ui.state import init_session_state
from src.ui.components import render_sidebar
from src.ui.pages.swap import render_swap_page
from src.ui.pages.tokens import render_tokens_page

st.set_page_config(page_title="SoulScan", layout="wide", page_icon="👻")

# Initialize
r = redis.Redis(decode_responses=True)
apply_styles()
init_session_state()

# Layout
page = render_sidebar()

if page == "Swap":
    render_swap_page(r)
elif page == "Tokens":
    render_tokens_page(r)
