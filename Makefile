# ==============================================================================
# Makefile — SDG-10 Big Data ITS
# ==============================================================================

.PHONY: help setup pipeline bronze silver gold dashboard test clean docker-up docker-down

# Default target
help:
	@echo ""
	@echo "  SDG-10 Big Data ITS — Available Commands"
	@echo "  ==========================================="
	@echo "  make setup       Install semua dependensi Python"
	@echo "  make pipeline    Jalankan full pipeline (bronze → silver → gold)"
	@echo "  make bronze      Jalankan Bronze Layer saja"
	@echo "  make silver      Jalankan Silver Layer saja"
	@echo "  make gold        Jalankan Gold Layer saja"
	@echo "  make dashboard   Jalankan Streamlit Dashboard"
	@echo "  make test        Jalankan semua unit tests"
	@echo "  make docker-up   Jalankan Spark cluster via Docker Compose"
	@echo "  make docker-down Hentikan Docker cluster"
	@echo "  make clean       Bersihkan data bronze/silver/gold (hati-hati!)"
	@echo ""

# ── Setup ──────────────────────────────────────────────────────────────────────
setup:
	pip install -r requirements.txt

# ── Pipeline ───────────────────────────────────────────────────────────────────
pipeline: bronze silver gold
	@echo "✅ Full pipeline selesai!"

bronze:
	@echo "🔄 Menjalankan Bronze Layer..."
	python scripts/bronze_layer.py

silver:
	@echo "🔄 Menjalankan Silver Layer..."
	python scripts/silver_layer.py

gold:
	@echo "🔄 Menjalankan Gold Layer..."
	python scripts/gold_layer.py

# ── Dashboard ──────────────────────────────────────────────────────────────────
dashboard:
	@echo "🚀 Menjalankan Streamlit Dashboard..."
	streamlit run dashboard/dashboard.py

# ── Testing ────────────────────────────────────────────────────────────────────
test:
	@echo "🧪 Menjalankan unit tests..."
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=scripts --cov-report=html
	@echo "📊 Coverage report: htmlcov/index.html"

# ── Docker ─────────────────────────────────────────────────────────────────────
docker-up:
	@echo "🐳 Menjalankan Spark cluster..."
	docker-compose -f docker/docker-compose.yml up -d
	@echo "Spark UI: http://localhost:8080"
	@echo "Dashboard: http://localhost:8501"

docker-down:
	docker-compose -f docker/docker-compose.yml down

docker-logs:
	docker-compose -f docker/docker-compose.yml logs -f

# ── Cleanup ────────────────────────────────────────────────────────────────────
clean:
	@echo "⚠️  Menghapus data bronze/silver/gold..."
	rm -rf data/bronze/* data/silver/* data/gold/*
	@echo "✅ Data layer dibersihkan."

clean-cache:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name ".ipynb_checkpoints" -exec rm -rf {} +
