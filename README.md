# SDG 10 Big Data Analytics and Medallion Architecture

<p align="center">
  <img src="https://img.shields.io/badge/Apache%20Spark-3.5-orange?style=for-the-badge&logo=apachespark&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/IPUMS-International-blue?style=for-the-badge" />
</p>

<p align="center">
  <b>Tugas Besar Analisis Big Data — Institut Teknologi Sumatera 2026</b><br>
  <i>Implementasi Medallion Architecture berbasis Apache Spark & Docker untuk Analisis Ketimpangan Pendapatan (SDG 10)</i>
</p>

---

## 📋 Daftar Isi

- [Deskripsi Proyek](#-deskripsi-proyek)
- [Anggota Tim](#-anggota-tim)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Teknologi](#-teknologi)
- [Dataset](#-dataset)
- [Cara Menjalankan](#-cara-menjalankan)
- [Struktur Folder](#-struktur-folder)
- [Pipeline Medallion](#-pipeline-medallion)
- [Dashboard Interaktif](#-dashboard-interaktif)
- [Benchmark & Evaluasi](#-benchmark--evaluasi)
- [Lisensi Data](#-lisensi-data)
- [Status Proyek](#-status-proyek)
- [Referensi](#-referensi)

---

## 🎯 Deskripsi Proyek

Proyek ini merancang dan mengimplementasikan **sistem pemrosesan data skala besar** untuk menganalisis **ketimpangan pendapatan** dalam konteks ***Sustainable Development Goal 10 (SDG 10 Reduced Inequalities)***. 

Menggunakan **Medallion Architecture** (Bronze → Silver → Gold) yang dijalankan pada **Apache Spark cluster terdistribusi** dan dikontainerisasi dengan **Docker**, sistem ini mampu memproses ratusan ribu hingga jutaan baris data mikro sensus individu secara efisien, menghasilkan metrik ketimpangan (Gini coefficient, Palma ratio, Theil index, dan *shared prosperity premium*), serta menyajikannya melalui **dashboard interaktif Streamlit**.

### Pertanyaan Ilmiah
> *Apakah arsitektur Medallion berbasis Apache Spark yang terkontainerisasi dengan Docker mampu meningkatkan throughput pemrosesan dan mengurangi latensi end-to-end pipeline untuk data mikro sensus ketimpangan pendapatan dibandingkan dengan pipeline pemrosesan sekuensial berbasis Pandas?*

---

## 👥 Anggota Tim

| No | Nama | Peran | Tanggung Jawab Utama |
|:---:|:---|:---|:---|
| 1 | **Ginda Fajar Riadi Marpaung** | 🎯 Ketua / Project Integrator | Koordinasi harian, merge kode, finalisasi proposal & presentasi, integrasi antar-modul |
| 2 | **Vany Salsabilla Putri** | 🗃️ Data Engineer | Handle data IPUMS, bangun Bronze → Silver layer, data quality & profiling |
| 3 | **Fathya Intami Gusd** | ⚡ Spark Analytics Developer | Bangun Gold layer (Gini UDF, kuintil, Theil index), optimasi query Spark |
| 4 | **Malika Azzahra Salsabila** | 📊 Baseline & Benchmark Specialist | Pipeline Pandas sekuensial, ukur throughput & latensi, bandingkan Spark vs Pandas |
| 5 | **Luthfia Laila Ramadhani** | 🖥️ Dashboard & DevOps Engineer | Setup Docker Compose (Spark + Streamlit), bangun dashboard interaktif, diagram arsitektur |

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DOCKER CONTAINER ORCHESTRATION                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐   │
│  │  Jupyter │  │  Spark   │  │  Spark   │  │  Spark   │  │Streamlit│   │
│  │ (Driver) │  │  Master  │  │ Worker 1 │  │ Worker 2 │  │Dashboard│   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘   │
│       │             │             │             │            │         │
│       └─────────────┴──────┬────┴─────────────┘            │         │
│                              ▼                               │         │
│                    ┌─────────────────┐                        │         │
│                    │  SHARED VOLUME  │                        │         │
│                    │  /data/         │                        │         │
│                    │  ├── raw/       │ ← IPUMS CSV (ignore)   │         │
│                    │  ├── bronze/    │ ← Parquet hasil ingest  │         │
│                    │  ├── silver/    │ ← Parquet hasil clean   │         │
│                    │  └── gold/      │ ← Parquet hasil agregasi│         │
│                    └─────────────────┘                        │         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    MEDALLION ARCHITECTURE PIPELINE                        │
│                                                                         │
│   [IPUMS CSV]  ──►  [BRONZE]  ──►  [SILVER]  ──►  [GOLD]  ──► [UI]   │
│       (Raw)          (Ingest)      (Transform)     (Analytics)         │
│                                                                         │
│   • Validasi skema   • Filter null   • Agregasi kuintil                │
│   • Parquet          • Deduplikasi   • Gini coefficient (UDF)          │
│   • Partisi          • Normalisasi   • Palma ratio                     │
│                        PPP            • Theil index                   │
│                                       • Shared prosperity               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Teknologi

| Kategori | Teknologi | Versi | Fungsi |
|:---|:---|:---:|:---|
| **Big Data Engine** | Apache Spark | 3.5 | Pemrosesan terdistribusi, PySpark API, Spark SQL |
| **Containerization** | Docker | Latest | Kontainerisasi Spark cluster + Jupyter + Streamlit |
| **Orchestration** | Docker Compose | Latest | Manajemen multi-container 1 perintah |
| **Bahasa** | Python | 3.11 | PySpark, Pandas, Streamlit |
| **Dashboard** | Streamlit | Latest | UI interaktif, filter, visualisasi real-time |
| **Storage Format** | Apache Parquet | — | Columnar storage, kompresi Snappy, efisiensi query |
| **Lakehouse (opsional)** | Delta Lake | Latest | ACID transactions, time travel, schema enforcement |
| **Version Control** | Git + GitHub | — | Kolaborasi tim, tracking perubahan |

---

## 📊 Dataset

| Atribut | Spesifikasi |
|:---|:---|
| **Nama** | IPUMS International (Integrated Public Use Microdata Series) |
| **Pengelola** | Minnesota Population Center, University of Minnesota |
| **Negara** | Brazil 2010, Mexico 2010 |
| **Unit Observasi** | Individu (*person records*) |
| **Estimasi Baris** | **32,257,874 baris** |
| **Ukuran File Mentah** | ~1.2 – 2.5 GB (CSV hasil ekstraksi dari .csv.gz) |
| **Variabel Inti** | `INCTOT`, `INCEARN`, `PERWT`, `AGE`, `SEX`, `EDATTAIN`, `EMPSTAT`, `OCCISCO`, `INDGEN` |
| **Lisensi** | Academic/Research Use Only dan redistribution dilarang |

> ⚠️ **Peringatan:** Data mentah IPUMS **tidak boleh di-push ke GitHub publik** sesuai ketentuan lisensi. Hanya kode pipeline, hasil agregat (Gold layer), dan dokumentasi yang dipublikasikan.

---

## 🚀 Cara Menjalankan

### Prasyarat
- Docker Desktop terinstall
- Git terinstall
- Minimal RAM 8 GB (16 GB direkomendasikan)

### 1. Clone Repository

```bash
git clone https://github.com/JARS-17/sdg10-bigdata-itera.git
cd sdg10-bigdata-itera
```

### 2. Jalankan Infrastruktur Docker

```bash
cd docker
docker-compose up -d
```

Verifikasi semua service berjalan:
```bash
docker-compose ps
```

### 3. Akses Service

| Service | URL | Keterangan |
|:---|:---|:---|
| **Jupyter Notebook** | http://localhost:8888 | Development & submit Spark jobs |
| **Spark UI (Master)** | http://localhost:8080 | Monitor cluster, job, stage, task |
| **Streamlit Dashboard** | http://localhost:8501 | Dashboard interaktif hasil analisis |

### 4. Jalankan Pipeline Medallion

```bash
# Di terminal Jupyter container atau terminal lokal dengan Spark
python scripts/bronze_layer.py    # Ingesti CSV → Parquet
python scripts/silver_layer.py    # Cleaning → Transformasi
python scripts/gold_layer.py      # Agregasi → Metrik SDG
```

### 5. Buka Dashboard

```bash
# Dashboard otomatis berjalan jika docker-compose sudah up
# Atau jalankan manual:
streamlit run dashboard/dashboard.py --server.address=0.0.0.0
```

### 6. Shutdown

```bash
docker-compose down
# atau hapus semua data volume:
docker-compose down -v
```

---

## 📁 Struktur Folder

```
sdg10-bigdata-itera/
├── 📂 data/
│   ├── 📂 raw/              ← DATA MENTAH IPUMS (excluded dari Git)
│   ├── 📂 bronze/           ← Hasil ingest: Parquet terpartisi
│   ├── 📂 silver/           ← Hasil transformasi
│   └── 📂 gold/             ← Hasil agregasi
├── 📂 notebooks/
│   ├── 01_baseline_pandas.ipynb      ← Pipeline baseline Pandas
│   ├── 02_eda_ipums.ipynb            ← Eksplorasi data
│   └── 03_benchmark_analysis.ipynb   ← Analisis perbandingan Spark vs Pandas
├── 📂 scripts/
│   ├── bronze_layer.py       ← Ingesti & validasi skema
│   ├── silver_layer.py       ← Pembersihan & transformasi
│   ├── gold_layer.py         ← Agregasi & perhitungan metrik
│   ├── utils.py              ← Fungsi Gini, Theil, Palma ratio
│   └── config.py             ← Konstanta: path, variabel, threshold
├── 📂 dashboard/
│   ├── dashboard.py          ← Aplikasi Streamlit utama
│   ├── 📂 components/
│   │   ├── gini_chart.py     ← Visualisasi Gini coefficient
│   │   ├── quintile_table.py ← Tabel kuintil interaktif
│   │   └── income_dist.py    ← Histogram distribusi income
│   └── 📂 assets/
│       └── logo.png          ← Logo/logo tim
├── 📂 docker/
│   ├── docker-compose.yml    ← Definisi 5 service container
│   └── Dockerfile.spark      ← Custom image Spark + Delta Lake
├── 📂 docs/
│   ├── proposal.docx         ← Proposal tugas besar
│   └── arsitektur-diagram.png ← Diagram arsitektur sistem
├── 📂 tests/
│   └── test_gini.py          ← Unit test perhitungan Gini
├── .gitignore                ← Exclude data mentah & file besar
├── README.md                 ← Dokumentasi ini
└── Makefile (opsional)       ← Perintah otomatisasi
```

---

## ⚙️ Pipeline Medallion

### Bronze Layer — Raw Ingestion
```python
# Contoh: bronze_layer.py
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("SDG10-Bronze") \
    .getOrCreate()

df = spark.read.csv("/data/raw/ipums_brazil_mexico_2010.csv", 
                    header=True, inferSchema=True)
df.write.parquet("/data/bronze/ipums_bronze.parquet", 
                 partitionBy=["COUNTRY", "YEAR"])
```

### Silver Layer — Clean & Transform
```python
# Contoh: silver_layer.py
from pyspark.sql.functions import col, when

df_silver = df_bronze \
    .filter(col("INCTOT").isNotNull()) \
    .dropDuplicates(["SAMPLE", "SERIAL", "PERNUM"]) \
    .withColumn("income_ppp", col("INCTOT") * 0.85)  # normalisasi PPP
```

### Gold Layer — Aggregated Analytics
```python
# Contoh: gold_layer.py
from scripts.utils import calculate_gini

df_gold = df_silver.groupBy("COUNTRY", "YEAR") \
    .agg(calculate_gini("INCTOT", "PERWT").alias("gini_coeff"))
```

---

## 📈 Dashboard Interaktif

### Fitur Utama

| Fitur | Deskripsi | Interaktivitas |
|:---|:---|:---|
| **Filter Negara** | Pilih Brazil atau Mexico | Dropdown sidebar |
| **Bar Chart Gini** | Perbandingan Gini coefficient | Hover tooltip |
| **Histogram Income** | Distribusi pendapatan per kuintil | Slider rentang |
| **Tabel Kuintil** | Q1–Q5 dengan jumlah populasi | Sort & search |
| **Box Plot Sektir** | Income per industri (INDGEN) | Drill-down |
| **Anomaly Flag** | Highlight jika bottom 40% < 50% median | Auto-detect |

### Screenshot Dashboard (Coming Soon)

> Dashboard akan di-deploy di `localhost:8501` setelah pipeline Gold layer berjalan.

---

## 📊 Benchmark & Evaluasi

| Metrik | Baseline (Pandas) | Target (Spark) | Speedup |
|:---|:---:|:---:|:---:|
| **Throughput Ingesti** | 2.500 baris/dtk | ≥ 25.000 baris/dtk | **10×+** |
| **Latensi End-to-End** | ~18 menit | ≤ 4 menit | **4.5×+** |
| **Rasio Kompresi** | 1.0× (CSV) | ≥ 3.0× (Parquet) | **3×** |
| **Akurasi Gini** | ±0.015 (exact) | ±0.020 (approximate) | Acceptable |

> Evaluasi diukur pada hardware identik: RAM 16 GB, 4-core CPU, SSD.

---

## ⚖️ Lisensi Data

Data **IPUMS International** digunakan berdasarkan **Academic Use License** dari Minnesota Population Center dan kantor statistik mitra nasional. Ketentuan utama:

- ✅ Penggunaan untuk penelitian dan pendidikan
- ❌ **Redistribution data mentah dilarang**
- ❌ **Commercial use dilarang**
- ❌ **Re-identification individu dilarang**
- ✅ Publikasi hasil agregat diperbolehkan dengan sitasi

Setiap anggota tim harus memiliki akun IPUMS International yang teregistrasi secara individual.

---

## 🚦 Status Proyek

| Milestone              |    Status   | Hari Target |
| :--------------------- | :---------: | :---------: |
| Setup Infrastruktur    |   🟢 Done   |    Hari 1   |
| Bronze Layer           |   🟢 Done   |    Hari 2   |
| Silver Layer           |   🟢 Done   |    Hari 3   |
| Gold Layer             |   🟢 Done   |    Hari 4   |
| Dashboard Streamlit    |   🟢 Done   |    Hari 5   |
| Benchmark & Polish     |   🟢 Done   |    Hari 6   |
| Final Testing & Submit | 🟡 Progress |    Hari 7   |


**Timeline:** 7 Hari (Senin - Minggu)  
**Metodologi:** Agile Daily Sync (19:00 WIB)

---

## 📚 Referensi

[1] Y. Liu et al., "A big data approach to assess progress towards Sustainable Development Goals for cities of varying sizes," *Communications Earth & Environment*, vol. 4, no. 1, p. 82, 2023.

[2] Steven Ruggles, Lara Cleveland, Rodrigo Lovaton, Sula Sarkar, Matthew Sobek, Derek Burk, Dan Ehrlich, Jane Lee, and Nate Merrill. Integrated Public Use Microdata Series, International: Version 7.6 [dataset]. Minneapolis, MN: IPUMS, 2025.
https://doi.org/10.18128/D020.V7.7

[3] World Bank, *Atlas of Sustainable Development Goals 2020: From World Development Indicators*, Washington, DC: World Bank, 2020.

[4] M. Armbrust et al., "Delta Lake: High-Performance ACID Table Storage over Cloud Object Stores," *Proc. VLDB Endowment*, vol. 13, no. 12, pp. 3411–3424, 2020.

[5] LIS Cross-National Data Center in Luxembourg, *Luxembourg Income Study Database: Inequality and Poverty Key Figures, 1967-2020*, Colchester, Essex: UK Data Service, 2022.

[6] M. Zaharia et al., "Apache Spark: A unified engine for big data processing," *Commun. ACM*, vol. 59, no. 11, pp. 56–65, 2016.

---

<p align="center">
  <i>Built with ❤️ by Team SDG10-ITERA | Institut Teknologi Sumatera 2026</i>
</p>
