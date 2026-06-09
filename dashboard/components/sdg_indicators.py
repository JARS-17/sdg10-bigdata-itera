import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def render_sdg_indicators(gini_df: pd.DataFrame, quintile_df: pd.DataFrame):
    st.header("🎯 Target SDG 10: Mengurangi Ketimpangan")
    st.markdown("""
    Sesuai dengan target **SDG 10**, dashboard ini melacak dua indikator kunci secara terintegrasi untuk Brazil dan Mexico:
    1. **Indikator 10.1.1 (Shared Prosperity Premium):** Tingkat pertumbuhan pendapatan dari 40% populasi terbawah dibandingkan dengan rata-rata nasional (karena data deret waktu terbatas pada tahun 2010, kami membandingkan proporsi pendapatan dan tingkat pertumbuhan lintas kelompok).
    2. **Indikator 10.2.1:** Proporsi populasi yang hidup di bawah 50% dari median pendapatan nasional (Garis Kemiskinan Relatif).
    """)
    
    st.divider()
    
    # -------------------------------------------------------------------------
    # 1. SDG 10.2.1: Proporsi di bawah 50% Median Income
    # -------------------------------------------------------------------------
    st.subheader("Indikator 10.2.1: Proporsi Populasi di Bawah 50% Median Pendapatan")
    st.caption("Indikator ini mengukur kemiskinan relatif. Semakin tinggi persentasenya, semakin besar kelompok masyarakat yang tertinggal dari standar hidup median nasional.")

    if "sdg_10_2_1" in gini_df.columns:
        # Tampilkan visualisasi perbandingan
        fig_1021 = px.bar(
            gini_df,
            x="country_name",
            y="sdg_10_2_1",
            color="country_name",
            text="sdg_10_2_1",
            title="Proporsi Populasi di Bawah 50% Median Pendapatan (2010)",
            labels={"country_name": "Negara", "sdg_10_2_1": "Proporsi Populasi (<50% Median)"},
            color_discrete_map={"Brazil 🇧🇷": "#009C3B", "Mexico 🇲🇽": "#CE1126"}
        )
        
        # Format
        fig_1021.update_layout(
            yaxis_tickformat='.1%',
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
            yaxis=dict(gridcolor="#2a2f3e"),
            margin=dict(t=40, b=10, l=0, r=0),
            showlegend=False
        )
        fig_1021.update_traces(texttemplate="%{y:.1%}", textposition="outside")
        
        st.plotly_chart(fig_1021, use_container_width=True)
        
        # Tampilkan metrik per negara side-by-side
        st.markdown("#### 📌 Ringkasan Populasi Rentan Miskin Relatif (SDG 10.2.1)")
        met_cols = st.columns(len(gini_df))
        for j, (_, row) in enumerate(gini_df.iterrows()):
            val = float(row["sdg_10_2_1"])
            cname = row["country_name"]
            with met_cols[j]:
                st.metric(
                    label=f"{cname} (2010)", 
                    value=f"{val * 100:.2f}%",
                    help=f"Persentase penduduk di {cname} yang berpendapatan kurang dari 50% median nasional."
                )
    else:
        st.warning("⚠️ Data 'sdg_10_2_1' belum tersedia di Gold Layer.")
        
    st.divider()

    # -------------------------------------------------------------------------
    # 2. Shared Prosperity (Proporsi Pendapatan Bottom 40%)
    # -------------------------------------------------------------------------
    st.subheader("Shared Prosperity (Target 10.1)")
    st.caption("Shared Prosperity berfokus pada peningkatan pendapatan dari kelompok 40% terbawah (Bottom 40%) populasi.")
    
    # Filter bottom 40 (Q1 & Q2)
    bottom40_df = quintile_df[quintile_df["quantile"].isin([1, 2])].copy()
    
    # Defensive programming: pastikan kolom country_name ada
    if "country_name" not in bottom40_df.columns:
        COUNTRY_MAP_LOCAL = {76: "Brazil 🇧🇷", 484: "Mexico 🇲🇽"}
        bottom40_df["country_name"] = bottom40_df["country"].map(COUNTRY_MAP_LOCAL).fillna(bottom40_df["country"].astype(str))
        
    # Hitung total share bottom 40 per negara
    b40_shares = bottom40_df.groupby(["country", "country_name", "year"])["income_share"].sum().reset_index()
    b40_shares["income_share_pct"] = b40_shares["income_share"] * 100
    
    # Tampilkan perbandingan share pendapatan Bottom 40% vs Top 10%
    st.markdown("#### 📊 Penguasaan Pendapatan: Bottom 40% vs Top 10% (Palma Components)")
    
    # Dapatkan Top 10% share (Q5 share, or we can approximate from Palma and Bottom 40)
    # Di gold_quintile, kuintil 5 adalah top 20%. Let's query from quintile_df
    q5_df = quintile_df[quintile_df["quantile"] == 5].copy()
    if "country_name" not in q5_df.columns:
        COUNTRY_MAP_LOCAL = {76: "Brazil 🇧🇷", 484: "Mexico 🇲🇽"}
        q5_df["country_name"] = q5_df["country"].map(COUNTRY_MAP_LOCAL).fillna(q5_df["country"].astype(str))
    q5_df.rename(columns={"income_share": "top20_share"}, inplace=True)
    
    comp_data = []
    for _, row in b40_shares.iterrows():
        c = row["country"]
        b40_val = row["income_share_pct"]
        # Find Q5 share
        q5_row = q5_df[q5_df["country"] == c]
        q5_val = q5_row["top20_share"].values[0] * 100 if not q5_row.empty else 0.0
        
        comp_data.append({
            "Negara": row["country_name"],
            "Kelompok": "Bottom 40% (Q1+Q2)",
            "Share Pendapatan (%)": b40_val
        })
        comp_data.append({
            "Negara": row["country_name"],
            "Kelompok": "Top 20% (Q5)",
            "Share Pendapatan (%)": q5_val
        })
        
    df_comp = pd.DataFrame(comp_data)
    
    fig_sp = px.bar(
        df_comp,
        x="Negara",
        y="Share Pendapatan (%)",
        color="Kelompok",
        barmode="group",
        text="Share Pendapatan (%)",
        color_discrete_map={"Bottom 40% (Q1+Q2)": "#4cb2a2", "Top 20% (Q5)": "#ee5253"}
    )
    fig_sp.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
    fig_sp.update_layout(
        height=350,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0",
        yaxis=dict(gridcolor="#2a2f3e"),
        margin=dict(t=40, b=10, l=0, r=0)
    )
    st.plotly_chart(fig_sp, use_container_width=True)
    
    # Info Box
    st.info(
        "💡 **Shared Prosperity** tercapai jika pendapatan Bottom 40% tumbuh lebih cepat daripada rata-rata nasional. "
        "Grafik di atas membandingkan porsi pendapatan yang dikuasai oleh 40% penduduk terbawah dengan 20% teratas. "
        "Terlihat bahwa di kedua negara, kelompok 20% teratas menguasai lebih dari setengah total pendapatan nasional, "
        "menunjukkan ketimpangan struktural yang tinggi."
    )
