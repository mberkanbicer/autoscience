"""Statistical power analysis utilities."""

from __future__ import annotations

import math
from dataclasses import dataclass


def _norm_ppf(p: float) -> float:
    """Approximate inverse CDF for standard normal (Acklam's approximation)."""
    if p <= 0 or p >= 1:
        raise ValueError("p must be between 0 and 1")
    a = [
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    ]
    b = [
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    ]
    c = [
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758227161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    ]
    d = [
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661761397e00,
    ]
    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
        )
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
        )
    q = p - 0.5
    r = q * q
    return (
        (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
        / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    )


@dataclass
class PowerAnalysisResult:
    test_type: str
    effect_size: float
    alpha: float
    power: float
    sample_size_per_group: int | None
    total_sample_size: int | None
    recommendation: str

    def as_dict(self) -> dict:
        return {
            "test_type": self.test_type,
            "effect_size": self.effect_size,
            "alpha": self.alpha,
            "power": self.power,
            "sample_size_per_group": self.sample_size_per_group,
            "total_sample_size": self.total_sample_size,
            "recommendation": self.recommendation,
        }


def two_sample_ttest_power(
    effect_size: float,
    *,
    alpha: float = 0.05,
    power: float = 0.8,
    ratio: float = 1.0,
) -> PowerAnalysisResult:
    """Compute per-group sample size for a two-sample t-test (Cohen's d)."""
    if effect_size <= 0:
        raise ValueError("effect_size must be positive")
    z_alpha = _norm_ppf(1 - alpha / 2)
    z_beta = _norm_ppf(power)
    n1 = math.ceil(((z_alpha + z_beta) / effect_size) ** 2)
    n2 = math.ceil(n1 * ratio)
    total = n1 + n2
    rec = (
        f"Target power {power:.0%} at α={alpha}: "
        f"allocate n≈{n1} per group (total n≈{total}) for d={effect_size:.2f}."
    )
    return PowerAnalysisResult(
        test_type="two_sample_ttest",
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        sample_size_per_group=n1,
        total_sample_size=total,
        recommendation=rec,
    )


def proportion_test_power(
    p1: float,
    p2: float,
    *,
    alpha: float = 0.05,
    power: float = 0.8,
) -> PowerAnalysisResult:
    """Compute sample size per group for a two-proportion z-test."""
    if not 0 < p1 < 1 or not 0 < p2 < 1:
        raise ValueError("proportions must be between 0 and 1")
    effect = abs(p2 - p1)
    p_bar = (p1 + p2) / 2
    z_alpha = _norm_ppf(1 - alpha / 2)
    z_beta = _norm_ppf(power)
    n = math.ceil(
        (z_alpha * math.sqrt(2 * p_bar * (1 - p_bar)) + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2)))
        ** 2
        / effect**2,
    )
    rec = (
        f"Two-proportion test (p1={p1:.3f}, p2={p2:.3f}): "
        f"n≈{n} per group for power {power:.0%} at α={alpha}."
    )
    return PowerAnalysisResult(
        test_type="two_proportion",
        effect_size=effect,
        alpha=alpha,
        power=power,
        sample_size_per_group=n,
        total_sample_size=2 * n,
        recommendation=rec,
    )
