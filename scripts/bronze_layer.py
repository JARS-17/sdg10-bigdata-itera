# ==============================================================================
# bronze_layer.py — Ingest data mentah IPUMS → Bronze Layer (Parquet)
# ==============================================================================

import logging
from pathlib import Path

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, IntegerType, DoubleType, LongType

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
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel(SPARK_LOG_LEVEL)
    return spark


BRONZE_SCHEMA = StructType([
    StructField("COUNTRY", IntegerType(), True),
    StructField("YEAR", IntegerType(), True),
    StructField("SAMPLE", LongType(), True),
    StructField("SERIAL", LongType(), True),
    StructField("HHWT", DoubleType(), True),
    StructField("PERNUM", IntegerType(), True),
    StructField("PERWT", DoubleType(), True),
    StructField("AGE", IntegerType(), True),
    StructField("SEX", IntegerType(), True),
    StructField("EDATTAIN", IntegerType(), True),
    StructField("EDATTAIND", IntegerType(), True),
    StructField("EMPSTAT", IntegerType(), True),
    StructField("EMPSTATD", IntegerType(), True),
    StructField("OCCISCO", IntegerType(), True),
    StructField("INDGEN", IntegerType(), True),
    StructField("INCTOT", DoubleType(), True),
    StructField("INCEARN", DoubleType(), True),
])


def ingest_ipums_csv(spark: SparkSession, filepath: Path) -> DataFrame:
    """
    Baca file CSV hasil export IPUMS secara efisien menggunakan skema eksplisit.
    """
    logger.info(f"Membaca data dari: {filepath}")
    df = (
        spark.read
        .option("header", "true")
        .schema(BRONZE_SCHEMA)
        .option("nullValue", "")
        .csv(str(filepath))
    )
    logger.info(f"Kolom dibaca: {len(df.columns)}")
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


def run(source_filename: str = "ipums_brazil_mexico_2010.csv") -> None:
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
