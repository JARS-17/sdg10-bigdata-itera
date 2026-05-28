# SDG-10 Big Data ITS 🇮🇩

> Analisis ketimpangan pendapatan menggunakan data IPUMS dan pipeline Big Data (PySpark + Delta Lake)

## 📌 Deskripsi Proyek

Proyek ini bertujuan menganalisis **Sustainable Development Goal 10** (Berkurangnya Ketimpangan) menggunakan data IPUMS dengan pendekatan arsitektur **Medallion (Bronze → Silver → Gold)** berbasis PySpark.

## 🏗️ Arsitektur

```
Raw Data (IPUMS)
     │
     ▼
  Bronze Layer  ← Ingest & simpan as-is (Parquet)
     │
     ▼
  Silver Layer  ← Cleaning, transformasi, standarisasi
     │
     ▼
  Gold Layer    ← Agregasi, Gini, Theil, Quintile Analysis
     │
     ▼
  Dashboard (Streamlit)
```

## 📁 Struktur Folder

```
sdg10-bigdata-its/
├── data/
│   ├── raw/              ← DATA MENTAH IPUMS (tidak di-push)
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── notebooks/
├── scripts/
├── dashboard/
├── docker/
├── docs/
└── tests/
```

## 🚀 Quick Start

```bash
# 1. Clone repo
git clone <repo-url>
cd sdg10-bigdata-its

# 2. Install dependencies
pip install -r requirements.txt

# 3. Jalankan pipeline
make pipeline

# 4. Jalankan dashboard
make dashboard
```

## 📊 Metrik Ketimpangan yang Dianalisis

| Metrik | Deskripsi |
|--------|-----------|
| **Gini Coefficient** | Mengukur distribusi pendapatan (0 = merata, 1 = tidak merata) |
| **Theil Index** | Dekomposisi ketimpangan antar dan dalam kelompok |
| **Quintile Ratio** | Perbandingan pendapatan 20% teratas vs 20% terbawah |
| **Palma Ratio** | Rasio 10% teratas terhadap 40% terbawah |

## 🔧 Teknologi

- **PySpark** — Distributed data processing
- **Delta Lake** — ACID transactions & versioning
- **Streamlit** — Interactive dashboard
- **Docker** — Containerized Spark cluster
- **IPUMS** — Data sumber (CPS / IHIS)

## 👥 Tim

Proyek Big Data — Institut Teknologi Sepuluh Nopember (ITS)

## 📄 Lisensi

MIT License
