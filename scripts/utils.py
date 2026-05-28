# ==============================================================================
# utils.py — Fungsi utilitas: Gini, Theil, Quintile, Palma, dsb.
# ==============================================================================

import numpy as np
import pandas as pd
from typing import Union, Optional


# ──────────────────────────────────────────────────────────────────────────────
# GINI COEFFICIENT
# ──────────────────────────────────────────────────────────────────────────────

def gini_coefficient(values: Union[np.ndarray, pd.Series],
                     weights: Optional[Union[np.ndarray, pd.Series]] = None) -> float:
    """
    Hitung Gini Coefficient dari distribusi pendapatan.

    Parameters
    ----------
    values  : array-like, nilai pendapatan (harus >= 0)
    weights : array-like opsional, bobot survei (mis. WTFINL dari IPUMS)

    Returns
    -------
    float   : nilai Gini antara 0 (merata sempurna) dan 1 (tidak merata sempurna)

    References
    ----------
    Dorfman (1979), "A Formula for the Gini Coefficient"
    """
    values = np.asarray(values, dtype=float)
    values = values[values >= 0]  # buang nilai negatif

    if len(values) == 0:
        return np.nan

    if weights is None:
        weights = np.ones_like(values)
    else:
        weights = np.asarray(weights, dtype=float)

    # Urutkan berdasarkan nilai
    sorted_idx = np.argsort(values)
    values  = values[sorted_idx]
    weights = weights[sorted_idx]

    # Hitung kumulatif tertimbang
    cumulative_weights = np.cumsum(weights)
    total_weight = cumulative_weights[-1]

    # Formula Gini tertimbang
    weighted_sum = np.sum(weights * values)
    if weighted_sum == 0:
        return 0.0

    gini = (2 * np.sum(weights * values * cumulative_weights) / (total_weight * weighted_sum)) - (
        (total_weight + 1) / total_weight
    )
    return float(np.clip(gini, 0.0, 1.0))


# ──────────────────────────────────────────────────────────────────────────────
# THEIL INDEX (T-statistic / GE(1))
# ──────────────────────────────────────────────────────────────────────────────

def theil_index(values: Union[np.ndarray, pd.Series],
                weights: Optional[Union[np.ndarray, pd.Series]] = None) -> float:
    """
    Hitung Theil T-Index (Generalized Entropy GE(1)).

    T = (1/n) * Σ (y_i / ȳ) * ln(y_i / ȳ)

    Parameters
    ----------
    values  : array-like, nilai pendapatan (> 0)
    weights : array-like opsional, bobot survei

    Returns
    -------
    float   : nilai Theil (0 = merata, semakin besar semakin tidak merata)
    """
    values = np.asarray(values, dtype=float)
    mask   = values > 0
    values = values[mask]

    if len(values) == 0:
        return np.nan

    if weights is None:
        weights = np.ones_like(values)
    else:
        weights = np.asarray(weights, dtype=float)[mask]

    mean_income = np.average(values, weights=weights)
    if mean_income == 0:
        return np.nan

    ratio = values / mean_income
    theil = np.average(ratio * np.log(ratio), weights=weights)
    return float(theil)


# ──────────────────────────────────────────────────────────────────────────────
# MEAN LOG DEVIATION (Theil L / GE(0))
# ──────────────────────────────────────────────────────────────────────────────

def mean_log_deviation(values: Union[np.ndarray, pd.Series],
                       weights: Optional[Union[np.ndarray, pd.Series]] = None) -> float:
    """
    Hitung Mean Log Deviation (Theil L / GE(0)).

    L = (1/n) * Σ ln(ȳ / y_i)
    """
    values = np.asarray(values, dtype=float)
    mask   = values > 0
    values = values[mask]

    if len(values) == 0:
        return np.nan

    if weights is None:
        weights = np.ones_like(values)
    else:
        weights = np.asarray(weights, dtype=float)[mask]

    mean_income = np.average(values, weights=weights)
    if mean_income == 0:
        return np.nan

    mld = np.average(np.log(mean_income / values), weights=weights)
    return float(mld)


# ──────────────────────────────────────────────────────────────────────────────
# QUINTILE SHARES
# ──────────────────────────────────────────────────────────────────────────────

def quintile_shares(values: Union[np.ndarray, pd.Series],
                    weights: Optional[Union[np.ndarray, pd.Series]] = None,
                    n: int = 5) -> pd.DataFrame:
    """
    Hitung share pendapatan tiap kuantil (quintile/decile).

    Parameters
    ----------
    values  : array-like, nilai pendapatan
    weights : array-like opsional, bobot survei
    n       : jumlah kuantil (default 5 = quintile)

    Returns
    -------
    pd.DataFrame dengan kolom: quantile, lower_bound, upper_bound,
                                mean_income, income_share
    """
    values = np.asarray(values, dtype=float)
    if weights is None:
        weights = np.ones_like(values)
    else:
        weights = np.asarray(weights, dtype=float)

    # Filter negatif
    mask    = values >= 0
    values  = values[mask]
    weights = weights[mask]

    # Sortir
    sorted_idx = np.argsort(values)
    values  = values[sorted_idx]
    weights = weights[sorted_idx]

    # Hitung batas kuantil berdasarkan cumulative weight
    cum_w     = np.cumsum(weights)
    total_w   = cum_w[-1]
    quantiles = np.arange(1, n + 1) / n * total_w

    results = []
    prev_bound = 0.0
    total_income = np.sum(values * weights)

    for q_idx, q_limit in enumerate(quantiles):
        in_q   = (cum_w > prev_bound) & (cum_w <= q_limit)
        if q_idx == n - 1:
            in_q = cum_w > prev_bound  # pastikan semua masuk kuantil terakhir

        q_values  = values[in_q]
        q_weights = weights[in_q]

        if len(q_values) == 0:
            continue

        q_income = np.sum(q_values * q_weights)
        results.append({
            "quantile":      q_idx + 1,
            "lower_bound":   q_values.min(),
            "upper_bound":   q_values.max(),
            "mean_income":   np.average(q_values, weights=q_weights),
            "income_share":  q_income / total_income if total_income > 0 else 0.0,
        })
        prev_bound = q_limit

    return pd.DataFrame(results)


# ──────────────────────────────────────────────────────────────────────────────
# PALMA RATIO
# ──────────────────────────────────────────────────────────────────────────────

def palma_ratio(values: Union[np.ndarray, pd.Series],
                weights: Optional[Union[np.ndarray, pd.Series]] = None) -> float:
    """
    Hitung Palma Ratio = share pendapatan 10% teratas / share 40% terbawah.

    Parameters
    ----------
    values  : array-like, nilai pendapatan
    weights : array-like opsional, bobot survei

    Returns
    -------
    float   : Palma Ratio (> 1 = ketimpangan; semakin besar semakin timpang)
    """
    values = np.asarray(values, dtype=float)
    if weights is None:
        weights = np.ones_like(values)
    else:
        weights = np.asarray(weights, dtype=float)

    mask    = values >= 0
    values  = values[mask]
    weights = weights[mask]

    sorted_idx = np.argsort(values)
    values  = values[sorted_idx]
    weights = weights[sorted_idx]

    cum_w   = np.cumsum(weights)
    total_w = cum_w[-1]

    # 40% terbawah
    bottom_40 = values[cum_w <= 0.40 * total_w]
    w_bottom  = weights[cum_w <= 0.40 * total_w]

    # 10% teratas
    top_10  = values[cum_w > 0.90 * total_w]
    w_top   = weights[cum_w > 0.90 * total_w]

    share_bottom = np.sum(bottom_40 * w_bottom)
    share_top    = np.sum(top_10 * w_top)

    if share_bottom == 0:
        return np.nan

    return float(share_top / share_bottom)


# ──────────────────────────────────────────────────────────────────────────────
# LORENZ CURVE DATA
# ──────────────────────────────────────────────────────────────────────────────

def lorenz_curve(values: Union[np.ndarray, pd.Series],
                 weights: Optional[Union[np.ndarray, pd.Series]] = None,
                 n_points: int = 100) -> pd.DataFrame:
    """
    Hitung data Kurva Lorenz.

    Returns
    -------
    pd.DataFrame dengan kolom: cum_population, cum_income
    """
    values = np.asarray(values, dtype=float)
    if weights is None:
        weights = np.ones_like(values)
    else:
        weights = np.asarray(weights, dtype=float)

    mask    = values >= 0
    values  = values[mask]
    weights = weights[mask]

    sorted_idx = np.argsort(values)
    values  = values[sorted_idx]
    weights = weights[sorted_idx]

    cum_w = np.cumsum(weights) / np.sum(weights)
    cum_y = np.cumsum(values * weights) / np.sum(values * weights)

    # Tambahkan titik origin
    cum_w = np.concatenate([[0], cum_w])
    cum_y = np.concatenate([[0], cum_y])

    return pd.DataFrame({"cum_population": cum_w, "cum_income": cum_y})
