# ==============================================================================
# test_gini.py — Unit tests untuk fungsi Gini Coefficient dan metrik lainnya
# ==============================================================================

import sys
import numpy as np
import pytest
from pathlib import Path

# Tambahkan scripts ke path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from utils import (
    gini_coefficient,
    theil_index,
    mean_log_deviation,
    quintile_shares,
    palma_ratio,
    lorenz_curve,
)


# ──────────────────────────────────────────────────────────────────────────────
# GINI COEFFICIENT TESTS
# ──────────────────────────────────────────────────────────────────────────────

class TestGiniCoefficient:
    def test_perfect_equality(self):
        """Semua orang punya pendapatan sama → Gini = 0."""
        values = np.array([1000.0] * 100)
        result = gini_coefficient(values)
        assert abs(result) < 1e-6, f"Expected ~0, got {result}"

    def test_perfect_inequality(self):
        """Satu orang punya semua pendapatan → Gini mendekati 1."""
        values = np.zeros(100)
        values[-1] = 100000.0
        result = gini_coefficient(values)
        assert result > 0.98, f"Expected ~1, got {result}"

    def test_gini_range(self):
        """Gini harus selalu antara 0 dan 1."""
        np.random.seed(42)
        values = np.random.lognormal(mean=10, sigma=1.5, size=1000)
        result = gini_coefficient(values)
        assert 0.0 <= result <= 1.0, f"Gini out of range: {result}"

    def test_with_weights(self):
        """Gini dengan weights tidak boleh error dan harus dalam range."""
        np.random.seed(0)
        values  = np.random.exponential(scale=50000, size=500)
        weights = np.random.uniform(0.5, 2.0, size=500)
        result  = gini_coefficient(values, weights)
        assert 0.0 <= result <= 1.0

    def test_single_value(self):
        """Dataset dengan satu nilai → Gini = 0."""
        result = gini_coefficient(np.array([5000.0]))
        assert result == 0.0 or np.isnan(result)

    def test_negative_values_removed(self):
        """Nilai negatif harus diabaikan."""
        values = np.array([-100.0, 1000.0, 2000.0, 3000.0])
        result = gini_coefficient(values)
        assert 0.0 <= result <= 1.0

    def test_known_value(self):
        """
        Untuk distribusi uniform [1, 2, 3, ..., n]:
        Gini = (n-1) / (2n - 1) ≈ 0.33 untuk n besar.
        """
        n = 1000
        values = np.arange(1, n + 1, dtype=float)
        result = gini_coefficient(values)
        expected = (n - 1) / (2 * n - 1)
        assert abs(result - expected) < 0.01, f"Expected ~{expected:.4f}, got {result:.4f}"


# ──────────────────────────────────────────────────────────────────────────────
# THEIL INDEX TESTS
# ──────────────────────────────────────────────────────────────────────────────

class TestTheilIndex:
    def test_perfect_equality(self):
        """Semua sama → Theil = 0."""
        values = np.array([5000.0] * 200)
        result = theil_index(values)
        assert abs(result) < 1e-10, f"Expected 0, got {result}"

    def test_theil_positive(self):
        """Theil harus selalu >= 0."""
        np.random.seed(7)
        values = np.random.lognormal(10, 2, 1000)
        result = theil_index(values)
        assert result >= 0, f"Theil negative: {result}"

    def test_zero_values_excluded(self):
        """Nilai 0 tidak boleh menyebabkan error (log(0) = -inf)."""
        values = np.array([0.0, 0.0, 5000.0, 10000.0, 50000.0])
        result = theil_index(values)
        assert np.isfinite(result), "Theil harus finite meski ada nilai 0"


# ──────────────────────────────────────────────────────────────────────────────
# QUINTILE SHARES TESTS
# ──────────────────────────────────────────────────────────────────────────────

class TestQuintileShares:
    def test_returns_correct_n_rows(self):
        """Harus mengembalikan 5 baris untuk quintile."""
        np.random.seed(1)
        values = np.random.lognormal(10, 1, 1000)
        result = quintile_shares(values, n=5)
        assert len(result) == 5

    def test_income_shares_sum_to_one(self):
        """Total share harus ≈ 1.0."""
        np.random.seed(2)
        values = np.random.exponential(50000, 1000)
        result = quintile_shares(values)
        total_share = result["income_share"].sum()
        assert abs(total_share - 1.0) < 0.01, f"Total share: {total_share}"

    def test_perfect_equality_equal_shares(self):
        """Dengan distribusi sempurna merata, setiap quintile ≈ 20%."""
        values = np.ones(1000) * 10000
        result = quintile_shares(values)
        for share in result["income_share"]:
            assert abs(share - 0.2) < 0.05, f"Share tidak merata: {share}"


# ──────────────────────────────────────────────────────────────────────────────
# PALMA RATIO TESTS
# ──────────────────────────────────────────────────────────────────────────────

class TestPalmaRatio:
    def test_palma_equal_distribution(self):
        """Distribusi merata → Palma ≈ 10/40 = 0.25."""
        values = np.ones(1000) * 10000
        result = palma_ratio(values)
        # 10% teratas / 40% terbawah = 10/40 = 0.25
        assert abs(result - 0.25) < 0.05, f"Expected ~0.25, got {result}"

    def test_palma_positive(self):
        """Palma Ratio harus positif."""
        np.random.seed(42)
        values = np.random.lognormal(10, 1.5, 1000)
        result = palma_ratio(values)
        assert result > 0


# ──────────────────────────────────────────────────────────────────────────────
# LORENZ CURVE TESTS
# ──────────────────────────────────────────────────────────────────────────────

class TestLorenzCurve:
    def test_starts_at_zero(self):
        """Kurva Lorenz harus mulai dari (0, 0)."""
        values = np.random.lognormal(10, 1, 200)
        result = lorenz_curve(values)
        assert result["cum_population"].iloc[0] == 0.0
        assert result["cum_income"].iloc[0] == 0.0

    def test_ends_at_one(self):
        """Kurva Lorenz harus berakhir di (1, 1)."""
        values = np.random.lognormal(10, 1, 200)
        result = lorenz_curve(values)
        assert abs(result["cum_population"].iloc[-1] - 1.0) < 1e-6
        assert abs(result["cum_income"].iloc[-1] - 1.0) < 1e-6

    def test_monotonically_increasing(self):
        """Nilai kumulatif harus monoton meningkat."""
        values = np.random.lognormal(10, 1, 500)
        result = lorenz_curve(values)
        assert (result["cum_income"].diff().dropna() >= -1e-9).all()


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
