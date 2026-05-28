# ==============================================================================
# gold_layer.py — Agregasi & Metrik Ketimpangan Silver → Gold Layer
# ==============================================================================

import logging

import numpy as np
import pandas as pd
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

from config import (
    SPARK_APP_NAME, SPARK_MASTER, SPARK_LOG_LEVEL,
    SILVER_DIR, GOLD_DIR,
    SILVER_FILE,
    GOLD_GINI_FILE, GOLD_QUINTILE_FILE, GOLD_THEIL_FILE,
    N_QUINTILES
)
from utils import gini_coefficient, theil_index, quintile_shares, palma_ratio

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def create_spark_session() -> SparkSession:
    spark = (
        SparkSession.builder
        .appName(f"{SPARK_APP_NAME} - Gold")
        .master(SPARK_MASTER)
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel(SPARK_LOG_LEVEL)
    return spark


def load_silver(spark: SparkSession) -> DataFrame:
    path = str(SILVER_DIR / SILVER_FILE)
    logger.info(f"Membaca Silver Layer dari: {path}")
    return spark.read.parquet(path)


def compute_gini_by_year(df: DataFrame) -> pd.DataFrame:
    """
    Hitung Gini Coefficient per tahun menggunakan Pandas UDF.
    Konversi ke Pandas untuk perhitungan sekuensial.
    """
    logger.info("Menghitung Gini Coefficient per tahun...")
    pdf = df.select("YEAR", "INCTOT", "WTFINL").toPandas()

    results = []
    for year, group in pdf.groupby("YEAR"):
        gini = gini_coefficient(group["INCTOT"].values, group["WTFINL"].values)
        theil = theil_index(group["INCTOT"].values, group["WTFINL"].values)
        palma = palma_ratio(group["INCTOT"].values, group["WTFINL"].values)
        results.append({
            "year":    year,
            "gini":    gini,
            "theil":   theil,
            "palma":   palma,
            "n_obs":   len(group),
        })
        logger.info(f"  {year}: Gini={gini:.4f}, Theil={theil:.4f}, Palma={palma:.4f}")

    return pd.DataFrame(results).sort_values("year").reset_index(drop=True)


def compute_quintile_by_year(df: DataFrame) -> pd.DataFrame:
    """Hitung distribusi quintile per tahun."""
    logger.info("Menghitung Quintile Share per tahun...")
    pdf = df.select("YEAR", "INCTOT", "WTFINL").toPandas()

    all_results = []
    for year, group in pdf.groupby("YEAR"):
        q_df = quintile_shares(group["INCTOT"].values, group["WTFINL"].values, n=N_QUINTILES)
        q_df["year"] = year
        all_results.append(q_df)

    return pd.concat(all_results, ignore_index=True).sort_values(["year", "quantile"])


def compute_income_stats_by_year(df: DataFrame) -> pd.DataFrame:
    """Statistik deskriptif pendapatan per tahun."""
    logger.info("Menghitung statistik pendapatan per tahun...")
    result = (
        df.groupBy("YEAR")
        .agg(
            F.mean("INCTOT").alias("mean_income"),
            F.percentile_approx("INCTOT", 0.5).alias("median_income"),
            F.stddev("INCTOT").alias("std_income"),
            F.min("INCTOT").alias("min_income"),
            F.max("INCTOT").alias("max_income"),
            F.count("*").alias("n_obs"),
        )
        .orderBy("YEAR")
    )
    return result.toPandas()


def write_gold_parquet(pdf: pd.DataFrame, filename: str, spark: SparkSession) -> None:
    """Simpan Pandas DataFrame ke Gold Layer sebagai Parquet."""
    output_path = str(GOLD_DIR / filename)
    sdf = spark.createDataFrame(pdf)
    sdf.write.mode("overwrite").parquet(output_path)
    logger.info(f"✅ Disimpan ke: {output_path}")


def run() -> None:
    spark = create_spark_session()

    df = load_silver(spark)
    df.cache()

    # Hitung metrik ketimpangan
    gini_pdf     = compute_gini_by_year(df)
    quintile_pdf = compute_quintile_by_year(df)
    stats_pdf    = compute_income_stats_by_year(df)

    # Simpan ke Gold Layer
    write_gold_parquet(gini_pdf,     GOLD_GINI_FILE,     spark)
    write_gold_parquet(quintile_pdf, GOLD_QUINTILE_FILE, spark)
    write_gold_parquet(stats_pdf,    GOLD_THEIL_FILE,    spark)

    df.unpersist()
    spark.stop()
    logger.info("🏁 Gold Layer pipeline selesai.")


if __name__ == "__main__":
    run()
