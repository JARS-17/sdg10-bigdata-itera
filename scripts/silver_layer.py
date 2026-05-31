# ==============================================================================
# silver_layer.py — Cleaning & Transformasi Bronze → Silver Layer
# ==============================================================================

import time
import logging

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

from config import (
    SPARK_APP_NAME, SPARK_MASTER, SPARK_LOG_LEVEL,
    BRONZE_DIR, SILVER_DIR,
    BRONZE_FILE, SILVER_FILE,
    SILVER_KEEP_COLS, INCOME_COLS, ID_COLS,
    MIN_AGE, MAX_AGE, MIN_INCOME, INCOME_TOP_CAP, PPP_FACTOR
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def create_spark_session() -> SparkSession:
    spark = (
        SparkSession.builder
        .appName(f"{SPARK_APP_NAME} - Silver")
        .master(SPARK_MASTER)
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel(SPARK_LOG_LEVEL)
    return spark


def load_bronze(spark: SparkSession) -> DataFrame:
    path = str(BRONZE_DIR / BRONZE_FILE)
    logger.info(f"Membaca Bronze Layer dari: {path}")
    return spark.read.parquet(path)


def select_columns(df: DataFrame) -> DataFrame:
    """Pilih kolom yang relevan saja (yang ada di dataset)."""
    available = set(df.columns)
    cols_to_keep = [c for c in SILVER_KEEP_COLS if c in available]
    missing = set(SILVER_KEEP_COLS) - available
    if missing:
        logger.warning(f"Kolom tidak ditemukan di Bronze: {missing}")
    logger.info(f"Kolom yang dipertahankan: {cols_to_keep}")
    return df.select(cols_to_keep)


def cast_income_columns(df: DataFrame) -> DataFrame:
    """Pastikan semua kolom pendapatan bertipe numerik."""
    for col in INCOME_COLS:
        if col in df.columns:
            df = df.withColumn(col, F.col(col).cast(DoubleType()))
    return df


def deduplicate_records(df: DataFrame) -> DataFrame:
    """Deduplikasi berdasarkan kombinasi unik individu: SERIAL + PERNUM"""
    if "SERIAL" in df.columns and "PERNUM" in df.columns:
        before = df.count()
        df = df.dropDuplicates(["SERIAL", "PERNUM"])
        after = df.count()
        logger.info(f"Deduplikasi: {before:,} → {after:,} baris (dihapus: {before - after:,})")
    return df


def filter_age(df: DataFrame) -> DataFrame:
    """Filter usia kerja (18–65 tahun)."""
    if "AGE" not in df.columns:
        return df
    before = df.count()
    df = df.filter(F.col("AGE").between(MIN_AGE, MAX_AGE))
    after = df.count()
    logger.info(f"Filter usia: {before:,} → {after:,} baris (dihapus: {before - after:,})")
    return df


def filter_income(df: DataFrame) -> DataFrame:
    """
    Bersihkan nilai pendapatan:
    - Hapus nilai kode khusus IPUMS (9999998, 9999999)
    - Pertahankan nilai >= 0 (termasuk 0 = tidak bekerja)
    """
    if "INCTOT" not in df.columns:
        return df
    before = df.count()
    df = df.filter(
        (F.col("INCTOT") >= MIN_INCOME) &
        (F.col("INCTOT") < INCOME_TOP_CAP)
    )
    after = df.count()
    logger.info(f"Filter pendapatan: {before:,} → {after:,} baris (dihapus: {before - after:,})")
    return df


def drop_nulls(df: DataFrame) -> DataFrame:
    """Hapus baris yang memiliki null pada kolom kritis."""
    critical_cols = [c for c in ["YEAR", "INCTOT", "WTFINL"] if c in df.columns]
    before = df.count()
    df = df.dropna(subset=critical_cols)
    after = df.count()
    logger.info(f"Drop nulls: {before:,} → {after:,} baris (dihapus: {before - after:,})")
    return df


def add_derived_columns(df: DataFrame) -> DataFrame:
    """Tambahkan kolom turunan yang berguna."""
    if "INCTOT" in df.columns:
        # Normalisasi PPP (Purchasing Power Parity)
        df = df.withColumn("income_ppp", F.col("INCTOT") * PPP_FACTOR)
        
        # Kategori pendapatan
        df = df.withColumn(
            "income_category",
            F.when(F.col("INCTOT") == 0, "zero")
             .when(F.col("INCTOT") < 10_000, "low")
             .when(F.col("INCTOT") < 50_000, "middle")
             .when(F.col("INCTOT") < 100_000, "upper_middle")
             .otherwise("high")
        )

    # Label gender
    if "SEX" in df.columns:
        df = df.withColumn(
            "sex_label",
            F.when(F.col("SEX") == 1, "Male").otherwise("Female")
        )

    return df.withColumn("_layer", F.lit("silver"))


def write_silver(df: DataFrame) -> None:
    output_path = str(SILVER_DIR / SILVER_FILE)
    logger.info(f"Menyimpan Silver Layer ke: {output_path}")
    t0 = time.time()
    (
        df.write
        .mode("overwrite")
        .parquet(output_path)
    )
    elapsed = time.time() - t0
    logger.info(f"✅ Silver Layer berhasil disimpan dalam {elapsed:.2f} detik.")


def run() -> None:
    t_start = time.time()
    spark = create_spark_session()

    df = load_bronze(spark)
    df = select_columns(df)
    df = cast_income_columns(df)
    df = deduplicate_records(df)
    df = filter_age(df)
    df = filter_income(df)
    df = drop_nulls(df)
    df = add_derived_columns(df)

    write_silver(df)
    spark.stop()
    
    total_elapsed = time.time() - t_start
    logger.info(f"🏁 Silver Layer pipeline selesai. Total Waktu: {total_elapsed:.2f} detik.")


if __name__ == "__main__":
    run()
