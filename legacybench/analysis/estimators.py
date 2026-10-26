"""Estimators for the pre-registered analysis.

All functions take plain sequences so they can be unit-tested and reused outside
Inspect. References: Miller 2024 (paired and clustered SEs), Wilson 1927 (small-n
pass-rate interval), Chen et al. 2021 (unbiased pass@k), Yao et al. 2024 (pass^k).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np
from scipy.stats import norm, t as student_t


@dataclass(frozen=True)
class Interval:
    estimate: float
    low: float
    high: float
    se: float | None = None
    n: int | None = None


def wilson(successes: int, n: int, alpha: float = 0.05) -> Interval:
    if n <= 0:
        raise ValueError("n must be > 0")
    z = norm.ppf(1 - alpha / 2)
    p = successes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return Interval(p, max(0.0, centre - half), min(1.0, centre + half), n=n)


def mean_ci(values: Sequence[float], alpha: float = 0.05) -> Interval:
    x = np.asarray(values, dtype=float)
    n = len(x)
    if n < 2:
        return Interval(float(x.mean()) if n else math.nan, math.nan, math.nan, None, n)
    se = float(x.std(ddof=1) / math.sqrt(n))
    tcrit = student_t.ppf(1 - alpha / 2, n - 1)
    m = float(x.mean())
    return Interval(m, m - tcrit * se, m + tcrit * se, se, n)


def paired_difference(a: Sequence[float], b: Sequence[float], alpha: float = 0.05) -> dict:
    """Mean of per-task differences a_i - b_i with a t interval and the pairing correlation."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.shape != b.shape:
        raise ValueError("a and b must align task-by-task")
    d = a - b
    ci = mean_ci(d, alpha)
    rho = float(np.corrcoef(a, b)[0, 1]) if len(a) > 2 and a.std() > 0 and b.std() > 0 else math.nan
    return {"diff": ci.estimate, "low": ci.low, "high": ci.high, "se": ci.se, "n": ci.n, "rho": rho}


def clustered_se(values: Sequence[float], clusters: Sequence[str]) -> float:
    """Cluster-robust SE of the mean (Miller 2024 rec. 2)."""
    x = np.asarray(values, dtype=float)
    c = np.asarray(clusters)
    n = len(x)
    mean = x.mean()
    resid = x - mean
    total = 0.0
    for g in np.unique(c):
        u = resid[c == g].sum()
        total += u * u
    return math.sqrt(total) / n


def bootstrap_ci(
    values: Sequence[float],
    stat: Callable[[np.ndarray], float] = np.mean,
    n_boot: int = 5000,
    alpha: float = 0.05,
    seed: int = 0,
) -> Interval:
    x = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    boots = np.array([stat(x[i]) for i in idx])
    return Interval(float(stat(x)), float(np.quantile(boots, alpha / 2)), float(np.quantile(boots, 1 - alpha / 2)), None, len(x))


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k)."""
    if k > n:
        raise ValueError("k must be <= n")
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k reliability estimator (tau-bench): C(c, k) / C(n, k)."""
    if k > n:
        raise ValueError("k must be <= n")
    if c < k:
        return 0.0
    return math.comb(c, k) / math.comb(n, k)


def mcnemar_exact(b: int, c: int) -> float:
    """Exact two-sided McNemar p-value from discordant counts (A right/B wrong = b, reverse = c)."""
    from scipy.stats import binomtest

    n = b + c
    if n == 0:
        return 1.0
    return float(binomtest(b, n, 0.5).pvalue)


def holm(pvalues: Sequence[float]) -> list[float]:
    """Holm step-down adjusted p-values."""
    p = np.asarray(pvalues, dtype=float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        val = min(1.0, (m - rank) * p[i])
        running = max(running, val)
        adj[i] = running
    return adj.tolist()
