# ==============================================================================
# config.py — Konfigurasi path dan konstanta proyek SDG-10 Big Data ITS
# ==============================================================================

import os
from pathlib import Path

# ── Root Proyek ────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent

# ── Data Paths ─────────────────────────────────────────────────────────────────
DATA_DIR    = ROOT_DIR / "data"
RAW_DIR     = DATA_DIR / "raw"
BRONZE_DIR  = DATA_DIR / "bronze"
SILVER_DIR  = DATA_DIR / "silver"
GOLD_DIR    = DATA_DIR / "gold"

# ── Notebook & Script Paths ────────────────────────────────────────────────────
NOTEBOOKS_DIR = ROOT_DIR / "notebooks"
SCRIPTS_DIR   = ROOT_DIR / "scripts"

# ── Dashboard ──────────────────────────────────────────────────────────────────
DASHBOARD_DIR = ROOT_DIR / "dashboard"
ASSETS_DIR    = DASHBOARD_DIR / "assets"

# ── Spark Config ───────────────────────────────────────────────────────────────
SPARK_APP_NAME   = "SDG10-BigData-ITS"
SPARK_MASTER     = os.getenv("SPARK_MASTER", "local[*]")
SPARK_LOG_LEVEL  = "WARN"

# ── Variabel IPUMS ─────────────────────────────────────────────────────────────
# Kolom pendapatan utama yang digunakan dari dataset IPUMS
INCOME_COLS = [
    "INCTOT",    # Total personal income
    "INCWAGE",   # Wage and salary income
    "INCBUS",    # Business income
    "INCFARM",   # Farm income
    "INCSSI",    # Social security income
    "INCWELFR",  # Welfare income
]

# Kolom identitas / demografis
ID_COLS = [
    "COUNTRY",
    "YEAR",
    "SERIAL",
    "PERNUM",
    "PERWT",    # Final weight (untuk analisis tertimbang)
    "AGE",
    "SEX",
    "RACE",
    "EDUC",
    "EDATTAIN",
    "EMPSTAT",
    "STATEFIP",
]

# Semua kolom yang dipertahankan ke Silver Layer
SILVER_KEEP_COLS = ID_COLS + INCOME_COLS

# ── Threshold & Filter ─────────────────────────────────────────────────────────
MIN_AGE        = 18          # Usia minimum untuk analisis kerja
MAX_AGE        = 65          # Usia maksimum
MIN_INCOME     = 0           # Pendapatan minimum valid
INCOME_TOP_CAP = 9_999_998   # Kode IPUMS untuk "tidak terdefinisi"

# ── Quintile / Desil ───────────────────────────────────────────────────────────
N_QUINTILES = 5
N_DECILES   = 10

# ── Output File Names ──────────────────────────────────────────────────────────
BRONZE_FILE = "ipums_bronze.parquet"
SILVER_FILE = "ipums_silver.parquet"
GOLD_GINI_FILE     = "gold_gini_by_year.parquet"
GOLD_QUINTILE_FILE = "gold_quintile_by_year.parquet"
GOLD_THEIL_FILE    = "gold_theil_by_year.parquet"
