import streamlit as st
import pandas as pd
import plotly.express as px


def render_quintile_table(df: pd.DataFrame) -> None:
    """
    Render visualisasi distribusi kuintil pendapatan.

    Parameters
    ----------
    df : pd.DataFrame
        Data dari gold_quintile_by_year yang sudah difilter per negara/tahun.
        Kolom yang diharapkan: quantile, income_share, mean_income, lower_bound, upper_bound
    """
    st.subheader("📊 Distribusi Kuintil Pendapatan")

    if df.empty:
        st.warning("Tidak ada data kuintil untuk ditampilkan.")
        return

    # Pastikan kolom income_share ada (bukan 'share')
    if "income_share" not in df.columns:
        st.error("Kolom 'income_share' tidak ditemukan di data kuintil.")
        return

    df = df.sort_values("quantile").reset_index(drop=True)

    # ── Insight Banner: rasio Q5 vs Q1 ────────────────────────────────────────
    q1_rows = df[df["quantile"] == 1]
    q5_rows = df[df["quantile"] == 5]

    if not q1_rows.empty and not q5_rows.empty:
        q1_share = float(q1_rows["income_share"].iloc[0])
        q5_share = float(q5_rows["income_share"].iloc[0])
        q1_mean  = float(q1_rows["mean_income"].iloc[0])
        q5_mean  = float(q5_rows["mean_income"].iloc[0])

        if q1_share > 0:
            ratio_share = q5_share / q1_share
            st.info(
                f"💡 **Insight Ketimpangan:** Kelompok 20% terkaya (Q5) menguasai "
                f"**{q5_share * 100:.1f}%** total pendapatan, sedangkan 20% termiskin (Q1) "
                f"hanya mendapat **{q1_share * 100:.1f}%**. "
                f"Rasio penguasaan = **{ratio_share:.1f}×** lipat."
            )
        if q1_mean > 0:
            ratio_mean = q5_mean / q1_mean
            st.warning(
                f"📉 Rata-rata pendapatan Q5 = **{q5_mean:,.0f}** vs Q1 = **{q1_mean:,.0f}** "
                f"(**{ratio_mean:.0f}× lebih besar**). Indikasi ketimpangan struktural."
            )

    # ── Kolom Grafik ──────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 💰 Rata-rata Pendapatan per Kuintil")

        label_map = {1: "Q1\n(Termiskin)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5\n(Terkaya)"}
        plot_df = df.copy()
        plot_df["label"] = plot_df["quantile"].map(label_map)

        fig_bar = px.bar(
            plot_df,
            x="label",
            y="mean_income",
            labels={"label": "Kuintil", "mean_income": "Rata-rata Pendapatan (PPP)"},
            color="mean_income",
            color_continuous_scale="Blues",
            text="mean_income",
        )
        fig_bar.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside",
            textfont_color="#e2e8f0",
        )
        fig_bar.update_layout(
            margin=dict(t=20, b=10, l=0, r=0),
            coloraxis_showscale=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
            yaxis=dict(gridcolor="#2a2f3e"),
            xaxis=dict(gridcolor="#2a2f3e"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.markdown("#### 🥧 Penguasaan (Share) Pendapatan")

        label_map_short = {1: "Q1 (20% Termiskin)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (20% Terkaya)"}
        plot_df2 = df.copy()
        plot_df2["label"] = plot_df2["quantile"].map(label_map_short)
        plot_df2["share_pct"] = (plot_df2["income_share"] * 100).round(2)

        fig_pie = px.pie(
            plot_df2,
            values="income_share",
            names="label",
            hole=0.45,
            color_discrete_sequence=["#e63946", "#f4a261", "#e9c46a", "#74c69d", "#4f8ef7"],
            custom_data=["share_pct"],
        )
        fig_pie.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Share: %{customdata[0]:.2f}%<extra></extra>",
        )
        fig_pie.update_layout(
            margin=dict(t=20, b=10, l=0, r=0),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Tabel Rinci ───────────────────────────────────────────────────────────
    st.markdown("#### 📋 Tabel Rincian Data Kuintil")

    display_df = df.copy()
    display_df["Kuintil"]              = display_df["quantile"].map(label_map_short)
    display_df["Batas Bawah"]          = display_df["lower_bound"].apply(lambda x: f"{float(x):,.0f}")
    display_df["Batas Atas"]           = display_df["upper_bound"].apply(lambda x: f"{float(x):,.0f}")
    display_df["Rata-rata Pendapatan"] = display_df["mean_income"].apply(lambda x: f"{float(x):,.2f}")
    display_df["Share Pendapatan"]     = display_df["income_share"].apply(lambda x: f"{float(x)*100:.2f}%")

    st.dataframe(
        display_df[["Kuintil", "Batas Bawah", "Batas Atas", "Rata-rata Pendapatan", "Share Pendapatan"]],
        use_container_width=True,
        hide_index=True,
    )
