# ==============================================================================
# income_dist.py — Komponen distribusi & Lorenz Curve
# ==============================================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np


def render_income_distribution(df: pd.DataFrame) -> None:
    """Render visualisasi distribusi pendapatan dan Lorenz Curve."""
    st.subheader("📉 Tren Metrik Ketimpangan")

    if df.empty:
        st.warning("Tidak ada data untuk ditampilkan.")
        return

    # ── Multi-line chart: Gini, Theil, Palma ──────────────────────────────────
    fig = go.Figure()

    metrics = [
        ("gini",  "Gini Coefficient",  "#4f8ef7"),
        ("theil", "Theil Index",        "#f7934f"),
        ("palma", "Palma Ratio",        "#69db7c"),
    ]

    for col, name, color in metrics:
        if col in df.columns:
            # Normalisasi ke 0-1 untuk perbandingan visual
            vals = df[col].values
            norm_vals = (vals - vals.min()) / (vals.max() - vals.min() + 1e-10)
            fig.add_trace(go.Scatter(
                x=df["year"], y=norm_vals,
                mode="lines+markers",
                name=f"{name} (normalized)",
                line=dict(color=color, width=2),
                marker=dict(size=6, color=color),
                hovertemplate=f"<b>{name}</b><br>Tahun: %{{x}}<br>Nilai (norm): %{{y:.4f}}<extra></extra>",
            ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(14,17,23,0.8)",
        xaxis=dict(title="Tahun", gridcolor="#1e2535"),
        yaxis=dict(title="Nilai Ternormalisasi (0–1)", gridcolor="#1e2535"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Interpretasi ───────────────────────────────────────────────────────────
    st.info("""
    **Catatan Interpretasi:**
    - **Gini Coefficient**: 0 = distribusi merata sempurna, 1 = sangat timpang
    - **Theil Index**: 0 = merata sempurna, nilai lebih besar = lebih timpang
    - **Palma Ratio**: Rasio pendapatan 10% teratas terhadap 40% terbawah. Nilai > 1 menunjukkan ketimpangan
    - Semua metrik **ternormalisasi (0–1)** pada grafik ini untuk memudahkan perbandingan visual
    """)
