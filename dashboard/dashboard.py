# ==============================================================================
# dashboard.py — SDG-10 Dashboard: Brazil & Mexico Income Inequality
# ==============================================================================

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from config import GOLD_DIR, GOLD_GINI_FILE, GOLD_QUINTILE_FILE, GOLD_THEIL_FILE, ASSETS_DIR
from components.visualizations import (
    render_tab_inequality,
    render_tab_quintile,
    render_tab_demographics,
)
from components.sdg_indicators import render_sdg_indicators
from components.lineage import render_data_lineage
from components.bronze_sample import render_bronze_sample

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SDG-10 | Ketimpangan Pendapatan IPUMS",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0e1117; }
    [data-testid="stSidebar"]          { background-color: #161b27; }
    .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }
    h1, h2, h3, h4, h5 { color: #e2e8f0 !important; }
    [data-testid="stMetricValue"]  { font-size: 1.5rem; color: #4f8ef7; }
    [data-testid="stMetricLabel"]  { font-size: 0.78rem; color: #8892a4; }
    .stTabs [data-baseweb="tab"] { font-size: 0.9rem; font-weight: 600; }
    hr { border-color: #2a2f3e; }
</style>
""", unsafe_allow_html=True)

COUNTRY_MAP = {76: "Brazil 🇧🇷", 484: "Mexico 🇲🇽"}


# ── Load Data ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="Memuat data Gold Layer…")
def load_all():
    try:
        gini_df     = pd.read_parquet(GOLD_DIR / GOLD_GINI_FILE)
        quintile_df = pd.read_parquet(GOLD_DIR / GOLD_QUINTILE_FILE)
        theil_df    = pd.read_parquet(GOLD_DIR / GOLD_THEIL_FILE)
        sex_df      = pd.read_parquet(GOLD_DIR / "gold_demog_sex.parquet")
        emp_df      = pd.read_parquet(GOLD_DIR / "gold_demog_emp.parquet")
        edu_df      = pd.read_parquet(GOLD_DIR / "gold_demog_edu.parquet")
        age_df      = pd.read_parquet(GOLD_DIR / "gold_demog_age.parquet")

        # Tambah kolom country_name di semua tabel
        gini_df["country_name"] = gini_df["country"].map(COUNTRY_MAP).fillna(gini_df["country"].astype(str))
        quintile_df["country_name"] = quintile_df["country"].map(COUNTRY_MAP).fillna(quintile_df["country"].astype(str))

        for df in [sex_df, emp_df, edu_df, age_df]:
            df["country_name"] = df["COUNTRY"].map(COUNTRY_MAP).fillna(df["COUNTRY"].astype(str))

        return gini_df, quintile_df, theil_df, sex_df, emp_df, edu_df, age_df

    except FileNotFoundError as e:
        st.error(f"❌ File tidak ditemukan: `{e.filename}`. Jalankan pipeline Spark terlebih dahulu.")
        return (None,) * 7
    except Exception as e:
        st.error(f"❌ Gagal memuat data: {e}")
        return (None,) * 7


gini_df, quintile_df, theil_df, sex_df, emp_df, edu_df, age_df = load_all()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    logo_path = ASSETS_DIR / "logo.png"
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)

    st.markdown("## ⚖️ SDG-10 Dashboard")
    st.caption("Analisis Ketimpangan Pendapatan")
    st.caption("Sumber: IPUMS International")
    st.divider()

    # Info Dataset
    if gini_df is not None:
        countries = gini_df["country_name"].unique().tolist()
        years     = sorted(gini_df["year"].unique().tolist())

        st.markdown("### 📦 Dataset Tersedia")
        for c in countries:
            st.markdown(f"- {c}")
        st.caption(f"Tahun: {', '.join(str(y) for y in years)}")

        # Total observasi
        if theil_df is not None:
            total_obs = int(theil_df["n_obs"].sum())
            st.metric("Total Observasi", f"{total_obs:,}")

        # Filter opsional — hanya tampilkan negara tertentu jika diinginkan
        st.divider()
        st.markdown("### 🔽 Filter")
        all_countries = sorted(gini_df["country"].unique().tolist())
        country_labels = {c: COUNTRY_MAP.get(c, str(c)) for c in all_countries}
        selected_countries = st.multiselect(
            "Tampilkan Negara",
            options=all_countries,
            default=all_countries,
            format_func=lambda c: country_labels.get(c, str(c)),
        )
        if not selected_countries:
            selected_countries = all_countries

    st.divider()
    st.caption("📊 **Institut Teknologi Sumatera**")
    st.caption("Big Data Analytics — Kelompok 12")


# ── Stop jika data tidak ada ───────────────────────────────────────────────────
if gini_df is None:
    st.info("🚀 Data Gold Layer belum tersedia. Jalankan pipeline Spark terlebih dahulu.")
    st.stop()

# ── Filter berdasarkan pilihan sidebar ────────────────────────────────────────
f_gini     = gini_df[gini_df["country"].isin(selected_countries)].copy()
f_quintile = quintile_df[quintile_df["country"].isin(selected_countries)].copy()
f_theil    = theil_df[theil_df["COUNTRY"].isin(selected_countries)].copy()
f_sex      = sex_df[sex_df["COUNTRY"].isin(selected_countries)].copy()
f_emp      = emp_df[emp_df["COUNTRY"].isin(selected_countries)].copy()
f_edu      = edu_df[edu_df["COUNTRY"].isin(selected_countries)].copy()
f_age      = age_df[age_df["COUNTRY"].isin(selected_countries)].copy()


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("# 📊 Analisis Ketimpangan Pendapatan — SDG Goal 10")
st.caption("Data: IPUMS International · Brazil & Mexico · Tahun 2010 · ~32,5 juta observasi")
st.divider()

# ── KPI Ringkasan (semua negara terpilih) ─────────────────────────────────────
n_cols = max(len(f_gini) * 3, 1)
kpi_cols = st.columns(len(f_gini) * 4)

for i, (_, row) in enumerate(f_gini.iterrows()):
    base = i * 4
    with kpi_cols[base]:
        st.metric(f"Gini — {row['country_name']}",
                  f"{float(row['gini']):.4f}", help="0=merata, 1=tidak merata")
    with kpi_cols[base + 1]:
        st.metric(f"Palma — {row['country_name']}",
                  f"{float(row['palma']):.2f}×", help="Q10/Q40")
    with kpi_cols[base + 2]:
        theil_row = f_theil[f_theil["COUNTRY"] == int(row["country"])]
        med = float(theil_row["median_income"].iloc[0]) if not theil_row.empty else 0
        st.metric(f"Median — {row['country_name']}", f"{med:,.0f}")
    with kpi_cols[base + 3]:
        st.metric(f"Obs — {row['country_name']}",
                  f"{int(row['n_obs']):,}")

st.divider()

# ── Tab Utama ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📉 Ketimpangan Pendapatan",
    "📊 Distribusi Kuintil",
    "👥 Demografi",
    "🎯 Target SDG 10",
    "🟫 Sampel Data Bronze",
    "🔗 Integrasi & Lineage Data",
])

with tab1:
    render_tab_inequality(f_gini, f_quintile)

with tab2:
    render_tab_quintile(f_quintile)

with tab3:
    render_tab_demographics(f_sex, f_emp, f_edu, f_age)

with tab4:
    render_sdg_indicators(f_gini, f_quintile)

with tab5:
    render_bronze_sample()

with tab6:
    render_data_lineage()