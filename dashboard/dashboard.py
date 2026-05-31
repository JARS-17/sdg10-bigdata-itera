# ==============================================================================
# dashboard.py — Streamlit Dashboard SDG-10 Ketimpangan Pendapatan
# Disesuaikan dengan data: gold_metrics_pandas.csv
# ==============================================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

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
    h1, h2, h3 { color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Data ───────────────────────────────────────────────────────────────────────
# Data Gold Layer — dari gold_metrics_pandas.csv
gold_df = pd.DataFrame([{
    "Negara": "Brazil",
    "Tahun": 2010,
    "N_individu": 1403557,
    "Median_PPP": 288.86,
    "Mean_PPP": 554.55,
    "Mean_B40": 29.63,
    "Gini": 0.6925,
    "Palma_Ratio": 25.6164,
    "Theil_T": 0.8034,
    "Anomali_B40": "Kritis",
}])

# Data Kuintil — dari bronze layer (sample 10%)
quintile_df = pd.DataFrame([
    {"Kuintil": "Q1 (0-20%)",   "Rata_rata_PPP": 185.68,  "Share_Pendapatan": 4.0},
    {"Kuintil": "Q2 (20-40%)",  "Rata_rata_PPP": 506.05,  "Share_Pendapatan": 9.0},
    {"Kuintil": "Q3 (40-60%)",  "Rata_rata_PPP": 627.62,  "Share_Pendapatan": 12.0},
    {"Kuintil": "Q4 (60-80%)",  "Rata_rata_PPP": 954.92,  "Share_Pendapatan": 18.0},
    {"Kuintil": "Q5 (80-100%)", "Rata_rata_PPP": 3460.15, "Share_Pendapatan": 57.0},
])

# Data Demografi — dari bronze layer
empstat_df = pd.DataFrame([
    {"Status": "Bekerja",      "Jumlah": 858735},
    {"Status": "Pengangguran", "Jumlah": 129526},
    {"Status": "Tidak Aktif",  "Jumlah": 754093},
])

edu_df = pd.DataFrame([
    {"Pendidikan": "Tdk Tamat SD",      "Jumlah": 761696},
    {"Pendidikan": "SD/Sederajat",      "Jumlah": 512757},
    {"Pendidikan": "SMA/Sederajat",     "Jumlah": 355679},
    {"Pendidikan": "Perguruan Tinggi",  "Jumlah": 112222},
])

age_df = pd.DataFrame([
    {"Usia": "10-19", "Jumlah": 380908},
    {"Usia": "20-29", "Jumlah": 359787},
    {"Usia": "30-39", "Jumlah": 310095},
    {"Usia": "40-49", "Jumlah": 263379},
    {"Usia": "50-59", "Jumlah": 197749},
    {"Usia": "60-69", "Jumlah": 126285},
    {"Usia": "70-79", "Jumlah": 71352},
    {"Usia": "80+",   "Jumlah": 32799},
])

row = gold_df.iloc[0]

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚖️ SDG-10 Dashboard")
    st.caption("Analisis Ketimpangan Pendapatan — IPUMS")
    st.divider()

    st.markdown("**Dataset**")
    st.info("Brazil 2010 — IPUMS International")

    st.divider()
    st.markdown("**Metrik Utama**")
    st.metric("Gini Coefficient", f"{row['Gini']:.4f}")
    st.metric("Palma Ratio", f"{row['Palma_Ratio']:.2f}x")
    st.metric("Theil Index", f"{row['Theil_T']:.4f}")
    st.metric("Total Observasi", f"{int(row['N_individu']):,}")

    st.divider()
    st.caption("📊 Institut Teknologi Sumatera")
    st.caption("Big Data Analytics — SDG Goal 10")

# ── Main Content ───────────────────────────────────────────────────────────────
st.title("📊 Analisis Ketimpangan Pendapatan (SDG Goal 10)")
st.caption("Sumber data: IPUMS International — Brazil 2010 · Gold Layer")
st.divider()

# ── KPI Row ────────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Gini Coefficient", f"{row['Gini']:.4f}",
              help="0 = merata sempurna, 1 = tidak merata sempurna. Target SDG ≤ 0.35")
with col2:
    st.metric("Theil Index", f"{row['Theil_T']:.4f}",
              help="Generalized Entropy GE(1)")
with col3:
    st.metric("Palma Ratio", f"{row['Palma_Ratio']:.2f}x",
              help="Rasio pendapatan 10% teratas vs 40% terbawah")
with col4:
    st.metric("Median PPP", f"${row['Median_PPP']:,.2f}",
              help="Median pendapatan dalam PPP 2017 Int'l $")
with col5:
    st.metric("Mean Bottom 40%", f"${row['Mean_B40']:,.2f}",
              help="Rata-rata pendapatan kelompok 40% terbawah")

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📈 Ketimpangan Pendapatan", "📊 Distribusi Kuintil", "👥 Demografi"])

# ── Tab 1: Ketimpangan ─────────────────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Gini Coefficient")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=row["Gini"],
            title={"text": "Gini Coefficient Brazil 2010"},
            gauge={
                "axis": {"range": [0, 1]},
                "bar": {"color": "#378ADD"},
                "steps": [
                    {"range": [0, 0.35], "color": "#1D9E75"},
                    {"range": [0.35, 0.5], "color": "#EF9F27"},
                    {"range": [0.5, 1.0], "color": "#E24B4A"},
                ],
                "threshold": {
                    "line": {"color": "white", "width": 3},
                    "thickness": 0.75,
                    "value": 0.35,
                },
            },
        ))
        fig.update_layout(
            height=280,
            paper_bgcolor="rgba(0,0,0,0)",
            font={"color": "#e2e8f0"},
            margin=dict(t=50, b=20, l=30, r=30),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("🟢 Rendah (≤0.35)  🟡 Sedang (0.35–0.50)  🔴 Tinggi (>0.50)")

    with col2:
        st.subheader("Perbandingan Metrik Ketimpangan")
        metrics_df = pd.DataFrame({
            "Metrik": ["Gini", "Theil Index", "Palma Ratio (÷10)"],
            "Nilai": [row["Gini"], row["Theil_T"], row["Palma_Ratio"] / 10],
            "Target SDG": [0.35, 0.30, 0.2],
        })
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name="Nilai Aktual",
            x=metrics_df["Metrik"],
            y=metrics_df["Nilai"],
            marker_color=["#E24B4A", "#E24B4A", "#E24B4A"],
            text=[f"{v:.3f}" for v in metrics_df["Nilai"]],
            textposition="outside",
        ))
        fig2.add_trace(go.Bar(
            name="Target SDG",
            x=metrics_df["Metrik"],
            y=metrics_df["Target SDG"],
            marker_color=["#1D9E75", "#1D9E75", "#1D9E75"],
            opacity=0.6,
        ))
        fig2.update_layout(
            barmode="group",
            height=280,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#e2e8f0"},
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("Ringkasan Data Gold Layer")
    st.dataframe(gold_df, use_container_width=True, hide_index=True)

    st.warning(
        f"⚠️ Gini {row['Gini']:.4f} jauh di atas target SDG-10 (≤0.35). "
        f"Palma Ratio {row['Palma_Ratio']:.1f}x mengindikasikan kelompok 10% teratas "
        f"memiliki pendapatan {row['Palma_Ratio']:.1f}x lebih besar dari 40% terbawah."
    )

# ── Tab 2: Kuintil ─────────────────────────────────────────────────────────────
with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Rata-rata Pendapatan per Kuintil")
        fig3 = go.Figure(go.Bar(
            x=quintile_df["Kuintil"],
            y=quintile_df["Rata_rata_PPP"],
            marker_color=["#B5D4F4", "#378ADD", "#185FA5", "#0C447C", "#042C53"],
            text=[f"${v:,.0f}" for v in quintile_df["Rata_rata_PPP"]],
            textposition="outside",
        ))
        fig3.update_layout(
            yaxis_title="Pendapatan Rata-rata (PPP $)",
            height=350,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#e2e8f0"},
            margin=dict(t=20, b=20, l=40, r=20),
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        st.subheader("Share Pendapatan per Kuintil")
        fig4 = go.Figure(go.Pie(
            labels=quintile_df["Kuintil"],
            values=quintile_df["Share_Pendapatan"],
            marker_colors=["#B5D4F4", "#378ADD", "#185FA5", "#0C447C", "#042C53"],
            hole=0.45,
            textinfo="label+percent",
        ))
        fig4.update_layout(
            height=350,
            paper_bgcolor="rgba(0,0,0,0)",
            font={"color": "#e2e8f0"},
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.divider()
    st.subheader("Tabel Distribusi Kuintil")
    quintile_df["Rasio vs Q1"] = (quintile_df["Rata_rata_PPP"] / quintile_df["Rata_rata_PPP"].iloc[0]).round(1).astype(str) + "x"
    st.dataframe(quintile_df, use_container_width=True, hide_index=True)

    ratio = quintile_df["Rata_rata_PPP"].iloc[-1] / quintile_df["Rata_rata_PPP"].iloc[0]
    st.info(f"📌 Kelompok Q5 (terkaya) berpenghasilan **{ratio:.1f}x** lebih besar dari Q1 (termiskin).")

# ── Tab 3: Demografi ───────────────────────────────────────────────────────────
with tab3:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Status Ketenagakerjaan")
        fig5 = go.Figure(go.Pie(
            labels=empstat_df["Status"],
            values=empstat_df["Jumlah"],
            marker_colors=["#1D9E75", "#E24B4A", "#B4B2A9"],
            hole=0.5,
            textinfo="label+percent",
        ))
        fig5.update_layout(
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            font={"color": "#e2e8f0"},
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig5, use_container_width=True)

    with col2:
        st.subheader("Tingkat Pendidikan")
        fig6 = go.Figure(go.Bar(
            x=edu_df["Pendidikan"],
            y=edu_df["Jumlah"],
            marker_color=["#AFA9EC", "#7F77DD", "#534AB7", "#26215C"],
            text=[f"{v/edu_df['Jumlah'].sum()*100:.1f}%" for v in edu_df["Jumlah"]],
            textposition="outside",
        ))
        fig6.update_layout(
            yaxis_title="Jumlah Individu",
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#e2e8f0"},
            margin=dict(t=20, b=20, l=40, r=20),
            showlegend=False,
        )
        st.plotly_chart(fig6, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Distribusi Usia")
        fig7 = go.Figure(go.Bar(
            x=age_df["Usia"],
            y=age_df["Jumlah"],
            marker_color="#9FE1CB",
            text=[f"{v/age_df['Jumlah'].sum()*100:.1f}%" for v in age_df["Jumlah"]],
            textposition="outside",
        ))
        fig7.update_layout(
            yaxis_title="Jumlah Individu",
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#e2e8f0"},
            margin=dict(t=20, b=20, l=40, r=20),
            showlegend=False,
        )
        st.plotly_chart(fig7, use_container_width=True)

    with col4:
        st.subheader("Jenis Kelamin")
        fig8 = go.Figure(go.Pie(
            labels=["Laki-laki", "Perempuan"],
            values=[859437, 882917],
            marker_colors=["#378ADD", "#F0997B"],
            hole=0.5,
            textinfo="label+percent",
        ))
        fig8.update_layout(
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            font={"color": "#e2e8f0"},
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig8, use_container_width=True)
