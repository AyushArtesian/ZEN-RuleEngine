import sys
import logging
from pathlib import Path

# Ensure the project root is on the Python path for all pages
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from config.settings import settings, LOGS_DIR
from database.db import init_db

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(str(LOGS_DIR / "app.log"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=settings.APP_NAME,
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] .css-1d391kg { padding-top: 1rem; }
        .block-container { padding-top: 2rem; }
        h1 { color: #1f2937; }
        .stAlert > div { border-radius: 0.5rem; }
        div[data-testid="metric-container"] {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 0.5rem;
            padding: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Database init (runs once per session) ──────────────────────────────────
if "db_initialized" not in st.session_state:
    try:
        init_db()
        st.session_state.db_initialized = True
    except Exception as exc:
        st.error(f"❌ Database initialisation failed: {exc}")
        st.stop()

# ── Home page ──────────────────────────────────────────────────────────────
st.title("📋 Invoice Rule Engine")
st.caption("Intelligent invoice routing through configurable business rules — no code changes required")

st.divider()

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown("#### 🚀 How it works")
    st.markdown(
        """
        1. **Create Rules** — define conditions for invoice routing
        2. **Prioritise** — lower priority number wins first
        3. **Evaluate** — engine checks each invoice against active rules
        4. **Audit** — every decision is logged for full traceability
        """
    )

with col2:
    st.markdown("#### ⚡ Supported Actions")
    st.success("✅ **Bypass Human Queue** — post invoice directly")
    st.warning("⏳ **Send to Human Queue** — route for manual review")
    st.error("🚫 **Block Posting** — reject the invoice")

with col3:
    st.markdown("#### 📌 Example Rule")
    st.code(
        'Vendor       = "Vendor A"\nAND\nValidation   = False\n─────────────────────────\n→  Bypass Human Queue',
        language="text",
    )
    st.caption("Use the **sidebar** to navigate between pages.")

st.divider()
st.caption("Invoice Rule Engine POC  ·  Python · Streamlit · ZEN Engine · SQLite")
