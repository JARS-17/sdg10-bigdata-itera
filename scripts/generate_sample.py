import time
import logging
from pathlib import Path

from pyspark.sql import SparkSession
from config import SPARK_APP_NAME, SPARK_MASTER, RAW_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run():
    t0 = time.time()
    spark = SparkSession.builder \
        .appName(f"{SPARK_APP_NAME} - Data Sampling") \
        .master(SPARK_MASTER) \
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("WARN")

    input_file = RAW_DIR / "ipums_brazil_mexico_2010.csv"
    output_file = RAW_DIR / "ipums_sample_10pct.csv"
    
    if not input_file.exists():
        logger.error(f"File sumber tidak ditemukan: {input_file}")
        spark.stop()
        return

    logger.info(f"Membaca data penuh dari {input_file}...")
    df = spark.read.csv(str(input_file), header=True, inferSchema=True)
    
    # Melakukan stratified sampling berdasarkan negara
    # 76 = Brazil, 484 = Mexico
    logger.info("Mengambil sampel 10% (0.1) dari masing-masing negara...")
    fractions = {76: 0.1, 484: 0.1} 
    df_sample = df.sampleBy("COUNTRY", fractions, seed=42)
    
    # Karena kita butuh file CSV tunggal untuk Pandas, kita konversi ke Pandas dulu.
    # 10% dari 32 juta baris = ~3.2 juta baris (masih sangat aman untuk RAM 16GB)
    logger.info("Mengkonversi sampel ke Pandas DataFrame untuk disimpan sebagai 1 file CSV...")
    df_sample_pd = df_sample.toPandas()
    
    sample_count = len(df_sample_pd)
    logger.info(f"Total baris sampel berhasil ditarik: {sample_count:,}")
    
    logger.info(f"Menyimpan sampel CSV ke {output_file}...")
    df_sample_pd.to_csv(output_file, index=False)
    
    elapsed = time.time() - t0
    logger.info(f"✅ Proses sampling selesai dalam {elapsed:.2f} detik!")
    spark.stop()

if __name__ == "__main__":
    run()
