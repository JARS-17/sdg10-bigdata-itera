import pandas as pd
from pathlib import Path

# Definisikan path data di dalam container
data_dir = Path("/home/jovyan/data")
bronze_path = data_dir / "bronze/ipums_bronze.parquet"
silver_path = data_dir / "silver/ipums_silver.parquet"
gold_dir = data_dir / "gold"

def show_bronze():
    print("\n" + "="*80)
    print(" 🟫 SAMPLE BRONZE LAYER (First 100 Rows) ")
    print("="*80)
    if bronze_path.exists():
        # Membaca hanya 100 baris pertama
        df = pd.read_parquet(bronze_path).head(100)
        # Menampilkan tabel dengan lebar penuh kolom
        with pd.option_context('display.max_columns', None, 'display.width', 1000):
            print(df)
        print(f"\nTotal kolom di Bronze: {len(df.columns)}")
    else:
        print(f"Path tidak ditemukan: {bronze_path}")

def show_silver():
    print("\n" + "="*80)
    print(" ⬜ SAMPLE SILVER LAYER (First 100 Rows) ")
    print("="*80)
    if silver_path.exists():
        # Membaca hanya 100 baris pertama
        df = pd.read_parquet(silver_path).head(100)
        with pd.option_context('display.max_columns', None, 'display.width', 1000):
            print(df)
        print(f"\nTotal kolom di Silver: {len(df.columns)}")
    else:
        print(f"Path tidak ditemukan: {silver_path}")

def show_gold():
    print("\n" + "="*80)
    print(" 🟨 GOLD LAYER TABLES ")
    print("="*80)
    
    # 1. Gini & SDG Metrics
    gini_path = gold_dir / "gold_gini_by_year.parquet"
    if gini_path.exists():
        print("\n--- Gini & SDG 10.2.1 Metrics (gold_gini_by_year.parquet) ---")
        df = pd.read_parquet(gini_path).head(100)
        with pd.option_context('display.max_columns', None, 'display.width', 1000):
            print(df)
            
    # 2. Quintiles
    quintile_path = gold_dir / "gold_quintile_by_year.parquet"
    if quintile_path.exists():
        print("\n--- Quintile Distribution (gold_quintile_by_year.parquet) ---")
        df = pd.read_parquet(quintile_path).head(100)
        with pd.option_context('display.max_columns', None, 'display.width', 1000):
            print(df)

    # 3. Descriptive Stats
    theil_path = gold_dir / "gold_theil_by_year.parquet"
    if theil_path.exists():
        print("\n--- Descriptive Income Stats (gold_theil_by_year.parquet) ---")
        df = pd.read_parquet(theil_path).head(100)
        with pd.option_context('display.max_columns', None, 'display.width', 1000):
            print(df)

if __name__ == "__main__":
    import sys
    # Bisa dipanggil dengan argumen: 'bronze', 'silver', 'gold', atau tanpa argumen untuk semuanya
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    
    if arg == "bronze":
        show_bronze()
    elif arg == "silver":
        show_silver()
    elif arg == "gold":
        show_gold()
    else:
        show_bronze()
        show_silver()
        show_gold()

