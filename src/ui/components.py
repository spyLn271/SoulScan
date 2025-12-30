import streamlit as st
from streamlit_option_menu import option_menu
from src.ui.state import TOKEN_INFO

def token_display(token_name):
    """Display token with icon and name inline"""
    if token_name in TOKEN_INFO:
        icon_url = TOKEN_INFO[token_name]["icon"]
        return f'<img src="{icon_url}" width="24" style="vertical-align:middle; margin-right:8px;"/><span style="font-size:20px; font-weight:bold;">{token_name}</span>'
    return token_name

def render_sidebar():
    with st.sidebar:
        st.markdown("""
            <style>
                @keyframes ghost-float {
                    0%, 100% { transform: translateY(0px) rotate(-1deg); }
                    50% { transform: translateY(-15px) rotate(1deg); }
                }
                @keyframes shadow-pulse {
                    0%, 100% { transform: scaleX(1); opacity: 0.4; }
                    50% { transform: scaleX(0.75); opacity: 0.2; }
                }
                @keyframes blink {
                    0%, 90%, 100% { transform: scaleY(1); }
                    95% { transform: scaleY(0.1); }
                }
                .ghost-brand {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 12px;
                    padding: 1rem 0;
                }
                .ghost-anim {
                    animation: ghost-float 3s ease-in-out infinite;
                }
                .ghost-shadow {
                    transform-origin: center;
                    animation: shadow-pulse 3s ease-in-out infinite;
                }
                .ghost-eyes {
                    transform-origin: center;
                    animation: blink 4s ease-in-out infinite;
                }
                .ghost-brand-title {
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: #ffffff;
                }
            </style>
            <div class="sidebar-brand">
                <div class="ghost-brand">
                    <div class="ghost-anim">
                        <svg width="60" height="75" viewBox="0 0 200 200">
                            <ellipse class="ghost-shadow" cx="100" cy="180" rx="45" ry="6" fill="rgba(167,139,250,0.3)"/>
                            <path d="M40 140 C40 55,160 55,160 140 L160 155 Q140 140,120 160 Q100 140,80 160 Q60 140,40 155 Z" fill="#f8f8ff" stroke="rgba(167,139,250,0.4)" stroke-width="2"/>
                            <ellipse class="ghost-eyes" cx="75" cy="100" rx="10" ry="12" fill="#333"/>
                            <ellipse class="ghost-eyes" cx="125" cy="100" rx="10" ry="12" fill="#333"/>
                            <circle cx="71" cy="96" r="3" fill="#fff" opacity="0.9"/>
                            <circle cx="121" cy="96" r="3" fill="#fff" opacity="0.9"/>
                            <ellipse cx="60" cy="118" rx="7" ry="4" fill="#a78bfa" opacity="0.5"/>
                            <ellipse cx="140" cy="118" rx="7" ry="4" fill="#a78bfa" opacity="0.5"/>
                            <path d="M88 125 Q100 138,112 125" fill="none" stroke="#333" stroke-width="3" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <span class="ghost-brand-title">SoulScan</span>
                </div>
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

    return page
