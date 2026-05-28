# ==============================================================================
# gini_chart.py — Komponen chart tren Gini Coefficient
# ==============================================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def render_gini_chart(df: pd.DataFrame) -> None:
    """Render chart tren Gini Coefficient dari waktu ke waktu."""
    st.subheader("📈 Tren Gini Coefficient")

    if df.empty:
        st.warning("Tidak ada data untuk ditampilkan.")
        return

    fig = go.Figure()

    # Line Gini
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["gini"],
        mode="lines+markers",
        name="Gini Coefficient",
        line=dict(color="#4f8ef7", width=3),
        marker=dict(size=8, symbol="circle", color="#4f8ef7"),
        hovertemplate="<b>Tahun %{x}</b><br>Gini: %{y:.4f}<extra></extra>",
    ))

    # Theil index (sumbu sekunder)
    if "theil" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["year"], y=df["theil"],
            mode="lines+markers",
            name="Theil Index",
            line=dict(color="#f7934f", width=2, dash="dash"),
            marker=dict(size=6, color="#f7934f"),
            yaxis="y2",
            hovertemplate="<b>Tahun %{x}</b><br>Theil: %{y:.4f}<extra></extra>",
        ))

    # Referensi WHO / World Bank (Gini 0.4 = "high inequality")
    fig.add_hline(
        y=0.4, line_dash="dot", line_color="#ff4b4b",
        annotation_text="High Inequality Threshold (0.40)",
        annotation_position="top right"
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(14,17,23,0.8)",
        xaxis=dict(title="Tahun", gridcolor="#1e2535"),
        yaxis=dict(title="Gini Coefficient", range=[0, 1], gridcolor="#1e2535"),
        yaxis2=dict(
            title="Theil Index",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=450,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Statistik ringkas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Gini Tertinggi",  f"{df['gini'].max():.4f}", f"({int(df.loc[df['gini'].idxmax(), 'year'])})")
    with col2:
        st.metric("Gini Terendah", f"{df['gini'].min():.4f}", f"({int(df.loc[df['gini'].idxmin(), 'year'])})")
    with col3:
        delta = df['gini'].iloc[-1] - df['gini'].iloc[0] if len(df) > 1 else 0
        st.metric("Perubahan Keseluruhan", f"{delta:+.4f}")
