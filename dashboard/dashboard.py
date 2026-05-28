# ==============================================================================
# dashboard.py — Streamlit Dashboard SDG-10 Ketimpangan Pendapatan
# ==============================================================================

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Tambahkan scripts ke path agar bisa import config
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from config import GOLD_DIR, GOLD_GINI_FILE, GOLD_QUINTILE_FILE, ASSETS_DIR
from components.gini_chart import render_gini_chart
from components.quintile_table import render_quintile_table
from components.income_dist import render_income_distribution

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SDG-10 Dashboard | Ketimpangan Pendapatan",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .metric-card {
        background: linear-gradient(135deg, #1a1f2e, #252b3b);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        border-left: 4px solid #4f8ef7;
        margin-bottom: 0.5rem;
    }
    .metric-value { font-size: 2rem; font-weight: bold; color: #4f8ef7; }
    .metric-label { font-size: 0.85rem; color: #8892a4; }
    h1, h2, h3 { color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)


# ── Load Data ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data():
    """Load semua data Gold Layer."""
    try:
        gini_df     = pd.read_parquet(GOLD_DIR / GOLD_GINI_FILE)
        quintile_df = pd.read_parquet(GOLD_DIR / GOLD_QUINTILE_FILE)
        return gini_df, quintile_df
    except FileNotFoundError:
        st.error("❌ Data Gold Layer belum tersedia. Jalankan pipeline terlebih dahulu.")
        return None, None


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    logo_path = ASSETS_DIR / "logo.png"
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)

    st.title("⚖️ SDG-10 Dashboard")
    st.caption("Analisis Ketimpangan Pendapatan — IPUMS")
    st.divider()

    gini_df, quintile_df = load_data()

    if gini_df is not None:
        years = sorted(gini_df["year"].unique())
        selected_years = st.slider(
            "Rentang Tahun",
            min_value=int(min(years)),
            max_value=int(max(years)),
            value=(int(min(years)), int(max(years))),
        )
        st.divider()
        st.caption("📊 **Institut Teknologi Sepuluh Nopember**")
        st.caption("Big Data Analytics — SDG Goal 10")


# ── Main Content ───────────────────────────────────────────────────────────────
st.title("📊 Analisis Ketimpangan Pendapatan (SDG Goal 10)")
st.caption("Sumber data: IPUMS — Current Population Survey (CPS)")
st.divider()

if gini_df is not None and quintile_df is not None:
    # Filter data sesuai tahun
    mask = (gini_df["year"] >= selected_years[0]) & (gini_df["year"] <= selected_years[1])
    filtered_gini = gini_df[mask]

    # ── KPI Row ────────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    latest = filtered_gini.iloc[-1] if len(filtered_gini) > 0 else None

    with col1:
        val = f"{latest['gini']:.4f}" if latest is not None else "N/A"
        st.metric("Gini Coefficient (Terbaru)", val, help="0 = merata, 1 = tidak merata")

    with col2:
        val = f"{latest['theil']:.4f}" if latest is not None else "N/A"
        st.metric("Theil Index (Terbaru)", val, help="Generalized Entropy GE(1)")

    with col3:
        val = f"{latest['palma']:.2f}x" if latest is not None else "N/A"
        st.metric("Palma Ratio (Terbaru)", val, help="Rasio 10% teratas / 40% terbawah")

    with col4:
        val = f"{int(latest['n_obs']):,}" if latest is not None else "N/A"
        st.metric("Observasi", val)

    st.divider()

    # ── Chart Section ──────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📈 Tren Gini", "📊 Distribusi Quintile", "📉 Distribusi Pendapatan"])

    with tab1:
        render_gini_chart(filtered_gini)

    with tab2:
        q_mask = (
            (quintile_df["year"] >= selected_years[0]) &
            (quintile_df["year"] <= selected_years[1])
        )
        render_quintile_table(quintile_df[q_mask])

    with tab3:
        render_income_distribution(filtered_gini)

else:
    st.info("🚀 Jalankan pipeline Bronze → Silver → Gold terlebih dahulu, lalu refresh halaman ini.")
    st.code("make pipeline", language="bash")
