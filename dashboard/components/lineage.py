import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def render_data_lineage():
    st.header("🔗 Integrasi & Lineage Data (Bronze ➔ Silver ➔ Gold)")
    st.markdown("""
    Halaman ini menjelaskan bagaimana data diintegrasikan dan diproses dari data mentah survei penduduk hingga menjadi metrik ketimpangan yang siap disajikan di dashboard.
    """)
    
    st.divider()
    
    # -------------------------------------------------------------------------
    # 1. Diagram Alir Pipeline (Data Flow)
    # -------------------------------------------------------------------------
    st.subheader("🏗️ Arsitektur Medallion Lakehouse")
    
    # Render flowchart sederhana menggunakan HTML + CSS bergaya modern
    st.markdown("""
    <div style="background-color:#161b27; padding:20px; border-radius:10px; margin-bottom:20px; border:1px solid #2a2f3e;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; text-align:center;">
            <div style="flex:1; min-width:150px; padding:10px; background-color:#3e2723; border-radius:8px; border:1px solid #d84315; margin:5px;">
                <strong style="color:#ff8a65; font-size:1.1em;">🟫 Bronze Layer</strong><br>
                <span style="font-size:0.85em; color:#d7ccc8;">Raw Data Ingestion</span><br>
                <span style="font-size:0.75em; color:#b0bec5; font-family:monospace;">ipums_bronze.parquet</span><br>
                <span style="font-size:0.9em; color:#fff; font-weight:bold;">32,573,874 baris</span>
            </div>
            <div style="padding:10px; color:#8892a4; font-size:1.5em;">➔</div>
            <div style="flex:1; min-width:150px; padding:10px; background-color:#263238; border-radius:8px; border:1px solid #00acc1; margin:5px;">
                <strong style="color:#80deea; font-size:1.1em;">⬜ Silver Layer</strong><br>
                <span style="font-size:0.85em; color:#e0f7fa;">Cleaning & Harmonization</span><br>
                <span style="font-size:0.75em; color:#b0bec5; font-family:monospace;">ipums_silver.parquet</span><br>
                <span style="font-size:0.9em; color:#fff; font-weight:bold;">19,162,336 baris</span>
            </div>
            <div style="padding:10px; color:#8892a4; font-size:1.5em;">➔</div>
            <div style="flex:1; min-width:150px; padding:10px; background-color:#1b5e20; border-radius:8px; border:1px solid #4caf50; margin:5px;">
                <strong style="color:#a5d6a7; font-size:1.1em;">🟨 Gold Layer</strong><br>
                <span style="font-size:0.85em; color:#e8f5e9;">Aggregated Metrics</span><br>
                <span style="font-size:0.75em; color:#b0bec5; font-family:monospace;">gold_*.parquet</span><br>
                <span style="font-size:0.9em; color:#fff; font-weight:bold;">KPIs & Demographics</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 2. Penyelamatan Data Mexico (Harmonisasi Pendapatan)
    # -------------------------------------------------------------------------
    st.subheader("💡 Solusi Integrasi Data: Penyelamatan Data Mexico")
    st.markdown("""
    > **Masalah Awal:** Data Mexico tidak muncul di dashboard karena seluruh baris data Mexico di Silver layer hilang saat filter pendapatan diterapkan.
    > 
    > **Penyebab:** IPUMS menyimpan pendapatan untuk **Brazil** di kolom `INCTOT` (Pendapatan Total), sedangkan untuk **Mexico**, kolom `INCTOT` bernilai `NULL` (tidak diisi). Sebagai gantinya, pendapatan penduduk Mexico disimpan di kolom `INCEARN` (Pendapatan dari Pekerjaan).
    > 
    > **Solusi Integrasi:** Kami memodifikasi pipeline Silver Layer untuk melakukan **Harmonisasi Kolom Pendapatan** lintas negara:
    > - Untuk **Brazil** (Country 76): Menggunakan kolom `INCTOT` (fallback ke `INCEARN` jika null).
    > - Untuk **Mexico** (Country 484): Menggunakan kolom `INCEARN`.
    > - Kedua kolom ini digabungkan secara dinamis menjadi kolom tunggal `income_analysis` di Silver layer.
    """)

    st.divider()

    # -------------------------------------------------------------------------
    # 3. Analisis Attrition / Penyusutan Baris Data
    # -------------------------------------------------------------------------
    st.subheader("📊 Analisis Penyusutan Data (Data Attrition)")
    st.markdown("Penyusutan data terjadi karena filter usia produktif (**18–65 tahun**) serta pembersihan nilai pendapatan tidak valid (sentinel codes IPUMS `9999999`).")
    
    # Data Attrition
    attrition_data = [
        {"Negara": "Brazil 🇧🇷", "Layer": "Bronze (Raw)", "Baris": 20635472},
        {"Negara": "Brazil 🇧🇷", "Layer": "Silver (Filtered)", "Baris": 12879303},
        {"Negara": "Mexico 🇲🇽", "Layer": "Bronze (Raw)", "Baris": 11938402},
        {"Negara": "Mexico 🇲🇽", "Layer": "Silver (Filtered)", "Baris": 6283033}
    ]
    df_att = pd.DataFrame(attrition_data)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Chart perbandingan penyusutan
        fig_att = px.bar(
            df_att,
            x="Layer",
            y="Baris",
            color="Negara",
            barmode="group",
            text="Baris",
            title="Penyusutan Jumlah Baris Data (Bronze vs Silver)",
            color_discrete_map={"Brazil 🇧🇷": "#009C3B", "Mexico 🇲🇽": "#CE1126"}
        )
        fig_att.update_traces(texttemplate="%{y:,.0f}", textposition="outside")
        fig_att.update_layout(
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
            yaxis=dict(gridcolor="#2a2f3e"),
            margin=dict(t=40, b=10, l=0, r=0)
        )
        st.plotly_chart(fig_att, use_container_width=True)
        
    with col2:
        st.markdown("#### 📉 Rasio Data Lolos Filter")
        for country in ["Brazil 🇧🇷", "Mexico 🇲🇽"]:
            sub = df_att[df_att["Negara"] == country]
            raw = sub[sub["Layer"] == "Bronze (Raw)"]["Baris"].values[0]
            filt = sub[sub["Layer"] == "Silver (Filtered)"]["Baris"].values[0]
            ratio = (filt / raw) * 100
            st.metric(
                label=f"Efisiensi Data {country}",
                value=f"{ratio:.1f}%",
                delta=f"-{(100-ratio):.1f}% Excluded"
            )
            
    st.divider()
    
    # -------------------------------------------------------------------------
    # 4. Skema Kolom di Setiap Layer
    # -------------------------------------------------------------------------
    st.subheader("📋 Kamus Data Integrasi Antar Layer")
    
    schema_data = {
        "Layer": ["🟫 Bronze Layer", "⬜ Silver Layer", "🟨 Gold Layer"],
        "Deskripsi": [
            "Data mentah hasil ekstraksi dari file CSV IPUMS.",
            "Data bersih hasil filter usia produktif dan penyelarasan kolom pendapatan.",
            "Tabel agregat berisi metrik ketimpangan per negara dan tahun."
        ],
        "Kolom Penting": [
            "COUNTRY, YEAR, AGE, SEX, EDATTAIN, EMPSTAT, INCTOT, INCEARN, OCCISCO, INDGEN",
            "COUNTRY, YEAR, AGE, SEX, EDATTAIN, EMPSTAT, income_analysis, sex_label, country_name",
            "gini, theil, palma, sdg_10_2_1, quantile, lower_bound, upper_bound, mean_income, income_share"
        ],
        "Format File": ["Parquet (Partitioned by Year)", "Parquet (Partitioned by COUNTRY)", "Parquet (Flat Aggregated Tables)"]
    }
    df_schema = pd.DataFrame(schema_data)
    st.dataframe(df_schema, use_container_width=True, hide_index=True)
