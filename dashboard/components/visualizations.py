import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ── Mapping Label ──────────────────────────────────────────────────────────────
COUNTRY_MAP  = {76: "Brazil 🇧🇷", 484: "Mexico 🇲🇽"}
EMPSTAT_MAP  = {1: "Bekerja", 2: "Pengangguran", 3: "Tidak Aktif"}
EDATTAIN_MAP = {1: "Tdk Tamat SD", 2: "SD/Sederajat", 3: "SMA/Sederajat", 4: "Perguruan Tinggi"}

OCCISCO_MAP = {
    1: "Manajer", 2: "Profesional", 3: "Teknisi", 4: "Klerikal",
    5: "Jasa/Penjualan", 6: "Pertanian", 7: "Kerajinan",
    8: "Operator Mesin", 9: "Pekerja Kasar", 10: "Militer",
    11: "Tidak Diidentifikasi", 99: "Tidak Bekerja"
}

INDGEN_MAP = {
    100: "Pertanian", 200: "Pertambangan", 300: "Manufaktur",
    400: "Utilitas", 500: "Konstruksi", 600: "Perdagangan",
    700: "Transportasi", 800: "Keuangan", 900: "Jasa Bisnis",
    1000: "Jasa Publik", 1100: "Pendidikan/Kesehatan",
    1200: "Jasa Lainnya", 1300: "Rumah Tangga", 9990: "Tidak Bekerja"
}

PALETTE_BRAZIL = "#009C3B"
PALETTE_MEXICO = "#CE1126"
PALETTE_BOTH   = ["#009C3B", "#CE1126"]

COLOR_SCALE = [
    [0.0,  "#2d6a4f"],
    [0.25, "#74c69d"],
    [0.5,  "#e9c46a"],
    [0.75, "#f4a261"],
    [1.0,  "#e63946"],
]


def _country_color(country_code: int) -> str:
    return PALETTE_BRAZIL if country_code == 76 else PALETTE_MEXICO


# ── Tab 1: Ketimpangan Pendapatan ──────────────────────────────────────────────
def render_tab_inequality(gini_df: pd.DataFrame, quintile_df: pd.DataFrame) -> None:
    """Visualisasi utama ketimpangan: perbandingan Brazil vs Mexico."""

    st.subheader("📉 Perbandingan Ketimpangan Pendapatan")

    if gini_df.empty:
        st.warning("Data ketimpangan tidak tersedia.")
        return

    # ── Banner Status per Negara ──────────────────────────────────────────────
    cols = st.columns(len(gini_df))
    for i, (_, row) in enumerate(gini_df.iterrows()):
        g = float(row["gini"])
        name = str(row["country_name"])
        with cols[i]:
            if g > 0.50:
                st.error(f"🚨 {name}\nGini = **{g:.4f}**\n(Sangat Tinggi)")
            elif g > 0.40:
                st.warning(f"⚠️ {name}\nGini = **{g:.4f}**\n(Tinggi)")
            else:
                st.success(f"✅ {name}\nGini = **{g:.4f}**\n(Moderat)")

    st.divider()

    # ── Baris 1: Gauge per negara ─────────────────────────────────────────────
    gauge_cols = st.columns(len(gini_df))
    for i, (_, row) in enumerate(gini_df.iterrows()):
        with gauge_cols[i]:
            g = float(row["gini"])
            name = str(row["country_name"])
            clr = _country_color(int(row["country"]))

            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=g,
                delta={"reference": 0.30, "increasing": {"color": "#e63946"},
                       "decreasing": {"color": "#4cb2a2"}},
                title={"text": f"<b>{name}</b><br><span style='font-size:0.8em;color:gray'>"
                               f"Tahun {int(row['year'])}</span>"},
                gauge={
                    "axis": {"range": [0, 1]},
                    "bar":  {"color": clr, "thickness": 0.3},
                    "steps": [
                        {"range": [0.00, 0.30], "color": "#1b4332"},
                        {"range": [0.30, 0.40], "color": "#52b788"},
                        {"range": [0.40, 0.55], "color": "#f4a261"},
                        {"range": [0.55, 1.00], "color": "#9d0208"},
                    ],
                    "threshold": {"line": {"color": "white", "width": 3},
                                  "thickness": 0.75, "value": 0.30},
                },
                number={"font": {"size": 38}},
            ))
            fig.update_layout(height=280, margin=dict(t=80, b=10, l=20, r=20),
                              paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
            st.plotly_chart(fig, use_container_width=True)

    # ── Baris 2: Metrik Tabel ─────────────────────────────────────────────────
    st.markdown("#### 📊 Tabel Metrik Ketimpangan")

    metric_df = gini_df[["country_name", "year", "gini", "theil", "palma",
                          "sdg_10_2_1", "mean_income", "mean_b40", "n_obs"]].copy()
    metric_df.columns = ["Negara", "Tahun", "Gini", "Theil", "Palma Ratio",
                         "SDG 10.2.1 (%)", "Mean Pendapatan", "Mean B40%", "Obs"]
    metric_df["Gini"]          = metric_df["Gini"].apply(lambda x: f"{float(x):.4f}")
    metric_df["Theil"]         = metric_df["Theil"].apply(lambda x: f"{float(x):.4f}")
    metric_df["Palma Ratio"]   = metric_df["Palma Ratio"].apply(lambda x: f"{float(x):.2f}×")
    metric_df["SDG 10.2.1 (%)"]= metric_df["SDG 10.2.1 (%)"].apply(lambda x: f"{float(x)*100:.1f}%")
    metric_df["Mean Pendapatan"]= metric_df["Mean Pendapatan"].apply(lambda x: f"{float(x):,.0f}")
    metric_df["Mean B40%"]     = metric_df["Mean B40%"].apply(lambda x: f"{float(x):,.0f}")
    metric_df["Obs"]           = metric_df["Obs"].apply(lambda x: f"{int(x):,}")
    st.dataframe(metric_df, use_container_width=True, hide_index=True)

    st.divider()

    # ── Baris 3: Bar Komparasi Semua Metrik ───────────────────────────────────
    st.markdown("#### 🏆 Perbandingan Semua Metrik (Brazil vs Mexico)")

    metrics = ["gini", "theil", "palma", "sdg_10_2_1"]
    labels  = ["Gini Coefficient", "Theil Index", "Palma Ratio", "SDG 10.2.1"]
    fig_comp = make_subplots(rows=1, cols=4, subplot_titles=labels)

    for j, (m, lbl) in enumerate(zip(metrics, labels), 1):
        for _, row in gini_df.iterrows():
            fig_comp.add_trace(
                go.Bar(
                    name=str(row["country_name"]),
                    x=[str(row["country_name"])],
                    y=[float(row[m])],
                    marker_color=_country_color(int(row["country"])),
                    showlegend=(j == 1),
                    text=[f"{float(row[m]):.3f}"],
                    textposition="outside",
                ),
                row=1, col=j,
            )

    fig_comp.update_layout(
        height=320, barmode="group",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        margin=dict(t=40, b=40, l=0, r=0),
    )
    fig_comp.update_yaxes(gridcolor="#2a2f3e")
    st.plotly_chart(fig_comp, use_container_width=True)

    # ── Target SDG ────────────────────────────────────────────────────────────
    st.markdown("#### 🎯 Nilai Aktual vs Target SDG 10 (Gini ≤ 0.30)")
    target = 0.30
    rows_target = []
    for _, row in gini_df.iterrows():
        g = float(row["gini"])
        rows_target.append({
            "Negara": str(row["country_name"]),
            "Nilai": g,
            "Tipe": "Aktual",
            "Gap": round(g - target, 4)
        })
        rows_target.append({"Negara": str(row["country_name"]), "Nilai": target, "Tipe": "Target SDG"})

    df_t = pd.DataFrame(rows_target)
    fig_t = px.bar(df_t, x="Negara", y="Nilai", color="Tipe", barmode="group",
                   color_discrete_map={"Aktual": "#ff9f43", "Target SDG": "#4cb2a2"},
                   text="Nilai")
    fig_t.update_traces(texttemplate="%{text:.4f}", textposition="outside")
    fig_t.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
                        yaxis=dict(gridcolor="#2a2f3e"),
                        margin=dict(t=10, b=10, l=0, r=0))
    st.plotly_chart(fig_t, use_container_width=True)

    st.divider()

    # ── Lorenz Curve ──────────────────────────────────────────────────────────
    st.markdown("#### 📈 Kurva Lorenz (Lorenz Curve)")
    st.caption("Kurva Lorenz menunjukkan proporsi kumulatif pendapatan nasional yang dikuasai oleh persentase kumulatif populasi. Garis diagonal abu-abu mewakili pemerataan sempurna.")

    fig_lorenz = go.Figure()
    
    # Tambah garis pemerataan sempurna (Line of Perfect Equality)
    fig_lorenz.add_trace(go.Scatter(
        x=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
        y=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
        mode="lines",
        name="Pemerataan Sempurna (Garis 45°)",
        line=dict(color="#8892a4", dash="dash", width=2)
    ))
    
    # Hitung dan plot kurva Lorenz per negara yang ada di quintile_df
    for country in sorted(quintile_df["country"].unique()):
        sub = quintile_df[quintile_df["country"] == country].sort_values("quantile")
        if sub.empty:
            continue
            
        cname = COUNTRY_MAP.get(country, str(country))
        clr = _country_color(int(country))
        
        # Kumulatif share pendapatan
        shares = [0.0] + sub["income_share"].cumsum().tolist()
        pop_cum = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        
        fig_lorenz.add_trace(go.Scatter(
            x=pop_cum,
            y=shares,
            mode="lines+markers",
            name=cname,
            line=dict(color=clr, width=3),
            marker=dict(size=6)
        ))
        
    fig_lorenz.update_layout(
        height=400,
        xaxis_title="Kumulatif Populasi",
        yaxis_title="Kumulatif Share Pendapatan",
        xaxis=dict(gridcolor="#2a2f3e", tickformat=".0%"),
        yaxis=dict(gridcolor="#2a2f3e", tickformat=".0%"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        margin=dict(t=20, b=40, l=0, r=0)
    )
    st.plotly_chart(fig_lorenz, use_container_width=True)


# ── Tab 2: Distribusi Kuintil ──────────────────────────────────────────────────
def render_tab_quintile(quintile_df: pd.DataFrame) -> None:
    st.subheader("📊 Distribusi Kuintil Pendapatan")

    if quintile_df.empty:
        st.warning("Data kuintil tidak tersedia.")
        return

    COUNTRY_MAP_SHORT = {76: "Brazil 🇧🇷", 484: "Mexico 🇲🇽"}
    quintile_df = quintile_df.sort_values(["country", "quantile"]).copy()
    quintile_df["country_name"] = quintile_df["country"].map(COUNTRY_MAP_SHORT).fillna(quintile_df["country"].astype(str))

    q_label = {1: "Q1 (20% Termiskin)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (20% Terkaya)"}
    quintile_df["q_label"] = quintile_df["quantile"].map(q_label)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 💰 Rata-rata Pendapatan per Kuintil")
        fig_bar = px.bar(
            quintile_df, x="q_label", y="mean_income",
            color="country_name", barmode="group",
            labels={"q_label": "Kuintil", "mean_income": "Rata-rata Pendapatan",
                    "country_name": "Negara"},
            color_discrete_map={"Brazil 🇧🇷": PALETTE_BRAZIL, "Mexico 🇲🇽": PALETTE_MEXICO},
            text="mean_income",
        )
        fig_bar.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig_bar.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
                              yaxis=dict(gridcolor="#2a2f3e"), margin=dict(t=10, b=10, l=0, r=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.markdown("#### 🥧 Share Pendapatan per Kuintil")
        fig_pie = make_subplots(
            rows=1, cols=len(quintile_df["country"].unique()),
            specs=[[{"type": "pie"}] * len(quintile_df["country"].unique())],
            subplot_titles=[COUNTRY_MAP_SHORT.get(c, str(c))
                            for c in sorted(quintile_df["country"].unique())]
        )
        for j, country in enumerate(sorted(quintile_df["country"].unique()), 1):
            sub = quintile_df[quintile_df["country"] == country]
            fig_pie.add_trace(
                go.Pie(labels=sub["q_label"], values=sub["income_share"],
                       hole=0.4, name=COUNTRY_MAP_SHORT.get(country, str(country)),
                       marker_colors=["#e63946", "#f4a261", "#e9c46a", "#74c69d", "#4f8ef7"],
                       textinfo="percent", showlegend=(j == 1)),
                row=1, col=j
            )
        fig_pie.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)",
                              font_color="#e2e8f0", margin=dict(t=40, b=10, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Tabel Detail ──────────────────────────────────────────────────────────
    st.markdown("#### 📋 Tabel Rincian per Kuintil")
    disp = quintile_df[["country_name", "q_label", "lower_bound", "upper_bound",
                         "mean_income", "income_share"]].copy()
    disp["mean_income"]   = disp["mean_income"].apply(lambda x: f"{float(x):,.2f}")
    disp["income_share"]  = disp["income_share"].apply(lambda x: f"{float(x)*100:.2f}%")
    disp["lower_bound"]   = disp["lower_bound"].apply(lambda x: f"{float(x):,.0f}")
    disp["upper_bound"]   = disp["upper_bound"].apply(lambda x: f"{float(x):,.0f}")
    disp.columns = ["Negara", "Kuintil", "Batas Bawah", "Batas Atas",
                    "Rata-rata Pendapatan", "Share Pendapatan"]
    st.dataframe(disp, use_container_width=True, hide_index=True)

    # ── Insight ───────────────────────────────────────────────────────────────
    for country in sorted(quintile_df["country"].unique()):
        sub = quintile_df[quintile_df["country"] == country]
        q1 = sub[sub["quantile"] == 1]["income_share"].values
        q5 = sub[sub["quantile"] == 5]["income_share"].values
        if len(q1) and len(q5) and float(q1[0]) > 0:
            ratio = float(q5[0]) / float(q1[0])
            cname = COUNTRY_MAP_SHORT.get(country, str(country))
            st.info(f"💡 **{cname}:** Kuintil Q5 menguasai **{float(q5[0])*100:.1f}%** "
                    f"vs Q1 hanya **{float(q1[0])*100:.1f}%** — rasio **{ratio:.1f}×**")


# ── Tab 3: Demografi ───────────────────────────────────────────────────────────
def render_tab_demographics(sex_df: pd.DataFrame, emp_df: pd.DataFrame,
                             edu_df: pd.DataFrame, age_df: pd.DataFrame) -> None:
    st.subheader("👥 Analisis Demografi")

    COUNTRY_MAP_SHORT = {76: "Brazil 🇧🇷", 484: "Mexico 🇲🇽"}

    for df in [sex_df, emp_df, edu_df, age_df]:
        if "country_name" not in df.columns and "COUNTRY" in df.columns:
            df["country_name"] = df["COUNTRY"].map(COUNTRY_MAP_SHORT).fillna(df["COUNTRY"].astype(str))

    # ── Baris 1: Jenis Kelamin + Ketenagakerjaan ──────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🚻 Distribusi Jenis Kelamin")
        if not sex_df.empty:
            fig = px.pie(sex_df, values="weighted_count", names="sex_label",
                         facet_col="country_name", hole=0.45,
                         color_discrete_sequence=["#4f8ef7", "#ff9f43"])
            fig.update_traces(textinfo="percent+label")
            fig.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)",
                              font_color="#e2e8f0", margin=dict(t=40, b=0, l=0, r=0),
                              showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 💼 Status Ketenagakerjaan")
        if not emp_df.empty:
            fig = px.bar(emp_df, x="country_name", y="weighted_count",
                         color="empstat_label", barmode="stack",
                         labels={"country_name": "Negara", "weighted_count": "Populasi Tertimbang",
                                 "empstat_label": "Status"},
                         color_discrete_sequence=["#4cb2a2", "#ee5253", "#f4a261"])
            fig.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
                              yaxis=dict(gridcolor="#2a2f3e"),
                              margin=dict(t=10, b=10, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

    # ── Baris 2: Pendidikan + Usia ────────────────────────────────────────────
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### 🎓 Tingkat Pendidikan")
        if not edu_df.empty:
            edu_order = ["Tdk Tamat SD", "SD/Sederajat", "SMA/Sederajat", "Perguruan Tinggi", "Lainnya"]
            edu_df["education_label"] = pd.Categorical(
                edu_df["education_label"], categories=edu_order, ordered=True)
            edu_sorted = edu_df.sort_values("education_label")
            fig = px.bar(edu_sorted, x="weighted_count", y="education_label",
                         color="country_name", orientation="h", barmode="group",
                         labels={"education_label": "Pendidikan",
                                 "weighted_count": "Populasi Tertimbang",
                                 "country_name": "Negara"},
                         color_discrete_map={"Brazil 🇧🇷": PALETTE_BRAZIL,
                                             "Mexico 🇲🇽": PALETTE_MEXICO})
            fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
                              xaxis=dict(gridcolor="#2a2f3e"),
                              margin=dict(t=10, b=10, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown("#### 📅 Distribusi Kelompok Usia")
        if not age_df.empty:
            age_order = ["10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
            age_df["age_group"] = pd.Categorical(
                age_df["age_group"], categories=age_order, ordered=True)
            age_sorted = age_df.sort_values("age_group")
            fig = px.bar(age_sorted, x="age_group", y="weighted_count",
                         color="country_name", barmode="group",
                         labels={"age_group": "Kelompok Usia",
                                 "weighted_count": "Populasi Tertimbang",
                                 "country_name": "Negara"},
                         color_discrete_map={"Brazil 🇧🇷": PALETTE_BRAZIL,
                                             "Mexico 🇲🇽": PALETTE_MEXICO})
            fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
                              yaxis=dict(gridcolor="#2a2f3e"),
                              margin=dict(t=10, b=10, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
