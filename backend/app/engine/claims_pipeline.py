"""Claims pipeline — formalize experiment output into structured claims."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.llm.base import Message
from app.llm.router import LLMRouter

from .effect_size_extraction import _interp_to_confidence, extract_effect_sizes

logger = structlog.get_logger()

# Regex to extract "metric_name: numeric_value" patterns from stdout
_NUMERIC_RESULT_RE = re.compile(
    r"(?P<label>[A-Za-z][A-Za-z0-9 _\-/]{1,60}?)\s*[:=]\s*(?P<value>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
)

# Regex to extract percentage changes like "15.2% improvement" or "decreased by 3.1%"
_PERCENTAGE_CHANGE_RE = re.compile(
    r"(?P<direction>increase|decrease|improve|reduce|drop|rise|fall|grow|decline)"
    r"(?:d|s|ing)?\s*(?:by|of|from|to)?\s*(?P<pct>[-+]?\d*\.?\d+)\s*%",
    re.IGNORECASE,
)

# Regex for p-value patterns
_PVALUE_RE = re.compile(
    r"(?:p\s*[=<>])\s*(?P<pvalue>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
    re.IGNORECASE,
)

# Regex for accuracy / metric scores like "accuracy: 0.942" or "f1_score = 0.87"
_METRIC_SCORE_RE = re.compile(
    r"(?P<metric>accuracy|f1[ _-]?score|precision|recall|auc|roc[ _-]?auc|mse|rmse|mae|r2|correlation)"
    r"\s*[:=]?\s*(?P<value>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
    re.IGNORECASE,
)


@dataclass
class Claim:
    """A structured claim extracted from experiment output."""

    statement: str
    claim_type: str  # finding | comparison | improvement | degradation | statistical | error
    confidence: float = 0.5
    evidence: str = ""
    metric: str | None = None
    value: float | None = None
    source_hypothesis_id: str | None = None
    source_hypothesis_statement: str | None = None


@dataclass
class ClaimsExtractionResult:
    """Result from claims extraction."""

    claims: list[Claim] = field(default_factory=list)
    extraction_notes: str = ""
    total_claims: int = 0
    llm_used: bool = False


def _extract_numeric_claims(stdout: str) -> list[Claim]:
    """Extract simple numeric findings from stdout via regex patterns."""
    claims: list[Claim] = []
    seen: set[str] = set()

    # Parse percentage changes
    for match in _PERCENTAGE_CHANGE_RE.finditer(stdout):
        direction = match.group("direction").lower()
        pct = float(match.group("pct"))
        ctx_start = max(0, match.start() - 60)
        ctx_end = min(len(stdout), match.end() + 60)
        context = stdout[ctx_start:ctx_end].strip()
        direction_word = "increased" if direction in ("increase", "improve", "rise", "grow") else "decreased"
        statement = f"Metric {direction_word} by {pct:.1f}%"
        dedup_key = statement.lower()
        if dedup_key not in seen:
            seen.add(dedup_key)
            claims.append(Claim(
                statement=statement,
                claim_type="improvement" if direction in ("increase", "improve", "rise", "grow") else "degradation",
                confidence=min(0.5 + pct / 200, 0.9),
                evidence=context[:200],
                metric="percentage_change",
                value=pct,
            ))

    # Parse metric scores (accuracy, f1, etc.)
    for match in _METRIC_SCORE_RE.finditer(stdout):
        metric = match.group("metric").lower().replace(" ", "_").replace("-", "_")
        value = float(match.group("value"))
        ctx_start = max(0, match.start() - 40)
        ctx_end = min(len(stdout), match.end() + 40)
        context = stdout[ctx_start:ctx_end].strip()
        statement = f"{metric.replace('_', ' ').title()}: {value:.4f}"
        dedup_key = statement.lower()
        if dedup_key not in seen:
            seen.add(dedup_key)
            claims.append(Claim(
                statement=statement,
                claim_type="finding",
                confidence=0.7,
                evidence=context[:200],
                metric=metric,
                value=value,
            ))

    # Parse p-values
    for match in _PVALUE_RE.finditer(stdout):
        pvalue = float(match.group("pvalue"))
        ctx_start = max(0, match.start() - 40)
        ctx_end = min(len(stdout), match.end() + 40)
        context = stdout[ctx_start:ctx_end].strip()
        significant = pvalue < 0.05
        statement = f"p = {pvalue:.4g}" + (" (statistically significant)" if significant else " (not significant)")
        dedup_key = f"pvalue_{pvalue:.4g}"
        if dedup_key not in seen:
            seen.add(dedup_key)
            claims.append(Claim(
                statement=statement,
                claim_type="statistical",
                confidence=0.85 if significant else 0.4,
                evidence=context[:200],
                metric="p_value",
                value=pvalue,
            ))

    # Parse generic label: value patterns
    for match in _NUMERIC_RESULT_RE.finditer(stdout):
        label = match.group("label").strip()
        value = match.group("value")
        # Skip if it's already captured by more specific patterns
        dedup_key = f"{label.lower()}:{value}"
        if dedup_key not in seen:
            seen.add(dedup_key)
            ctx_start = max(0, match.start() - 30)
            ctx_end = min(len(stdout), match.end() + 30)
            context = stdout[ctx_start:ctx_end].strip()
            claims.append(Claim(
                statement=f"{label}: {value}",
                claim_type="finding",
                confidence=0.5,
                evidence=context[:200],
                metric=label,
                value=float(value) if _is_numeric(value) else None,
            ))

    return claims


def _is_numeric(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def _extract_error_claims(stderr: str, error_message: str | None) -> list[Claim]:
    """Extract error/failure claims from stderr."""
    claims: list[Claim] = []
    if stderr:
        lines = [l.strip() for l in stderr.split("\n") if l.strip()][:5]
        for line in lines:
            claims.append(Claim(
                statement=f"Experiment error: {line[:150]}",
                claim_type="error",
                confidence=0.9,
                evidence=line[:300],
                metric="error",
            ))
    if error_message and error_message not in stderr:
        claims.append(Claim(
            statement=f"Execution failed: {error_message[:150]}",
            claim_type="error",
            confidence=0.95,
            evidence=error_message[:300],
            metric="error_message",
        ))
    return claims


async def extract_claims(
    experiment_result: dict[str, Any],
    hypotheses: list[dict[str, Any]] | None = None,
    llm_router: LLMRouter | None = None,
) -> ClaimsExtractionResult:
    """Extract structured claims from experiment results.

    Uses a two-stage approach:
    1. Regex-based extraction for numeric patterns (fast, deterministic)
    2. LLM-based extraction for semantic understanding (when available)
    """
    stdout = experiment_result.get("stdout", "") or ""
    stderr = experiment_result.get("stderr", "") or ""
    error_message = experiment_result.get("error_message")
    success = experiment_result.get("success", False)

    all_claims: list[Claim] = []

    # Stage 1A: Regex-based numeric extraction
    numeric_claims = _extract_numeric_claims(stdout)
    all_claims.extend(numeric_claims)

    # Stage 1B: Effect size extraction (Cohen's d, η², R², r, etc.)
    es_result = extract_effect_sizes(stdout)
    if es_result.effect_sizes:
        for es in es_result.effect_sizes:
            interp = es.interpretation.replace("_", " ")
            statement = f"{es.label} = {es.value:.4f} ({interp} effect)"
            all_claims.append(Claim(
                statement=statement,
                claim_type="statistical",
                confidence=_interp_to_confidence(es.interpretation),
                evidence=es.evidence[:200],
                metric=f"effect_size_{es.effect_type}",
                value=es.value,
            ))

    # Error claims
    error_claims = _extract_error_claims(stderr, error_message)
    all_claims.extend(error_claims)

    # Stage 2: LLM-based semantic extraction (if available)
    llm_used = False
    if llm_router and llm_router.has_provider() and stdout.strip():
        try:
            llm_claims = await _llm_extract_claims(stdout, stderr, success, llm_router)
            all_claims.extend(llm_claims)
            llm_used = True
        except (ValueError, RuntimeError) as e:
            logger.warning("llm_claim_extraction_error", error=str(e))
        except Exception as e:
            logger.warning("llm_claim_extraction_failed", error=str(e))

    # Link claims to hypotheses if provided
    if hypotheses:
        for claim in all_claims:
            if hypotheses:
                # Link to the first hypothesis (or best matching)
                claim.source_hypothesis_id = hypotheses[0].get("id")
                claim.source_hypothesis_statement = hypotheses[0].get("statement", "")[:200]

    # Deduplicate by statement similarity
    deduped = _deduplicate_claims(all_claims)

    # Generate extraction notes
    notes_parts = []
    if numeric_claims:
        notes_parts.append(f"Extracted {len(numeric_claims)} numeric findings from experiment output.")
    if error_claims:
        notes_parts.append(f"Detected {len(error_claims)} execution errors.")
    if llm_used:
        notes_parts.append("LLM semantic analysis applied.")
    notes = " ".join(notes_parts) if notes_parts else "No structured claims extracted from experiment output."

    return ClaimsExtractionResult(
        claims=deduped,
        extraction_notes=notes,
        total_claims=len(deduped),
        llm_used=llm_used,
    )


def _deduplicate_claims(claims: list[Claim]) -> list[Claim]:
    """Remove duplicate claims based on statement similarity."""
    seen: set[str] = set()
    result: list[Claim] = []
    for claim in claims:
        key = claim.statement.lower().strip()
        # Fuzzy dedup: keep if share of matching words < 80%
        is_dup = False
        for existing_key in seen:
            words_new = set(key.split())
            words_existing = set(existing_key.split())
            if len(words_new) > 0 and len(words_new & words_existing) / len(words_new) > 0.8:
                is_dup = True
                break
        if not is_dup:
            seen.add(key)
            result.append(claim)
    return result


async def _llm_extract_claims(
    stdout: str,
    stderr: str,
    success: bool,
    llm_router: LLMRouter,
) -> list[Claim]:
    """Use LLM to extract semantic claims from experiment output."""
    system = """You are a scientific claims extractor. Given experiment output, identify key claims.

For each claim, output a JSON object with:
- statement: A clear, precise statement of the finding (string)
- claim_type: "finding" | "comparison" | "improvement" | "degradation" | "statistical" (string)
- confidence: Your confidence in this claim 0-1 (float)
- evidence: The exact text that supports this claim (string)
- metric: The metric being measured, if applicable (string or null)
- value: The numeric value, if applicable (float or null)

Output a JSON object with key "claims" containing the array of claims.
Focus on specific, quantifiable findings. Limit to 8 claims."""

    stdout_preview = stdout[:3000]
    stderr_preview = stderr[:1000] if stderr else "none"

    user = (
        f"Experiment completed with status: {'success' if success else 'failure'}\n\n"
        f"stdout output:\n```\n{stdout_preview}\n```\n\n"
        f"stderr output:\n```\n{stderr_preview}\n```\n\n"
        "Extract structured claims from this experiment output as JSON."
    )

    messages = [Message(role="system", content=system), Message(role="user", content=user)]
    result = await llm_router.complete_structured(messages, schema={})
    raw_claims = result.data.get("claims", [])

    claims: list[Claim] = []
    for rc in raw_claims:
        claims.append(Claim(
            statement=str(rc.get("statement", "")),
            claim_type=str(rc.get("claim_type", "finding")),
            confidence=float(rc.get("confidence", 0.5)),
            evidence=str(rc.get("evidence", "")),
            metric=str(rc.get("metric")) if rc.get("metric") else None,
            value=float(rc.get("value")) if rc.get("value") is not None else None,
        ))

    return claims


def format_claims_for_manuscript(claims: list[Claim]) -> list[str]:
    """Format claims as human-readable findings for manuscript inclusion."""
    formatted: list[str] = []
    for claim in claims:
        if claim.claim_type == "error":
            continue  # Skip error claims in manuscript findings
        entry = claim.statement
        # Append metric detail to the natural-language statement rather than replace it
        if claim.value is not None and claim.metric:
            metric_label = claim.metric.replace("_", " ").replace("-", " ").title()
            entry = f"{claim.statement.rstrip('.')} ({metric_label}: {claim.value:.4f})"
        if claim.confidence >= 0.7:
            entry += f" (confidence: {claim.confidence:.0%})"
        if claim.source_hypothesis_statement:
            entry += f" — supports hypothesis: {claim.source_hypothesis_statement[:80]}"
        formatted.append(entry)
    return formatted


def format_claims_as_validation_results(claims: list[Claim]) -> list[dict[str, Any]]:
    """Format claims as validation result dicts for manuscript context."""
    results: list[dict[str, Any]] = []
    for claim in claims:
        if claim.claim_type == "error":
            continue
        results.append({
            "metric": claim.metric or claim.claim_type,
            "result": claim.statement,
            "p_value": "N/A",
            "confidence": claim.confidence,
            "evidence": claim.evidence[:200],
            "source_hypothesis": claim.source_hypothesis_statement,
        })
    return results[:15]
