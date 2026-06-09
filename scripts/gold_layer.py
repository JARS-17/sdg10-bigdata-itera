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
from utils import gini_coefficient, theil_index, quintile_shares, palma_ratio, proportion_below_50_median

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def create_spark_session() -> SparkSession:
    spark = (
        SparkSession.builder
        .appName(f"{SPARK_APP_NAME} - Gold")
        .master(SPARK_MASTER)
        .config("spark.driver.memory", "8g")
        .config("spark.executor.memory", "4g")
        .config("spark.driver.maxResultSize", "4g")
        # Kurangi partisi shuffle agar tiap partisi lebih kecil → hemat memori
        .config("spark.sql.shuffle.partitions", "50")
        # Aktifkan Adaptive Query Execution → Spark otomatis optimasi memori
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        # Aktifkan off-heap agar aggregasi bisa spill ke luar JVM heap
        .config("spark.memory.offHeap.enabled", "true")
        .config("spark.memory.offHeap.size", "2g")
        # Izinkan spill ke disk jika memori penuh
        .config("spark.sql.execution.arrow.pyspark.fallback.enabled", "true")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel(SPARK_LOG_LEVEL)
    return spark


def load_silver(spark: SparkSession) -> DataFrame:
    path = str(SILVER_DIR / SILVER_FILE)
    logger.info(f"Membaca Silver Layer dari: {path}")
    return spark.read.parquet(path)


def compute_gini_by_country_year(df: DataFrame, counts_by_country_year: dict) -> pd.DataFrame:
    """
    Hitung Gini Coefficient per negara dan tahun.
    Gunakan kolom 'income_analysis' (harmonisasi INCTOT/INCEARN dari Silver layer).
    """
    logger.info("Menghitung Gini Coefficient per negara dan tahun...")
    # Gunakan income_analysis jika ada (Silver baru), fallback ke INCTOT (Silver lama)
    income_col = "income_analysis" if "income_analysis" in df.columns else "INCTOT"
    logger.info(f"Menggunakan kolom pendapatan: {income_col}")
    pdf = df.select("COUNTRY", "YEAR", income_col, "PERWT").toPandas()
    pdf = pdf.rename(columns={income_col: "_income"})

    COUNTRY_MAP = {76: "Brazil", 484: "Mexico"}

    results = []
    for (country, year), group in pdf.groupby(["COUNTRY", "YEAR"]):
        inc = group["_income"].values.astype(float)
        wt  = group["PERWT"].values.astype(float)

        gini        = gini_coefficient(inc, wt)
        theil       = theil_index(inc, wt)
        palma       = palma_ratio(inc, wt)
        sdg_10_2_1  = proportion_below_50_median(inc, wt)
        mean_all = np.average(inc, weights=wt) if len(inc) > 0 else 0.0
        
        order = np.argsort(inc)
        sorted_inc = inc[order]
        sorted_wt = wt[order]
        cum_w = np.cumsum(sorted_wt)
        b40_mask = cum_w <= 0.40 * cum_w[-1] if len(cum_w) > 0 else []
        mean_b40 = np.average(sorted_inc[b40_mask], weights=sorted_wt[b40_mask]) if len(b40_mask) > 0 and sum(b40_mask) > 0 else 0.0
        
        anomali_b40 = "Kritis" if mean_b40 < 0.5 * mean_all else "Normal"
        
        n_obs_actual = counts_by_country_year.get((country, year), len(group))
        
        results.append({
            "country": country,
            "country_name": COUNTRY_MAP.get(country, str(country)),
            "year":    year,
            "gini":    gini,
            "theil":   theil,
            "palma":   palma,
            "sdg_10_2_1": sdg_10_2_1,
            "mean_income": mean_all,
            "mean_b40": mean_b40,
            "anomali_b40": anomali_b40,
            "n_obs":   n_obs_actual,
        })
        logger.info(f"  {country} {year}: Gini={gini:.4f}, Theil={theil:.4f}, Palma={palma:.4f}, SDG10.2.1={sdg_10_2_1:.4f}, n_obs={n_obs_actual}")

    return pd.DataFrame(results).sort_values(["country", "year"]).reset_index(drop=True)


def compute_quintile_by_country_year(df: DataFrame) -> pd.DataFrame:
    """Hitung distribusi quintile per negara dan tahun."""
    logger.info("Menghitung Quintile Share per negara dan tahun...")
    income_col = "income_analysis" if "income_analysis" in df.columns else "INCTOT"
    pdf = df.select("COUNTRY", "YEAR", income_col, "PERWT").toPandas()
    pdf = pdf.rename(columns={income_col: "_income"})

    all_results = []
    for (country, year), group in pdf.groupby(["COUNTRY", "YEAR"]):
        q_df = quintile_shares(group["_income"].values, group["PERWT"].values, n=N_QUINTILES)
        q_df["country"] = country
        q_df["year"] = year
        all_results.append(q_df)

    return pd.concat(all_results, ignore_index=True).sort_values(["country", "year", "quantile"])


def compute_income_stats_by_country_year(df: DataFrame) -> pd.DataFrame:
    """Statistik deskriptif pendapatan per negara dan tahun."""
    logger.info("Menghitung statistik pendapatan per negara dan tahun...")
    income_col = "income_analysis" if "income_analysis" in df.columns else "INCTOT"
    result = (
        df.groupBy("COUNTRY", "YEAR")
        .agg(
            F.mean(income_col).alias("mean_income"),
            F.percentile_approx(income_col, 0.5).alias("median_income"),
            F.stddev(income_col).alias("std_income"),
            F.min(income_col).alias("min_income"),
            F.max(income_col).alias("max_income"),
            F.count("*").alias("n_obs"),
        )
        .orderBy("COUNTRY", "YEAR")
    )
    return result.toPandas()


def compute_and_write_demographics(df: DataFrame, spark: SparkSession) -> None:
    logger.info("Menghitung dan menyimpan data demografi...")
    
    # Gunakan income_analysis jika ada
    income_col = "income_analysis" if "income_analysis" in df.columns else "INCTOT"

    # 1. Sex
    sex_df = df.select("COUNTRY", "YEAR", "SEX", "PERWT") \
               .withColumn("sex_label", F.when(F.col("SEX") == 1, "Laki-laki").otherwise("Perempuan")) \
               .groupBy("COUNTRY", "YEAR", "sex_label") \
               .agg(F.sum("PERWT").alias("weighted_count"), F.count("*").alias("raw_count")) \
               .toPandas()
    
    # 2. Employment
    emp_df = df.select("COUNTRY", "YEAR", "EMPSTAT", "PERWT") \
               .withColumn("empstat_label", 
                           F.when(F.col("EMPSTAT") == 1, "Bekerja")
                            .when(F.col("EMPSTAT") == 2, "Pengangguran")
                            .when(F.col("EMPSTAT") == 3, "Tidak Aktif")
                            .otherwise("Lainnya")) \
               .groupBy("COUNTRY", "YEAR", "empstat_label") \
               .agg(F.sum("PERWT").alias("weighted_count"), F.count("*").alias("raw_count")) \
               .toPandas()
               
    # 3. Education
    edu_df = df.select("COUNTRY", "YEAR", "EDATTAIN", "PERWT") \
               .withColumn("education_label",
                           F.when(F.col("EDATTAIN") == 1, "Tdk Tamat SD")
                            .when(F.col("EDATTAIN") == 2, "SD/Sederajat")
                            .when(F.col("EDATTAIN") == 3, "SMA/Sederajat")
                            .when(F.col("EDATTAIN") == 4, "Perguruan Tinggi")
                            .otherwise("Lainnya")) \
               .groupBy("COUNTRY", "YEAR", "education_label") \
               .agg(F.sum("PERWT").alias("weighted_count"), F.count("*").alias("raw_count")) \
               .toPandas()
               
    # 4. Age Group
    age_df = df.select("COUNTRY", "YEAR", "AGE", "PERWT") \
               .withColumn("age_group",
                           F.when(F.col("AGE").between(10, 19), "10-19")
                            .when(F.col("AGE").between(20, 29), "20-29")
                            .when(F.col("AGE").between(30, 39), "30-39")
                            .when(F.col("AGE").between(40, 49), "40-49")
                            .when(F.col("AGE").between(50, 59), "50-59")
                            .when(F.col("AGE").between(60, 69), "60-69")
                            .when(F.col("AGE").between(70, 79), "70-79")
                            .otherwise("80+")) \
               .groupBy("COUNTRY", "YEAR", "age_group") \
               .agg(F.sum("PERWT").alias("weighted_count"), F.count("*").alias("raw_count")) \
               .toPandas()
               
    # Save to gold directory as parquet
    spark.createDataFrame(sex_df).write.mode("overwrite").parquet(str(GOLD_DIR / "gold_demog_sex.parquet"))
    spark.createDataFrame(emp_df).write.mode("overwrite").parquet(str(GOLD_DIR / "gold_demog_emp.parquet"))
    spark.createDataFrame(edu_df).write.mode("overwrite").parquet(str(GOLD_DIR / "gold_demog_edu.parquet"))
    spark.createDataFrame(age_df).write.mode("overwrite").parquet(str(GOLD_DIR / "gold_demog_age.parquet"))
    logger.info("✅ Data demografi berhasil disimpan.")


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

    # Hitung total counts asli per negara dan tahun secara efisien di Spark
    logger.info("Menghitung total baris asli per negara dan tahun...")
    counts_by_country_year = {
        (row["COUNTRY"], row["YEAR"]): row["count"] 
        for row in df.groupBy("COUNTRY", "YEAR").count().collect()
    }

    # Ambil sampel 10% untuk perhitungan analitis di Pandas agar tidak OOM
    logger.info("Mengambil sampel 10% untuk perhitungan Pandas...")
    sample_df = df.sample(fraction=0.1, seed=42)

    # Hitung metrik ketimpangan
    gini_pdf     = compute_gini_by_country_year(sample_df, counts_by_country_year)
    quintile_pdf = compute_quintile_by_country_year(sample_df)
    stats_pdf    = compute_income_stats_by_country_year(df) # Tetap pakai full df karena aggregasi di Spark

    # Hitung dan simpan data demografi
    compute_and_write_demographics(df, spark)

    # Simpan ke Gold Layer
    write_gold_parquet(gini_pdf,     GOLD_GINI_FILE,     spark)
    write_gold_parquet(quintile_pdf, GOLD_QUINTILE_FILE, spark)
    write_gold_parquet(stats_pdf,    GOLD_THEIL_FILE,    spark)

    df.unpersist()
    spark.stop()
    logger.info("🏁 Gold Layer pipeline selesai.")


if __name__ == "__main__":
    run()
