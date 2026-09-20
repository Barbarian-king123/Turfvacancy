"""
app.py
Streamlit wrapper rendering the exact TurfPulse AI dashboard.
Hides default Streamlit chrome to align with the provided design.
"""

from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="TurfPulse AI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit header, footer, and sidebar completely
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    iframe {
        width: 100% !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

html_path = Path(__file__).parent / "static" / "index.html"
if html_path.exists():
    html_content = html_path.read_text(encoding="utf-8")
    st.components.v1.html(html_content, height=1800, scrolling=True)
else:
    st.error("static/index.html not found.")
