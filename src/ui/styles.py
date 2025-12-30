import streamlit as st

def apply_styles():
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

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
