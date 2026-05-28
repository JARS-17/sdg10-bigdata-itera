# ==============================================================================
# bronze_layer.py — Ingest data mentah IPUMS → Bronze Layer (Parquet)
# ==============================================================================

import logging
from pathlib import Path

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F

from config import (
    SPARK_APP_NAME, SPARK_MASTER, SPARK_LOG_LEVEL,
    RAW_DIR, BRONZE_DIR, BRONZE_FILE
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def create_spark_session() -> SparkSession:
    """Inisialisasi SparkSession."""
    spark = (
        SparkSession.builder
        .appName(f"{SPARK_APP_NAME} - Bronze")
        .master(SPARK_MASTER)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel(SPARK_LOG_LEVEL)
    return spark


def ingest_ipums_csv(spark: SparkSession, filepath: Path) -> DataFrame:
    """
    Baca file CSV hasil export IPUMS.

    IPUMS biasanya menghasilkan file .csv atau .dat dengan header.
    Sesuaikan dengan format data yang Anda download.
    """
    logger.info(f"Membaca data dari: {filepath}")
    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .option("nullValue", "")
        .csv(str(filepath))
    )
    logger.info(f"Total baris: {df.count():,} | Kolom: {len(df.columns)}")
    return df


def add_metadata(df: DataFrame, source_file: str) -> DataFrame:
    """Tambahkan kolom metadata untuk data lineage."""
    return df.withColumns({
        "_source_file":    F.lit(source_file),
        "_ingested_at":    F.current_timestamp(),
        "_layer":          F.lit("bronze"),
    })


def write_bronze(df: DataFrame) -> None:
    """Simpan Bronze Layer ke Parquet."""
    output_path = str(BRONZE_DIR / BRONZE_FILE)
    logger.info(f"Menyimpan Bronze Layer ke: {output_path}")
    (
        df.write
        .mode("overwrite")
        .parquet(output_path)
    )
    logger.info("✅ Bronze Layer berhasil disimpan.")


def run(source_filename: str = "ipums_data.csv") -> None:
    """Entry point pipeline Bronze Layer."""
    spark = create_spark_session()
    source_path = RAW_DIR / source_filename

    if not source_path.exists():
        logger.error(f"File tidak ditemukan: {source_path}")
        logger.error("Pastikan Anda sudah menempatkan data IPUMS di folder data/raw/")
        spark.stop()
        return

    df = ingest_ipums_csv(spark, source_path)
    df = add_metadata(df, source_file=str(source_path))
    write_bronze(df)

    spark.stop()
    logger.info("🏁 Bronze Layer pipeline selesai.")


if __name__ == "__main__":
    run()
