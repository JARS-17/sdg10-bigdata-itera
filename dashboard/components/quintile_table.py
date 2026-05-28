# ==============================================================================
# quintile_table.py — Komponen tabel & chart distribusi quintile
# ==============================================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render_quintile_table(df: pd.DataFrame) -> None:
    """Render tabel distribusi quintile dan chart stacked bar."""
    st.subheader("📊 Distribusi Pendapatan per Quintile")

    if df.empty:
        st.warning("Tidak ada data untuk ditampilkan.")
        return

    # Pivot untuk chart
    pivot = df.pivot_table(
        index="year", columns="quantile", values="income_share", aggfunc="mean"
    )
    pivot.columns = [f"Q{int(c)}" for c in pivot.columns]
    pivot = pivot.reset_index()

    # ── Stacked Bar Chart ──────────────────────────────────────────────────────
    colors = ["#ff6b6b", "#ffa94d", "#ffd43b", "#69db7c", "#4dabf7"]
    quintile_labels = ["Q1 (Terbawah)", "Q2", "Q3", "Q4", "Q5 (Teratas)"]

    fig = go.Figure()
    for i, (q_col, label, color) in enumerate(zip(pivot.columns[1:], quintile_labels, colors)):
        if q_col in pivot.columns:
            fig.add_trace(go.Bar(
                x=pivot["year"],
                y=pivot[q_col] * 100,
                name=label,
                marker_color=color,
                hovertemplate=f"<b>{label}</b><br>Tahun: %{{x}}<br>Share: %{{y:.1f}}%<extra></extra>",
            ))

    fig.update_layout(
        barmode="stack",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(14,17,23,0.8)",
        xaxis=dict(title="Tahun", gridcolor="#1e2535"),
        yaxis=dict(title="Share Pendapatan (%)", gridcolor="#1e2535"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Tabel Detail ───────────────────────────────────────────────────────────
    st.subheader("Tabel Quintile Detail")
    latest_year = df["year"].max()
    latest_df = df[df["year"] == latest_year].copy()
    latest_df["income_share_pct"] = (latest_df["income_share"] * 100).round(2)
    latest_df["mean_income_fmt"]  = latest_df["mean_income"].apply(lambda x: f"${x:,.0f}")

    display_cols = {
        "quantile":        "Quintile",
        "lower_bound":     "Batas Bawah",
        "upper_bound":     "Batas Atas",
        "mean_income_fmt": "Rata-rata Pendapatan",
        "income_share_pct": "Share (%)",
    }
    st.dataframe(
        latest_df[list(display_cols.keys())].rename(columns=display_cols),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"*Data untuk tahun {int(latest_year)}")
