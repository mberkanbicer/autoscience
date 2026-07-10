"""Effect size extraction from experiment numeric output.

Parses stdout for common statistical effect size patterns:
- Cohen's d (from t-statistics or direct d = ...)
- η² / η²p (from F-statistics)
- R² / adjusted R² (from regression output)
- Correlation coefficients (r, ρ / rho)
- Simple mean differences with SD
- Odds ratios with confidence intervals

All functions accept a stdout string and return a list of EffectSize dataclass
instances, which are then integrated into the claims pipeline and manuscript context.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Cohen's d: "d = 0.45", "Cohen's d: 0.8", "d=1.23", "effect size d = 0.67"
_COHENS_D_RE = re.compile(
    r"(?:Cohen['’]?s\s+)?d\s*(?:statistic)?\s*[:=]?\s*(?P<value>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
    re.IGNORECASE,
)

# t-statistic with df: t(28) = 2.14, t(df) = value
# The parentheses are REQUIRED to extract df (avoids stealing digits from the value)
_T_STAT_RE = re.compile(
    r"t\s*\(\s*(?P<df>\d+)\s*\)\s*[=:≈]\s*(?P<value>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
    re.IGNORECASE,
)

# F-statistic: F(1, 28) = 5.23, F = 12.3
_F_STAT_RE = re.compile(
    r"F\s*\(\s*(?P<df1>\d+)\s*,\s*(?P<df2>\d+)\s*\)\s*[=:≈]\s*(?P<value>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
    re.IGNORECASE,
)

# η² / η²p: "η² = 0.14", "eta-squared: 0.06", "partial η² = 0.32"
_ETA_SQ_RE = re.compile(
    r"(?:(?:partial\s+)?η²|eta[- ]?squared|eta_sq)\s*[:=≈]?\s*(?P<value>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
    re.IGNORECASE,
)

# R² / adjusted R²: "R² = 0.85", "R-squared: 0.72", "adj. R² = 0.68"
_R_SQUARED_RE = re.compile(
    r"(?:(?:R|r)\s*[²2]|R[- ]?squared|r[- ]?squared|R_sq)\s*[:=≈]?\s*(?P<value>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
    re.IGNORECASE,
)

# Correlation: "r = 0.42", "ρ = 0.31", "Spearman's ρ = 0.55", "Pearson r = 0.67"
_CORRELATION_RE = re.compile(
    r"(?:(?:Pearson|Spearman|Kendall)['’]?s?\s+)?[rρ]\s*(?:statistic)?\s*[=:≈]?\s*(?P<value>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
    re.IGNORECASE,
)

# Mean ± SD: "12.3 ± 1.5", "mean = 45.2 (SD = 3.1)"
_MEAN_SD_RE = re.compile(
    r"(?P<mean>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*±\s*(?P<sd>\d*\.?\d+(?:[eE][-+]?\d+)?)",
)

# Odds ratio: "OR = 1.45", "odds ratio: 2.3 (CI: [1.1, 4.2])"
_ODDS_RATIO_RE = re.compile(
    r"(?:OR|odds[- ]?ratio)\s*[=:≈]?\s*(?P<value>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
    re.IGNORECASE,
)

# Generic "effect size:" label pattern
_GENERIC_ES_RE = re.compile(
    r"(?:effect size|effect_size|es)\s*[=:≈]?\s*(?P<value>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class EffectSize:
    """A parsed effect size from experiment output."""

    effect_type: str      # cohens_d | eta_squared | r_squared | correlation | mean_diff | odds_ratio
    value: float
    direction: str = ""   # positive | negative | unknown
    interpretation: str = ""  # small | medium | large | very_large | none
    evidence: str = ""    # The matched text snippet
    label: str = ""       # Human-readable label like "Cohen's d"
    n: int | None = None  # Sample size (if extractable)
    ci_lower: float | None = None
    ci_upper: float | None = None

    def __post_init__(self):
        if not self.direction:
            self.direction = "positive" if self.value >= 0 else "negative"
        if not self.interpretation:
            self.interpretation = self._interpret()
        if not self.label:
            self.label = self._default_label()

    def _interpret(self) -> str:
        """Interpret effect size magnitude using conventional thresholds."""
        v = abs(self.value)
        if self.effect_type in ("cohens_d", "mean_diff"):
            # Cohen's d: 0.2 small, 0.5 medium, 0.8 large
            if v <= 0.01:
                return "none"
            if v <= 0.2:
                return "small"
            if v < 0.5:
                return "small_to_medium"
            if v < 0.8:
                return "medium"
            if v < 1.2:
                return "large"
            return "very_large"
        if self.effect_type == "eta_squared":
            # η²: 0.01 small, 0.06 medium, 0.14 large
            # 0.01 is the boundary for small, 0.14 is the boundary for large
            if v <= 0.01:
                return "none"
            if v < 0.06:
                return "small"
            if v < 0.14:
                return "medium"
            return "large"
        if self.effect_type == "r_squared":
            # R²: 0.02 small, 0.13 medium, 0.26 large (Cohen's f² guidelines)
            if v <= 0.01:
                return "none"
            if v < 0.13:
                return "small"
            if v < 0.26:
                return "medium"
            return "large"
        if self.effect_type == "correlation":
            # r: 0.1 small, 0.3 medium, 0.5 large
            v_abs = abs(v)
            if v_abs <= 0.05:
                return "none"
            if v_abs < 0.3:
                return "small"
            if v_abs < 0.5:
                return "medium"
            return "large"
        if self.effect_type == "odds_ratio":
            # OR: 1.5 small, 2.5 medium, 4.0+ large (log scale)
            if v <= 1.05:
                return "none"
            if v < 1.5:
                return "small"
            if v <= 2.5:
                return "medium"
            if v < 4.0:
                return "large"
            return "very_large"
        return "unknown"

    def _default_label(self) -> str:
        labels = {
            "cohens_d": "Cohen's d",
            "eta_squared": "η²",
            "r_squared": "R²",
            "correlation": "r",
            "mean_diff": "Mean difference",
            "odds_ratio": "Odds ratio",
        }
        return labels.get(self.effect_type, self.effect_type)


# ---------------------------------------------------------------------------
# Extraction functions
# ---------------------------------------------------------------------------


def _extract_cohens_d(stdout: str) -> list[EffectSize]:
    """Parse direct Cohen's d assignments and compute d from t-statistics."""
    results: list[EffectSize] = []
    seen: set[str] = set()

    # Direct d = value patterns
    for match in _COHENS_D_RE.finditer(stdout):
        value = float(match.group("value"))
        if abs(value) > 10:  # Sanity check: d > 10 is unrealistic
            continue
        dedup_key = f"d:{value:.4f}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        ctx = _context(stdout, match.start(), match.end())
        results.append(EffectSize(
            effect_type="cohens_d",
            value=value,
            evidence=ctx,
        ))

    # Compute d from t-statistics: d = 2*t / sqrt(df)
    for match in _T_STAT_RE.finditer(stdout):
        df = int(match.group("df"))
        t_val = float(match.group("value"))
        if df <= 0 or abs(t_val) > 100:
            continue
        d = 2 * t_val / math.sqrt(df)
        if abs(d) > 10:
            continue
        dedup_key = f"d_from_t:{d:.4f}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        ctx = _context(stdout, match.start(), match.end())
        results.append(EffectSize(
            effect_type="cohens_d",
            value=d,
            evidence=ctx + f" (computed from t({df})={t_val:.4f})",
            n=df + 1,  # Approximate: df = n-2 for two-sample
        ))

    return results


def _extract_eta_squared(stdout: str) -> list[EffectSize]:
    """Parse direct η² assignments and compute η² from F-statistics."""
    results: list[EffectSize] = []
    seen: set[str] = set()

    # Direct η² = value patterns
    for match in _ETA_SQ_RE.finditer(stdout):
        value = float(match.group("value"))
        if not (0 <= value <= 1):
            continue
        dedup_key = f"eta2:{value:.4f}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        ctx = _context(stdout, match.start(), match.end())
        results.append(EffectSize(
            effect_type="eta_squared",
            value=value,
            evidence=ctx,
        ))

    # Compute η² from F-statistics: η² = F*df1 / (F*df1 + df2)
    for match in _F_STAT_RE.finditer(stdout):
        df1 = int(match.group("df1"))
        df2 = int(match.group("df2"))
        f_val = float(match.group("value"))
        if df1 <= 0 or df2 <= 0 or f_val < 0:
            continue
        eta2 = (f_val * df1) / (f_val * df1 + df2)
        if eta2 < 0 or eta2 > 1:
            continue
        dedup_key = f"eta2_from_F:{eta2:.4f}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        ctx = _context(stdout, match.start(), match.end())
        results.append(EffectSize(
            effect_type="eta_squared",
            value=eta2,
            evidence=ctx + f" (computed from F({df1},{df2})={f_val:.4f})",
            n=df1 + df2 + 1,
        ))

    return results


def _extract_r_squared(stdout: str) -> list[EffectSize]:
    """Parse R² values from stdout."""
    results: list[EffectSize] = []
    seen: set[str] = set()

    for match in _R_SQUARED_RE.finditer(stdout):
        value = float(match.group("value"))
        if not (0 <= value <= 1):
            continue
        # Avoid capturing "R²" from other contexts like variable names
        # Skip if value is suspiciously high/low for R² in context (0.0-1.0)
        dedup_key = f"r2:{value:.4f}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        ctx = _context(stdout, match.start(), match.end())
        results.append(EffectSize(
            effect_type="r_squared",
            value=value,
            evidence=ctx,
        ))

    return results


def _extract_correlation(stdout: str) -> list[EffectSize]:
    """Parse correlation coefficients (r, ρ)."""
    results: list[EffectSize] = []
    seen: set[str] = set()

    for match in _CORRELATION_RE.finditer(stdout):
        value = float(match.group("value"))
        if not (-1 <= value <= 1):
            continue
        dedup_key = f"corr:{value:.4f}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        ctx = _context(stdout, match.start(), match.end())
        results.append(EffectSize(
            effect_type="correlation",
            value=value,
            evidence=ctx,
        ))

    return results


def _extract_mean_diff(stdout: str) -> list[EffectSize]:
    """Parse mean ± SD patterns as effect sizes.

    Uses the ratio mean/SD as an approximate Cohen's d (standardized mean diff).
    """
    results: list[EffectSize] = []
    seen: set[str] = set()

    for match in _MEAN_SD_RE.finditer(stdout):
        mean = float(match.group("mean"))
        sd = float(match.group("sd"))
        if sd <= 0 or abs(mean) > 1e6:
            continue
        # Standardized mean difference (approximate Cohen's d from a single group)
        # This is a rough heuristic when comparing against a reference
        d_approx = mean / sd if sd > 0 else 0.0
        dedup_key = f"mean_diff:{mean:.4f}:{sd:.4f}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        ctx = _context(stdout, match.start(), match.end())
        results.append(EffectSize(
            effect_type="mean_diff",
            value=d_approx,
            evidence=ctx,
            label=f"Mean ± SD ({mean:.4f} ± {sd:.4f})",
        ))

    return results


def _extract_odds_ratio(stdout: str) -> list[EffectSize]:
    """Parse odds ratios."""
    results: list[EffectSize] = []
    seen: set[str] = set()

    for match in _ODDS_RATIO_RE.finditer(stdout):
        value = float(match.group("value"))
        if value <= 0 or value > 100:  # Sanity check
            continue
        dedup_key = f"or:{value:.4f}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        ctx = _context(stdout, match.start(), match.end())
        results.append(EffectSize(
            effect_type="odds_ratio",
            value=value,
            evidence=ctx,
        ))

    return results


def _extract_generic_effect_size(stdout: str) -> list[EffectSize]:
    """Catch-all for generic 'effect size = X' patterns not matched above."""
    results: list[EffectSize] = []
    seen: set[str] = set()

    for match in _GENERIC_ES_RE.finditer(stdout):
        value = float(match.group("value"))
        if abs(value) > 100:
            continue
        dedup_key = f"generic_es:{value:.4f}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        ctx = _context(stdout, match.start(), match.end())
        results.append(EffectSize(
            effect_type="cohens_d",  # Default assumption: Cohen's d
            value=value,
            evidence=ctx,
            label="Effect size",
        ))

    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _context(text: str, start: int, end: int, window: int = 50) -> str:
    """Extract surrounding context for a match."""
    ctx_start = max(0, start - window)
    ctx_end = min(len(text), end + window)
    return text[ctx_start:ctx_end].strip()


def _deduplicate(results: list[EffectSize]) -> list[EffectSize]:
    """Remove near-duplicate effect sizes by value similarity."""
    kept: list[EffectSize] = []
    seen_values: dict[str, list[float]] = {}
    for es in results:
        bucket = seen_values.setdefault(es.effect_type, [])
        # Check if any existing value is within 5% of this one
        is_dup = any(abs(es.value - existing) / max(abs(existing), 0.001) < 0.05 for existing in bucket)
        if not is_dup:
            bucket.append(es.value)
            kept.append(es)
    return kept


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass
class EffectSizeExtractionResult:
    """Result from effect size extraction."""

    effect_sizes: list[EffectSize] = field(default_factory=list)
    total_count: int = 0
    notes: str = ""


def extract_effect_sizes(stdout: str) -> EffectSizeExtractionResult:
    """Extract all effect sizes from experiment stdout.

    Runs all extraction strategies and returns a combined, deduplicated result.
    """
    if not stdout or not stdout.strip():
        return EffectSizeExtractionResult()

    all_es: list[EffectSize] = []

    all_es.extend(_extract_cohens_d(stdout))
    all_es.extend(_extract_eta_squared(stdout))
    all_es.extend(_extract_r_squared(stdout))
    all_es.extend(_extract_correlation(stdout))
    all_es.extend(_extract_mean_diff(stdout))
    all_es.extend(_extract_odds_ratio(stdout))
    all_es.extend(_extract_generic_effect_size(stdout))

    # Deduplicate across all extractors
    deduped = _deduplicate(all_es)

    # Sort by effect type for stable output
    deduped.sort(key=lambda e: (e.effect_type, -abs(e.value)))

    notes_parts = []
    type_counts: dict[str, int] = {}
    for es in deduped:
        type_counts[es.effect_type] = type_counts.get(es.effect_type, 0) + 1

    if type_counts:
        for etype, count in sorted(type_counts.items()):
            labels = {
                "cohens_d": "Cohen's d",
                "eta_squared": "η²",
                "r_squared": "R²",
                "correlation": "Correlation",
                "mean_diff": "Mean difference",
                "odds_ratio": "Odds ratio",
            }
            notes_parts.append(f"{count} {labels.get(etype, etype)} estimate(s)")
        notes = "Extracted " + ", ".join(notes_parts) + " from experiment output."
    else:
        notes = "No effect sizes detected in experiment output."

    return EffectSizeExtractionResult(
        effect_sizes=deduped,
        total_count=len(deduped),
        notes=notes,
    )


def format_effect_sizes_for_manuscript(effect_sizes: list[EffectSize]) -> list[str]:
    """Format effect sizes as human-readable findings for manuscript inclusion."""
    formatted: list[str] = []
    for es in effect_sizes[:10]:
        base = f"{es.label} = {es.value:.4f}"
        interp = es.interpretation.replace("_", " ")
        base += f" ({interp} effect)"
        if es.evidence:
            base += f" — {es.evidence[:120]}"
        formatted.append(base)
    return formatted


def format_effect_sizes_as_validation_results(effect_sizes: list[EffectSize]) -> list[dict[str, Any]]:
    """Format effect sizes as validation result dicts for manuscript context."""
    results: list[dict[str, Any]] = []
    for es in effect_sizes[:10]:
        interp = es.interpretation.replace("_", " ").title()
        results.append({
            "metric": f"effect_size_{es.effect_type}",
            "result": f"{es.label} = {es.value:.4f} ({interp})",
            "p_value": "N/A",
            "confidence": _interp_to_confidence(es.interpretation),
            "evidence": es.evidence[:200],
        })
    return results


def _interp_to_confidence(interp: str) -> float:
    """Map interpretation to a confidence score."""
    mapping = {
        "none": 0.1,
        "small": 0.4,
        "small_to_medium": 0.5,
        "medium": 0.6,
        "large": 0.8,
        "very_large": 0.9,
    }
    return mapping.get(interp, 0.5)
