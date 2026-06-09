"""
benchmark_pipeline.py — Mengukur waktu eksekusi pipeline SDG-10 selama 3 iterasi.

Pipeline:
  - Bronze : Membaca bronze.parquet yang sudah ada via Spark (bukan re-ingest CSV)
  - Silver : Transformasi Bronze → Silver (spark-submit silver_layer.py)
  - Gold   : Agregasi Silver → Gold   (spark-submit gold_layer.py)
"""

import time
import subprocess
import sys
from pathlib import Path

# Paths inside the container
scripts_dir    = Path("/home/jovyan/scripts")
bronze_parquet = "/home/jovyan/data/bronze/ipums_bronze.parquet"
silver_script  = str(scripts_dir / "silver_layer.py")
gold_script    = str(scripts_dir / "gold_layer.py")
bronze_read_script = "/tmp/bronze_read_bench.py"

# ── Tulis script bronze read ke file agar bisa dijalankan via spark-submit ──
BRONZE_READ_CODE = f"""
import time
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("Benchmark - Bronze Read")
    .master("local[*]")
    .config("spark.driver.memory", "4g")
    .config("spark.driver.extraJavaOptions", "-Dlog4j.rootCategory=ERROR,console")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

t0 = time.time()
df = spark.read.parquet("{bronze_parquet}")
n  = df.count()
t1 = time.time()

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger(__name__).info(f"Bronze Read selesai: {{n}} baris, {{t1-t0:.2f}}s")
spark.stop()
"""

def write_bronze_read_script():
    """Tulis script bronze read ke /tmp agar bisa dijalankan spark-submit."""
    with open(bronze_read_script, "w") as f:
        f.write(BRONZE_READ_CODE)


def run_spark_submit(name: str, script_path: str) -> float:
    """Jalankan spark-submit dan kembalikan durasi (detik)."""
    print(f"[{time.strftime('%H:%M:%S')}] ▶  {name}...", flush=True)
    start = time.time()
    result = subprocess.run(
        ["spark-submit", script_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    duration = time.time() - start

    if result.returncode != 0:
        print(f"❌ {name} GAGAL (exit {result.returncode})", flush=True)
        print("--- STDERR (tail) ---", flush=True)
        print(result.stderr[-2000:], flush=True)
        sys.exit(1)

    # Tampilkan baris INFO dari stderr (Spark log ke stderr)
    for line in result.stderr.splitlines():
        if "[INFO]" in line and ("selesai" in line or "berhasil" in line or "Bronze Read" in line):
            print(f"   ℹ️  {line.strip()}", flush=True)

    print(f"✅ {name} selesai dalam {duration:.2f} detik.", flush=True)
    return duration


def fmt(seconds: float) -> str:
    return f"{seconds:.2f}s ({seconds/60:.2f}m)"


def main():
    # Pastikan bronze parquet sudah ada
    check = subprocess.run(
        ["test", "-e", bronze_parquet],
        capture_output=True
    )
    # test -e tidak tersedia langsung, pakai python3 bawaan
    check2 = subprocess.run(
        ["python3", "-c", f"import sys; from pathlib import Path; sys.exit(0 if Path('{bronze_parquet}').exists() else 1)"],
        capture_output=True
    )
    if check2.returncode != 0:
        print(f"❌ Bronze parquet tidak ditemukan: {bronze_parquet}", flush=True)
        print("   Jalankan bronze_layer.py (ingest dari CSV) terlebih dahulu.", flush=True)
        sys.exit(1)

    print(f"✅ Bronze parquet ditemukan: {bronze_parquet}\n", flush=True)

    # Tulis script bronze read ke /tmp
    write_bronze_read_script()

    print("=" * 80, flush=True)
    print("   SDG-10 PIPELINE BENCHMARK — 3 ITERASI (via spark-submit)", flush=True)
    print("   Bronze = baca parquet  |  Silver = transformasi  |  Gold = agregasi", flush=True)
    print("=" * 80, flush=True)

    results = []

    for i in range(1, 4):
        print(f"\n{'─'*40}", flush=True)
        print(f"  🔄 ITERASI {i} / 3", flush=True)
        print(f"{'─'*40}", flush=True)

        t_bronze = run_spark_submit("Bronze Read  (spark-submit)", bronze_read_script)
        t_silver = run_spark_submit("Silver Layer (spark-submit)", silver_script)
        t_gold   = run_spark_submit("Gold Layer   (spark-submit)", gold_script)
        t_total  = t_bronze + t_silver + t_gold

        print(f"\n⏱️  Iterasi {i}: Bronze={t_bronze:.2f}s | Silver={t_silver:.2f}s | Gold={t_gold:.2f}s | Total={fmt(t_total)}", flush=True)

        results.append({
            "Iterasi":    i,
            "Bronze (s)": round(t_bronze, 2),
            "Silver (s)": round(t_silver, 2),
            "Gold (s)":   round(t_gold, 2),
            "Total (s)":  round(t_total, 2),
            "Total (m)":  round(t_total / 60, 2),
        })

    # ── Hitung rata-rata ────────────────────────────────────────────────────
    avg = {k: sum(r[k] for r in results) / 3
           for k in ["Bronze (s)", "Silver (s)", "Gold (s)", "Total (s)"]}
    avg["Total (m)"] = avg["Total (s)"] / 60

    # ── Cetak tabel ringkasan ───────────────────────────────────────────────
    print("\n" + "=" * 80, flush=True)
    print("  📊 RINGKASAN HASIL BENCHMARK", flush=True)
    print("=" * 80, flush=True)
    print(f"{'Iterasi':<10} | {'Bronze (s)':<12} | {'Silver (s)':<12} | {'Gold (s)':<12} | {'Total (s)':<12} | {'Total (m)':<10}", flush=True)
    print("-" * 80, flush=True)
    for r in results:
        print(f"{r['Iterasi']:<10} | {r['Bronze (s)']:<12} | {r['Silver (s)']:<12} | {r['Gold (s)']:<12} | {r['Total (s)']:<12} | {r['Total (m)']:<10}", flush=True)
    print("-" * 80, flush=True)
    print(f"{'Rata-rata':<10} | {avg['Bronze (s)']:<12.2f} | {avg['Silver (s)']:<12.2f} | {avg['Gold (s)']:<12.2f} | {avg['Total (s)']:<12.2f} | {avg['Total (m)']:<10.2f}", flush=True)
    print("=" * 80, flush=True)

    # ── Simpan markdown report ──────────────────────────────────────────────
    doc_path = Path("/home/jovyan/docs/benchmark_report.md")
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    with open(doc_path, "w") as f:
        f.write("# SDG-10 Pipeline Execution Benchmark Report\n\n")
        f.write("Benchmark dijalankan selama **3 iterasi penuh** pada Medallion Pipeline (Bronze → Silver → Gold).\n\n")
        f.write("> **Catatan:** Semua step dijalankan via `spark-submit`.\n")
        f.write("> Step _Bronze_ hanya mengukur waktu **membaca** `bronze.parquet` yang sudah tersedia\n")
        f.write("> (bukan re-ingest dari CSV). Step _Silver_ dan _Gold_ melakukan transformasi & agregasi penuh.\n\n")
        f.write("## Hasil Pengukuran Waktu\n\n")
        f.write("| Iterasi | Bronze (s) | Silver (s) | Gold (s) | Total (s) | Total (m) |\n")
        f.write("|:-------:|:----------:|:----------:|:--------:|:---------:|:---------:|\n")
        for r in results:
            f.write(f"| {r['Iterasi']} | {r['Bronze (s)']} | {r['Silver (s)']} | {r['Gold (s)']} | {r['Total (s)']} | {r['Total (m)']} |\n")
        f.write(f"| **Rata-rata** | **{avg['Bronze (s)']:.2f}** | **{avg['Silver (s)']:.2f}** | **{avg['Gold (s)']:.2f}** | **{avg['Total (s)']:.2f}** | **{avg['Total (m)']:.2f}** |\n\n")
        f.write("## Detail Sistem\n\n")
        f.write("| Parameter | Nilai |\n")
        f.write("|-----------|-------|\n")
        f.write("| Engine | Apache Spark (PySpark) via `spark-submit` |\n")
        f.write("| Deploy Mode | Local (`local[*]`) inside Docker |\n")
        f.write("| Ukuran Data | ~32.5 juta baris (raw IPUMS CSV ~2.3 GB) |\n")
        f.write("| Bronze Input | `bronze.parquet` (sudah tersedia, tidak re-ingest) |\n")
        f.write("| Silver Output | `silver.parquet` (partisi per COUNTRY) |\n")
        f.write("| Gold Output | `gold_gini.parquet`, `gold_quintile.parquet`, dll. |\n")

    print(f"\n📄 Laporan disimpan ke: {doc_path}", flush=True)
    print("🏁 Benchmark selesai!\n", flush=True)


if __name__ == "__main__":
    main()
