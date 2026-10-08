"""
FoundIt AI pipeline - step 3a: plain-numpy similarity helpers.

With ~20 demo items, comparing vectors in memory is instant. No vector DB required.
"""
from __future__ import annotations

import numpy as np


def cosine(a, b) -> float:
    """Cosine similarity of two vectors (lists or arrays). Returns 0.0 for empty/zero vectors."""
    if a is None or b is None:
        return 0.0
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(a @ b / denom)


def minmax(values: list[float]) -> list[float]:
    """Rescale to 0..1 so scores from different comparison types can be averaged.
    If every value is equal, return 0.5 for all (no ranking signal)."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def top_k(scored: list[dict], k: int) -> list[dict]:
    """Sort dicts that have a 'score' key, best first, keep k."""
    return sorted(scored, key=lambda d: d["score"], reverse=True)[:k]
