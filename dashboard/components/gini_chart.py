import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def render_gini_chart(gini_row: pd.Series) -> None:
    """
    Render visualisasi ketimpangan pendapatan berdasarkan satu baris data Gini.

    Parameters
    ----------
    gini_row : pd.Series
        Satu baris dari gold_gini_by_year yang sudah difilter (satu negara, satu tahun).
    """

    # ── Ambil nilai skalar (paksa ke float agar aman dengan Plotly) ────────────
    gini_value   = float(gini_row["gini"])
    theil_value  = float(gini_row["theil"])
    palma_value  = float(gini_row["palma"])
    sdg_value    = float(gini_row["sdg_10_2_1"])
    country_name = str(gini_row["country_name"])
    year         = int(gini_row["year"])

    # ── Banner Peringatan ──────────────────────────────────────────────────────
    if gini_value > 0.5:
        st.error(
            f"🚨 **Ketimpangan Sangat Tinggi!** Gini = **{gini_value:.4f}** "
            f"(> 0.50) — {country_name} {year} membutuhkan intervensi kebijakan segera."
        )
    elif gini_value > 0.4:
        st.warning(
            f"⚠️ **Ketimpangan Tinggi.** Gini = **{gini_value:.4f}** "
            f"(> 0.40) — {country_name} {year} belum memenuhi standar SDG 10."
        )
    else:
        st.success(
            f"✅ Gini = **{gini_value:.4f}** — Ketimpangan moderat/rendah."
        )

    # ── Baris 1: Gauge + Bar Aktual vs Target ─────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🎯 Gini Gauge Chart")

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=gini_value,
            delta={"reference": 0.30, "increasing": {"color": "#ee5253"}, "decreasing": {"color": "#4cb2a2"}},
            title={"text": f"Gini Coefficient<br><span style='font-size:0.85em;color:gray'>{country_name} {year}</span>"},
            gauge={
                "axis": {"range": [0, 1], "tickwidth": 1, "tickcolor": "#8892a4"},
                "bar": {"color": "#4f8ef7", "thickness": 0.3},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0.00, 0.30], "color": "#2d6a4f"},
                    {"range": [0.30, 0.40], "color": "#74c69d"},
                    {"range": [0.40, 0.55], "color": "#f4a261"},
                    {"range": [0.55, 1.00], "color": "#e63946"},
                ],
                "threshold": {
                    "line": {"color": "white", "width": 3},
                    "thickness": 0.75,
                    "value": 0.30,
                },
            },
            number={"font": {"size": 36, "color": "#e2e8f0"}, "suffix": ""},
        ))
        fig_gauge.update_layout(
            height=300,
            margin=dict(t=60, b=20, l=30, r=30),
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col2:
        st.markdown("#### 📊 Aktual vs Target SDG 10")

        target_gini = 0.30
        df_target = pd.DataFrame({
            "Kategori": ["Aktual", "Target SDG"],
            "Nilai Gini": [round(gini_value, 4), target_gini],
            "Warna": ["#ff9f43", "#4cb2a2"],
        })

        fig_bar = px.bar(
            df_target,
            x="Kategori",
            y="Nilai Gini",
            color="Kategori",
            color_discrete_map={"Aktual": "#ff9f43", "Target SDG": "#4cb2a2"},
            text="Nilai Gini",
        )
        fig_bar.update_traces(texttemplate="%{text:.4f}", textposition="outside", textfont_color="#e2e8f0")
        fig_bar.update_layout(
            height=300,
            margin=dict(t=10, b=10, l=0, r=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            yaxis=dict(range=[0, max(gini_value, target_gini) * 1.25], gridcolor="#2a2f3e"),
            xaxis=dict(gridcolor="#2a2f3e"),
            font_color="#e2e8f0",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Baris 2: Metrik Tambahan ───────────────────────────────────────────────
    st.markdown("#### 📈 Metrik Ketimpangan Lainnya")
    m1, m2, m3 = st.columns(3)

    with m1:
        st.metric(
            "Theil Index",
            f"{theil_value:.4f}",
            help="Generalized Entropy GE(1). Semakin tinggi = semakin tidak merata.",
        )
    with m2:
        st.metric(
            "Palma Ratio",
            f"{palma_value:.2f}×",
            help="Rasio pendapatan 10% teratas dibanding 40% terbawah.",
        )
    with m3:
        st.metric(
            "SDG 10.2.1 — Penduduk < 50% Median",
            f"{sdg_value * 100:.2f}%",
            help="Proporsi penduduk dengan pendapatan di bawah 50% median nasional.",
        )