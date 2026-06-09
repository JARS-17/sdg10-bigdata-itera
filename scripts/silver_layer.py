# ==============================================================================
# silver_layer.py — Cleaning & Transformasi Bronze → Silver Layer
# Fix: Mexico menggunakan INCEARN (bukan INCTOT) sebagai kolom pendapatan
# ==============================================================================

import logging

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

from config import (
    SPARK_APP_NAME, SPARK_MASTER, SPARK_LOG_LEVEL,
    BRONZE_DIR, SILVER_DIR,
    BRONZE_FILE, SILVER_FILE,
    MIN_AGE, MAX_AGE,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Kolom yang dipertahankan di Silver — termasuk INCEARN untuk Mexico
SILVER_COLS = [
    "COUNTRY", "YEAR", "SERIAL", "PERNUM", "PERWT",
    "AGE", "SEX", "EDATTAIN", "EMPSTAT",
    "INCTOT",   # Pendapatan total — Brazil
    "INCEARN",  # Pendapatan dari pekerjaan — Mexico (INCTOT null untuk Mexico)
]


def create_spark_session() -> SparkSession:
    spark = (
        SparkSession.builder
        .appName(f"{SPARK_APP_NAME} - Silver")
        .master(SPARK_MASTER)
        .config("spark.driver.memory", "6g")
        .config("spark.sql.shuffle.partitions", "200")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel(SPARK_LOG_LEVEL)
    return spark


def load_bronze(spark: SparkSession) -> DataFrame:
    path = str(BRONZE_DIR / BRONZE_FILE)
    logger.info(f"Membaca Bronze Layer dari: {path}")
    return spark.read.parquet(path)


def select_columns(df: DataFrame) -> DataFrame:
    """Pilih kolom yang relevan (yang ada di dataset)."""
    available    = set(df.columns)
    cols_to_keep = [c for c in SILVER_COLS if c in available]
    missing      = set(SILVER_COLS) - available
    if missing:
        logger.warning(f"Kolom tidak ditemukan di Bronze: {missing}")
    logger.info(f"Kolom yang dipertahankan: {cols_to_keep}")
    return df.select(cols_to_keep)


def cast_numeric_columns(df: DataFrame) -> DataFrame:
    """Pastikan kolom pendapatan dan bobot bertipe numerik."""
    for col in ["INCTOT", "INCEARN", "PERWT", "AGE"]:
        if col in df.columns:
            df = df.withColumn(col, F.col(col).cast(DoubleType()))
    return df


def filter_age(df: DataFrame) -> DataFrame:
    """Filter usia kerja (18–65 tahun)."""
    if "AGE" not in df.columns:
        return df
    df = df.filter(F.col("AGE").between(MIN_AGE, MAX_AGE))
    logger.info(f"Filter usia {MIN_AGE}–{MAX_AGE} diaplikasikan.")
    return df


def harmonize_income(df: DataFrame) -> DataFrame:
    """
    Harmonisasi kolom pendapatan antar negara:
    - Brazil  (76):  INCTOT berisi nilai, INCEARN bisa juga ada
    - Mexico  (484): INCTOT NULL semua, INCEARN berisi nilai
    Hasilkan kolom tunggal 'income_analysis' untuk Gini/Palma/Theil.
    """
    has_inctot  = "INCTOT"  in df.columns
    has_incearn = "INCEARN" in df.columns

    if has_inctot and has_incearn:
        # Prioritaskan INCTOT, fallback ke INCEARN jika INCTOT null
        df = df.withColumn(
            "income_analysis",
            F.when(F.col("INCTOT").isNotNull(),  F.col("INCTOT").cast(DoubleType()))
             .when(F.col("INCEARN").isNotNull(), F.col("INCEARN").cast(DoubleType()))
             .otherwise(F.lit(0.0))
        )
    elif has_inctot:
        df = df.withColumn("income_analysis", F.col("INCTOT").cast(DoubleType()))
    elif has_incearn:
        df = df.withColumn("income_analysis", F.col("INCEARN").cast(DoubleType()))
    else:
        df = df.withColumn("income_analysis", F.lit(0.0))

    # Buang nilai IPUMS "truly missing" (9999999) dan floor negatif ke 0
    df = df.withColumn(
        "income_analysis",
        F.when(F.col("income_analysis") >= 9_999_999, F.lit(None).cast(DoubleType()))
         .when(F.col("income_analysis") < 0, F.lit(0.0))
         .otherwise(F.col("income_analysis"))
    )

    # Hanya pertahankan baris di mana income_analysis valid (tidak null)
    df = df.filter(F.col("income_analysis").isNotNull())
    logger.info("Harmonisasi income_analysis selesai.")
    return df


def drop_nulls(df: DataFrame) -> DataFrame:
    """Hapus baris yang null di kolom kritis YEAR dan PERWT."""
    critical = [c for c in ["YEAR", "PERWT"] if c in df.columns]
    df = df.dropna(subset=critical)
    logger.info("Drop nulls (YEAR, PERWT) selesai.")
    return df


def add_derived_columns(df: DataFrame) -> DataFrame:
    """Tambahkan kolom turunan: kategori pendapatan, label gender, label negara."""

    # Kategori pendapatan berdasarkan income_analysis
    if "income_analysis" in df.columns:
        df = df.withColumn(
            "income_category",
            F.when(F.col("income_analysis") == 0, "zero")
             .when(F.col("income_analysis") < 10_000,  "low")
             .when(F.col("income_analysis") < 50_000,  "middle")
             .when(F.col("income_analysis") < 100_000, "upper_middle")
             .otherwise("high")
        )

    # Label gender
    if "SEX" in df.columns:
        df = df.withColumn(
            "sex_label",
            F.when(F.col("SEX") == 1, "Laki-laki").otherwise("Perempuan")
        )

    # Label negara
    if "COUNTRY" in df.columns:
        df = df.withColumn(
            "country_name",
            F.when(F.col("COUNTRY") == 76,  "Brazil")
             .when(F.col("COUNTRY") == 484, "Mexico")
             .otherwise(F.col("COUNTRY").cast("string"))
        )

    return df.withColumn("_layer", F.lit("silver"))


def write_silver(df: DataFrame) -> None:
    output_path = str(SILVER_DIR / SILVER_FILE)
    logger.info(f"Menyimpan Silver Layer ke: {output_path}")
    (
        df.write
        .mode("overwrite")
        .partitionBy("COUNTRY")   # Partition per negara agar Gold layer lebih efisien
        .parquet(output_path)
    )
    logger.info("✅ Silver Layer berhasil disimpan.")


def run() -> None:
    spark = create_spark_session()

    df = load_bronze(spark)
    df = select_columns(df)
    df = cast_numeric_columns(df)
    df = filter_age(df)
    df = harmonize_income(df)   # ← Kunci perbaikan Mexico
    df = drop_nulls(df)
    df = add_derived_columns(df)

    write_silver(df)
    spark.stop()
    logger.info("🏁 Silver Layer pipeline selesai.")


if __name__ == "__main__":
    run()
