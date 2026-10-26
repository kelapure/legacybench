"""Power and minimum-detectable-effect for a paired two-model comparison.

Model (Miller 2024, arXiv 2411.00640, with the k-run extension):
    per-task paired difference d_i has variance  Var(d) = 2 B (1 - rho) + 2 W / k
where B is between-task variance of true task means, W is mean within-task
(run-to-run) variance, rho is the across-model correlation of task means, and k is
runs per task. For pass rates, B + W = p(1-p), at most 0.25.

    n_tasks = (z_{1-alpha/2} + z_{1-beta})^2 * Var(d) / delta^2

Default scenario (Miller's illustrative split): B = 1/12, W = 1/6, rho = 0.5.
"""

from __future__ import annotations

import math

from scipy.stats import norm


def var_paired_diff(B: float = 1 / 12, W: float = 1 / 6, rho: float = 0.5, k: int = 1) -> float:
    if k < 1:
        raise ValueError("k must be >= 1")
    return 2.0 * B * (1.0 - rho) + 2.0 * W / k


def z_factor(alpha: float = 0.05, power: float = 0.8) -> float:
    return (norm.ppf(1 - alpha / 2) + norm.ppf(power)) ** 2


def n_tasks(
    delta: float,
    *,
    B: float = 1 / 12,
    W: float = 1 / 6,
    rho: float = 0.5,
    k: int = 1,
    alpha: float = 0.05,
    power: float = 0.8,
    design_effect: float = 1.0,
) -> int:
    """Tasks needed to detect a difference `delta` (in score units, e.g. 0.05 = 5 points)."""
    if delta <= 0:
        raise ValueError("delta must be > 0")
    n = z_factor(alpha, power) * var_paired_diff(B, W, rho, k) / delta**2
    return math.ceil(n * design_effect)


def mde(
    n: int,
    *,
    B: float = 1 / 12,
    W: float = 1 / 6,
    rho: float = 0.5,
    k: int = 1,
    alpha: float = 0.05,
    power: float = 0.8,
    design_effect: float = 1.0,
) -> float:
    """Minimum detectable difference at `n` tasks."""
    if n <= 0:
        raise ValueError("n must be > 0")
    return math.sqrt(z_factor(alpha, power) * var_paired_diff(B, W, rho, k) * design_effect / n)


def design_effect(mean_cluster_size: float, icc: float) -> float:
    """1 + (m - 1) * ICC for tasks clustered by repo or family."""
    return 1.0 + (mean_cluster_size - 1.0) * icc


def table(deltas=(0.05, 0.10, 0.15), ks=(1, 3, 5), **scenario) -> dict[int, dict[float, int]]:
    return {k: {d: n_tasks(d, k=k, **scenario) for d in deltas} for k in ks}
