import streamlit as st
import pandas as pd
from pathlib import Path
from config import BRONZE_DIR, BRONZE_FILE

def render_bronze_sample():
    st.header("🟫 Sampel Data Raw (Bronze Layer)")
    st.markdown("""
    Menampilkan **100 data sampel pertama** dari data mentah (Bronze Layer) untuk masing-masing negara sebelum filter usia (18-65 tahun) atau pembersihan nilai pendapatan dilakukan.
    """)
    
    st.divider()
    
    # Path folder partisi di dalam container
    bronze_base = BRONZE_DIR / BRONZE_FILE
    
    @st.cache_data(ttl=3600, show_spinner="Memuat sampel data Bronze…")
    def load_sample(country_code):
        partition_folder = bronze_base / f"COUNTRY={country_code}/YEAR=2010"
        if not partition_folder.exists():
            return pd.DataFrame()
            
        # Cari part file parquet pertama di folder partisi
        part_files = list(partition_folder.glob("part-*.parquet"))
        if not part_files:
            return pd.DataFrame()
            
        # Baca part file pertama saja (aman dari OOM karena ukurannya kecil ~10MB)
        df = pd.read_parquet(part_files[0]).head(100)
        
        # Tambahkan kembali kolom partisi yang hilang saat membaca file partisi secara langsung
        df.insert(0, "COUNTRY", country_code)
        df.insert(1, "YEAR", 2010)
        return df

    # Pilih Negara
    country_choice = st.radio(
        "Pilih Sampel Negara dari Bronze Layer:",
        options=["Brazil 🇧🇷 (Country 76)", "Mexico 🇲🇽 (Country 484)"],
        horizontal=True
    )
    
    country_code = 76 if "Brazil" in country_choice else 484
    
    try:
        df_sample = load_sample(country_code)
        if df_sample.empty:
            st.warning("⚠️ File sampel Bronze layer tidak ditemukan.")
        else:
            st.markdown(f"#### 📋 100 Baris Pertama - {'Brazil 🇧🇷' if country_code == 76 else 'Mexico 🇲🇽'} (Bronze)")
            st.caption(f"Tabel ini berisi {len(df_sample.columns)} kolom mentah asli hasil ekstraksi IPUMS.")
            
            # Format display agar angka tidak berformat ribuan untuk ID seperti SERIAL, PERNUM
            st.dataframe(
                df_sample, 
                use_container_width=True, 
                hide_index=True
            )
            
            # Catatan kolom
            with st.expander("🔍 Penjelasan Kolom Mentah (Bronze)"):
                st.markdown("""
                * **COUNTRY:** Kode negara (76 = Brazil, 484 = Mexico)
                * **YEAR:** Tahun sensus (2010)
                * **SERIAL:** Nomor seri rumah tangga
                * **PERNUM:** Nomor urut individu dalam rumah tangga
                * **PERWT:** Bobot survei individu (Person Weight)
                * **INCTOT:** Pendapatan total pribadi (Brazil menggunakan ini, Mexico bernilai Null)
                * **INCEARN:** Pendapatan dari pekerjaan (Mexico menggunakan ini)
                * **EDATTAIN:** Tingkat pencapaian pendidikan (kode mentah)
                * **EMPSTAT:** Status ketenagakerjaan (kode mentah)
                * **OCCISCO / INDGEN:** Kode pekerjaan dan sektor industri standar internasional
                """)
    except Exception as e:
        st.error(f"❌ Gagal memuat data Bronze: {e}")
