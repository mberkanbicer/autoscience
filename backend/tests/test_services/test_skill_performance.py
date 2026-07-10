"""Tests for the skill performance feedback loop."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.skill import Skill
from app.services.skill_performance_service import (
    MIN_SUCCESS_RATE,
    MIN_USAGE_FOR_EVAL,
    MIN_NEGATIVE_IMPACT,
    SkillPerformanceService,
    SkillPerformanceReport,
    PerformanceEvaluationResult,
)


async def _create_skill(
    db_session,
    times_used: int = 10,
    successful_uses: int = 8,
    avg_improvement: float | None = 0.2,
    status: str = "active",
    name: str = "Test Skill",
) -> Skill:
    """Create a persisted Skill record with the given stats."""
    skill = Skill(
        id=str(uuid4()),
        project_id=None,
        name=name,
        skill_type="functional",
        purpose="Test purpose",
        trigger_conditions=[],
        inputs=[],
        procedure=[],
        outputs=[],
        status=status,
        version="1.0",
        times_used=times_used,
        successful_uses=successful_uses,
        average_score_improvement=avg_improvement,
        failure_cases=[],
        domains_where_it_works=[],
        domains_where_it_fails=[],
    )
    db_session.add(skill)
    await db_session.flush()
    return skill


class TestEvaluateSkill:
    """Tests for _evaluate_skill on individual skills via DB records."""

    @pytest.mark.asyncio
    async def test_keeps_high_performing_skill(self, db_session):
        """A skill with high success rate and positive impact should be kept."""
        skill = await _create_skill(
            db_session,
            times_used=20,
            successful_uses=18,
            avg_improvement=0.15,
        )
        service = SkillPerformanceService(db_session)
        report = await service.evaluate_skill(skill.id)

        assert report is not None
        assert report.recommendation == "keep"
        assert report.success_rate == pytest.approx(0.9)
        assert report.reasons == []

    @pytest.mark.asyncio
    async def test_deprecates_low_success_rate(self, db_session):
        """A skill with low success rate should be deprecated."""
        skill = await _create_skill(
            db_session,
            times_used=10,
            successful_uses=2,
            avg_improvement=0.1,
        )
        service = SkillPerformanceService(db_session)
        report = await service.evaluate_skill(skill.id)

        assert report is not None
        assert report.recommendation == "deprecate"
        assert report.success_rate == pytest.approx(0.2)
        assert any("Low success rate" in r for r in report.reasons)

    @pytest.mark.asyncio
    async def test_deprecates_negative_impact(self, db_session):
        """A skill with negative score impact should be deprecated."""
        skill = await _create_skill(
            db_session,
            times_used=10,
            successful_uses=6,
            avg_improvement=-0.2,
        )
        service = SkillPerformanceService(db_session)
        report = await service.evaluate_skill(skill.id)

        assert report is not None
        assert report.recommendation == "deprecate"
        assert any("Negative score impact" in r for r in report.reasons)

    @pytest.mark.asyncio
    async def test_keeps_skill_with_low_usage(self, db_session):
        """A skill with low usage (< MIN_USAGE_FOR_EVAL) should be kept regardless."""
        skill = await _create_skill(
            db_session,
            times_used=2,
            successful_uses=0,
            avg_improvement=None,
        )
        service = SkillPerformanceService(db_session)
        report = await service.evaluate_skill(skill.id)

        assert report is not None
        assert report.recommendation == "keep"

    @pytest.mark.asyncio
    async def test_handles_zero_usage(self, db_session):
        """A skill with zero times_used should handle gracefully."""
        skill = await _create_skill(
            db_session,
            times_used=0,
            successful_uses=0,
            avg_improvement=None,
        )
        service = SkillPerformanceService(db_session)
        report = await service.evaluate_skill(skill.id)

        assert report is not None
        assert report.recommendation == "keep"
        assert report.success_rate == 0.0

    @pytest.mark.asyncio
    async def test_deprecates_both_reasons(self, db_session):
        """A skill with both low success rate AND negative impact."""
        skill = await _create_skill(
            db_session,
            times_used=10,
            successful_uses=2,
            avg_improvement=-0.3,
        )
        service = SkillPerformanceService(db_session)
        report = await service.evaluate_skill(skill.id)

        assert report is not None
        assert report.recommendation == "deprecate"
        assert len(report.reasons) >= 2


class TestEvaluateAllSkills:
    """Tests for evaluate_all_skills with DB-persisted records."""

    @pytest.mark.asyncio
    async def test_high_skill_not_affected(self, db_session):
        """A high-performing skill should remain active after bulk evaluation."""
        skill = await _create_skill(
            db_session,
            times_used=20,
            successful_uses=18,
            avg_improvement=0.15,
        )
        service = SkillPerformanceService(db_session)
        result = await service.evaluate_all_skills(dry_run=False)

        assert result.evaluated_count >= 1
        assert not any(r.skill_id == skill.id for r in result.deprecated)
        assert not any(r.skill_id == skill.id for r in result.retired)

    @pytest.mark.asyncio
    async def test_deprecates_underperforming_skill(self, db_session):
        """A low-success-rate skill should be deprecated by bulk evaluation."""
        skill = await _create_skill(
            db_session,
            times_used=10,
            successful_uses=2,
            avg_improvement=0.1,
            name="Bad Skill",
        )
        service = SkillPerformanceService(db_session)
        result = await service.evaluate_all_skills(dry_run=False)

        assert any(r.skill_id == skill.id for r in result.deprecated), \
            f"Expected {skill.name} to be in deprecated: {[r.skill_name for r in result.deprecated]}"

    @pytest.mark.asyncio
    async def test_dry_run_does_not_modify(self, db_session):
        """dry_run=True should report but NOT change status."""
        skill = await _create_skill(
            db_session,
            times_used=10,
            successful_uses=2,
            avg_improvement=0.1,
            status="active",
        )
        service = SkillPerformanceService(db_session)
        result = await service.evaluate_all_skills(dry_run=True)

        assert any(r.skill_id == skill.id for r in result.deprecated)

        # Status should still be 'active' (not changed)
        from sqlalchemy import select
        db_result = await db_session.execute(select(Skill).where(Skill.id == skill.id))
        reloaded = db_result.scalar_one()
        assert reloaded.status == "active", "dry_run should not modify status"

    @pytest.mark.asyncio
    async def test_ineligible_skill_not_evaluated(self, db_session):
        """A skill with low usage should NOT be evaluated."""
        skill = await _create_skill(
            db_session,
            times_used=1,
            successful_uses=0,
            avg_improvement=None,
            status="candidate",
        )
        service = SkillPerformanceService(db_session)
        result = await service.evaluate_all_skills(dry_run=False)

        assert not any(r.skill_id == skill.id for r in result.deprecated)
        assert not any(r.skill_id == skill.id for r in result.retired)


class TestPerformanceReport:
    """Tests for the SkillPerformanceReport dataclass."""

    def test_report_fields(self):
        report = SkillPerformanceReport(
            skill_id="s1",
            skill_name="Test",
            skill_type="functional",
            current_status="active",
            times_used=10,
            successful_uses=8,
            success_rate=0.8,
            average_score_improvement=0.1,
            recommendation="keep",
            reasons=[],
        )
        assert report.skill_name == "Test"
        assert report.success_rate == 0.8
        assert report.recommendation == "keep"


class TestPerformanceStats:
    """Tests for get_performance_stats."""

    @pytest.mark.asyncio
    async def test_empty_stats(self, db_session):
        """Stats with no skills should return zeros."""
        service = SkillPerformanceService(db_session)
        stats = await service.get_performance_stats()
        assert stats["total_skills_evaluated"] == 0
        assert stats["total_usage"] == 0
        assert stats["at_risk_count"] == 0

    @pytest.mark.asyncio
    async def test_stats_with_skills(self, db_session):
        """Stats should reflect DB state."""
        await _create_skill(
            db_session,
            times_used=10,
            successful_uses=8,
            avg_improvement=0.2,
        )
        await _create_skill(
            db_session,
            times_used=5,
            successful_uses=1,
            avg_improvement=-0.1,
        )
        service = SkillPerformanceService(db_session)
        stats = await service.get_performance_stats()

        assert stats["total_skills_evaluated"] >= 2
        assert stats["total_usage"] >= 15
        assert stats["avg_success_rate"] > 0
