from __future__ import annotations
import pandas as pd
import numpy as np
from numpy.linalg import norm


def compute_similarity(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    """Compute simple similarity metrics between two composite windows.

    Returns:
      {
        'pearson': float,
        'cosine': float,
        'dtw_like': float  # crude alignment-free measure
      }
    """
    if a is None or a.empty or b is None or b.empty:
        return {'pearson': np.nan, 'cosine': np.nan, 'dtw_like': np.nan}

    # Align by index length via interpolation to common length
    n = min(len(a), len(b))
    if n < 3:
        return {'pearson': np.nan, 'cosine': np.nan, 'dtw_like': np.nan}

    def to_array(df):
        s = df['composite'].astype(float)
        x = np.linspace(0, 1, len(s))
        xi = np.linspace(0, 1, n)
        return np.interp(xi, x, s.values)

    va = to_array(a)
    vb = to_array(b)

    # Pearson correlation
    pearson = float(np.corrcoef(va, vb)[0, 1])

    # Cosine similarity
    cosine = float(np.dot(va, vb) / (norm(va) * norm(vb) + 1e-12))

    # DTW-like: inverse of average absolute difference after min-max scaling
    def minmax(x):
        mn, mx = np.min(x), np.max(x)
        if mx - mn < 1e-12:
            return x * 0
        return (x - mn) / (mx - mn)

    da = minmax(va)
    db = minmax(vb)
    mae = float(np.mean(np.abs(da - db)))
    dtw_like = float(1 - mae)  # 1 identical, 0 very different

    return {
        'pearson': round(pearson, 3),
        'cosine': round(cosine, 3),
        'dtw_like': round(dtww := dtw_like, 3)
    }
