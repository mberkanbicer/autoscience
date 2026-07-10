"""Skill performance feedback loop — evaluates skills against thresholds and
auto-deprecates/retires low-performing ones.

Thresholds:
  - success_rate < MIN_SUCCESS_RATE (30%) AND times_used >= MIN_USAGE_FOR_EVAL (5) → deprecate
  - average_score_improvement < 0 (negative impact) AND times_used >= MIN_USAGE_FOR_EVAL → deprecate
  - Deprecated for > DEPRECATED_GRACE_DAYS (30) with no improvement → retire
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill, SkillEvaluation

logger = structlog.get_logger()

# Thresholds
MIN_SUCCESS_RATE = 0.30       # 30% — below this is underperforming
MIN_USAGE_FOR_EVAL = 5        # Minimum times used before we can evaluate
MIN_NEGATIVE_IMPACT = -0.05   # Average score improvement below this is negative impact
DEPRECATED_GRACE_DAYS = 30    # Days after deprecation before auto-retirement


@dataclass
class SkillPerformanceReport:
    """Report of a single skill's performance evaluation."""

    skill_id: str
    skill_name: str
    skill_type: str
    current_status: str
    times_used: int
    successful_uses: int
    success_rate: float
    average_score_improvement: float | None
    recommendation: str  # keep | deprecate | retire
    reasons: list[str]


@dataclass
class PerformanceEvaluationResult:
    """Result of a full performance evaluation run."""

    evaluated_count: int
    deprecated: list[SkillPerformanceReport]
    retired: list[SkillPerformanceReport]
    kept: list[SkillPerformanceReport]
    errors: list[str]
    summary: str


class SkillPerformanceService:
    """Evaluates skill performance and auto-manages the skill lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_all_skills(
        self,
        project_id: str | None = None,
        dry_run: bool = False,
    ) -> PerformanceEvaluationResult:
        """Evaluate all skills against performance thresholds.

        Args:
            project_id: Optional project scope. If None, evaluates all skills.
            dry_run: When True, only reports what would happen without acting.

        Returns:
            PerformanceEvaluationResult with lists of affected skills.

        """
        # Fetch all non-retired skills with enough usage
        query = select(Skill).where(Skill.status.in_(["candidate", "tested", "active", "revised", "deprecated"]))
        if project_id:
            query = query.where(Skill.project_id == project_id)

        result = await self.db.execute(query)
        all_skills = list(result.scalars().all())
        eligible = [s for s in all_skills if s.times_used >= MIN_USAGE_FOR_EVAL]

        deprecated: list[SkillPerformanceReport] = []
        retired: list[SkillPerformanceReport] = []
        kept: list[SkillPerformanceReport] = []
        errors: list[str] = []

        for skill in eligible:
            try:
                report = await self._evaluate_skill(skill)
                if report.recommendation == "deprecate":
                    if not dry_run:
                        skill.status = "deprecated"
                        await self._record_evaluation(skill.id, 2.0, f"Auto-deprecated: {'; '.join(report.reasons)}")
                    deprecated.append(report)
                elif report.recommendation == "retire":
                    if not dry_run:
                        skill.status = "retired"
                        await self._record_evaluation(skill.id, 1.0, f"Auto-retired: {'; '.join(report.reasons)}")
                    retired.append(report)
                else:
                    kept.append(report)
            except (ValueError, SQLAlchemyError) as exc:
                errors.append(f"Skill {skill.id} ({skill.name}): {exc}")
                logger.warning("skill_evaluation_data_error", skill_id=skill.id, error=str(exc))
            except Exception as exc:
                errors.append(f"Skill {skill.id} ({skill.name}): {exc}")
                logger.warning("skill_evaluation_failed", skill_id=skill.id, error=str(exc))

        if not dry_run and (deprecated or retired):
            await self.db.flush()
            logger.info(
                "skill_performance_evaluation_complete",
                evaluated=len(eligible),
                deprecated=len(deprecated),
                retired=len(retired),
            )

        # Build summary
        parts = []
        if deprecated:
            parts.append(f"Deprecated {len(deprecated)} underperforming skill(s)")
        if retired:
            parts.append(f"Retired {len(retired)} long-deprecated skill(s)")
        if not parts and not errors:
            parts.append(f"All {len(eligible)} evaluated skills performing adequately")
        if dry_run:
            parts.insert(0, "[DRY RUN]")
        if errors:
            parts.append(f"{len(errors)} evaluation error(s)")
        summary = ". ".join(parts) + "."

        return PerformanceEvaluationResult(
            evaluated_count=len(eligible),
            deprecated=deprecated,
            retired=retired,
            kept=kept,
            errors=errors,
            summary=summary,
        )

    async def evaluate_skill(self, skill_id: str) -> SkillPerformanceReport | None:
        """Evaluate a single skill by ID."""
        skill = await self.db.get(Skill, skill_id)
        if not skill:
            return None
        return await self._evaluate_skill(skill)

    async def _evaluate_skill(self, skill: Skill) -> SkillPerformanceReport:
        """Evaluate a single skill and determine recommendation."""
        success_rate = skill.successful_uses / max(skill.times_used, 1)
        avg_improvement = skill.average_score_improvement
        reasons: list[str] = []
        recommendation = "keep"

        # Check 1: Low success rate with sufficient usage
        if success_rate < MIN_SUCCESS_RATE and skill.times_used >= MIN_USAGE_FOR_EVAL:
            reasons.append(
                f"Low success rate ({success_rate:.0%} < {MIN_SUCCESS_RATE:.0%}) "
                f"after {skill.times_used} uses",
            )

        # Check 2: Negative score impact
        if avg_improvement is not None and avg_improvement < MIN_NEGATIVE_IMPACT:
            reasons.append(
                f"Negative score impact ({avg_improvement:+.3f} avg improvement)",
            )

        # Check 3: Grace period expired for deprecated skills
        if skill.status == "deprecated":
            is_overdue = await self._is_past_grace_period(skill.id)
            if is_overdue:
                reasons.append(f"Deprecated grace period ({DEPRECATED_GRACE_DAYS} days) expired")
            if not reasons:
                # Not eligible for retirement yet but below thresholds
                if success_rate < MIN_SUCCESS_RATE or (avg_improvement is not None and avg_improvement < MIN_NEGATIVE_IMPACT):
                    reasons.append("Still underperforming after deprecation")

        # Determine recommendation
        if skill.status == "deprecated" and any("grace period" in r for r in reasons):
            recommendation = "retire"
        elif reasons:
            recommendation = "deprecate"
        else:
            recommendation = "keep"

        # Record findings
        avg_imp_str = f"{avg_improvement:+.3f}" if avg_improvement is not None else "N/A"
        await self._record_evaluation(
            skill.id,
            success_rate * 10 if success_rate > 0 else 1.0,
            f"Auto-eval: SR={success_rate:.0%}, "
            f"avg_imp={avg_imp_str}, "
            f"uses={skill.times_used}, action={recommendation}",
        )

        return SkillPerformanceReport(
            skill_id=skill.id,
            skill_name=skill.name,
            skill_type=skill.skill_type,
            current_status=skill.status,
            times_used=skill.times_used,
            successful_uses=skill.successful_uses,
            success_rate=round(success_rate, 3),
            average_score_improvement=round(avg_improvement, 4) if avg_improvement is not None else None,
            recommendation=recommendation,
            reasons=reasons,
        )

    async def _is_past_grace_period(self, skill_id: str) -> bool:
        """Check if a deprecated skill is past its grace period.

        Uses the FIRST 'Auto-deprecated' evaluation record as the deprecation
        timestamp, so the grace period is not reset by subsequent evaluations.
        """
        # Look for the FIRST evaluation with 'Auto-deprecated' in feedback
        result = await self.db.execute(
            select(SkillEvaluation)
            .where(SkillEvaluation.skill_id == skill_id)
            .where(SkillEvaluation.evaluator == "system")
            .where(SkillEvaluation.feedback.like("Auto-deprecated:%"))
            .order_by(SkillEvaluation.created_at.asc())
            .limit(1),
        )
        eval_record = result.scalar_one_or_none()
        if not eval_record:
            return False

        cutoff = datetime.now(UTC) - timedelta(days=DEPRECATED_GRACE_DAYS)
        # SkillEvaluation.created_at is a datetime (non-tz-aware from BaseModel)
        eval_time = eval_record.created_at
        if eval_time.tzinfo is None:
            from datetime import timezone as tz
            eval_time = eval_time.replace(tzinfo=UTC)
        return eval_time < cutoff

    async def _record_evaluation(
        self, skill_id: str, rating: float, feedback: str,
    ) -> None:
        """Record an evaluation in the database."""
        evaluation = SkillEvaluation(
            id=str(uuid4()),
            skill_id=skill_id,
            evaluator="system",
            rating=rating,
            feedback=feedback,
        )
        self.db.add(evaluation)

    async def get_performance_history(
        self,
        project_id: str | None = None,
        skill_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get time-series performance history from evaluation records.

        Parses evaluation feedback strings to extract success rate, avg
        improvement, and usage count at each evaluation point. Returns
        data ordered by timestamp for chart rendering.

        Args:
            project_id: Optional project scope.
            skill_id: Optional single skill scope.
            limit: Max records to return.

        Returns:
            List of dicts with keys:
              - timestamp: ISO datetime
              - skill_id, skill_name, skill_type
              - success_rate: float 0-1
              - avg_score_improvement: float or None
              - times_used: int
              - rating: float 0-10
              - recommendation: str (keep|deprecate|retire)

        """
        import re

        from app.models.skill import Skill as SkillModel

        query = (
            select(SkillEvaluation)
            .join(SkillModel, SkillEvaluation.skill_id == SkillModel.id)
            .where(SkillEvaluation.evaluator == "system")
        )

        if project_id:
            query = query.where(SkillModel.project_id == project_id)
        if skill_id:
            query = query.where(SkillEvaluation.skill_id == skill_id)

        query = query.order_by(SkillEvaluation.created_at.asc()).limit(limit)
        result = await self.db.execute(query)
        records = result.scalars().all()

        history: list[dict[str, Any]] = []
        sr_re = re.compile(r"SR=([\d.]+)%")
        imp_re = re.compile(r"avg_imp=([+-]?[\d.]+|N/A)")
        uses_re = re.compile(r"uses=(\d+)")
        action_re = re.compile(r"action=(\w+)")

        for record in records:
            feedback = record.feedback or ""
            sr_match = sr_re.search(feedback)
            imp_match = imp_re.search(feedback)
            uses_match = uses_re.search(feedback)
            action_match = action_re.search(feedback)

            history.append({
                "timestamp": record.created_at.isoformat() if record.created_at else None,
                "skill_id": record.skill_id,
                "rating": record.rating,
                "success_rate": float(sr_match.group(1)) / 100.0 if sr_match else None,
                "avg_score_improvement": float(imp_match.group(1)) if imp_match and imp_match.group(1) != "N/A" else None,
                "times_used": int(uses_match.group(1)) if uses_match else None,
                "recommendation": action_match.group(1) if action_match else None,
            })

        return history

    async def get_performance_stats(
        self, project_id: str | None = None,
    ) -> dict[str, Any]:
        """Get aggregate performance statistics for skills."""
        from sqlalchemy import func

        query = select(
            func.count(Skill.id).label("total"),
            func.sum(Skill.times_used).label("total_usage"),
            func.avg(
                Skill.successful_uses * 1.0 / func.nullif(Skill.times_used, 0),
            ).label("avg_success_rate"),
        )
        if project_id:
            query = query.where(Skill.project_id == project_id)

        result = await self.db.execute(query)
        row = result.one()

        # Count skills at risk
        risk_query = select(Skill).where(
            Skill.times_used >= MIN_USAGE_FOR_EVAL,
            Skill.status.in_(["candidate", "tested", "active", "revised"]),
        )
        if project_id:
            risk_query = risk_query.where(Skill.project_id == project_id)

        risk_result = await self.db.execute(risk_query)
        skills = list(risk_result.scalars().all())

        at_risk = 0
        for skill in skills:
            sr = skill.successful_uses / max(skill.times_used, 1)
            if sr < MIN_SUCCESS_RATE or (
                skill.average_score_improvement is not None
                and skill.average_score_improvement < MIN_NEGATIVE_IMPACT
            ):
                at_risk += 1

        return {
            "total_skills_evaluated": int(row.total or 0),
            "total_usage": int(row.total_usage or 0),
            "avg_success_rate": round(float(row.avg_success_rate or 0), 3),
            "at_risk_count": at_risk,
            "min_success_rate_threshold": MIN_SUCCESS_RATE,
            "min_usage_for_evaluation": MIN_USAGE_FOR_EVAL,
            "deprecated_grace_days": DEPRECATED_GRACE_DAYS,
        }



