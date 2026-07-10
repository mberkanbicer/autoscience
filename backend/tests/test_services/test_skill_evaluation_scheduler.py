"""Tests for the automatic skill evaluation scheduler."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

import app.services.skill_evaluation_scheduler as mod


@pytest.fixture(autouse=True)
def reset_scheduler_globals():
    """Reset scheduler global state before each test."""
    mod._scheduler_task = None
    mod._last_run_at = None
    mod._last_run_result = None
    mod._run_count = 0
    yield


def _make_db_factory():
    """Create a mock db_factory that returns a usable async session.

    Uses a regular Mock for the factory so db_factory() returns the mock_db
    directly (not a coroutine), matching how async_session_factory works.
    """
    mock_db = AsyncMock()
    # Support async with: mock_db.__aenter__ returns mock_db
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)
    mock_db_factory = Mock(return_value=mock_db)  # regular Mock, not AsyncMock
    return mock_db_factory, mock_db


def _make_eval_result(
    evaluated: int = 0,
    deprecated: int = 0,
    retired: int = 0,
    errors: list | None = None,
):
    """Create a mock evaluation result."""
    result = AsyncMock()
    result.evaluated_count = evaluated
    result.deprecated = [AsyncMock(skill_name=f"skill_{i}") for i in range(deprecated)]
    result.retired = [AsyncMock(skill_name=f"retired_{i}") for i in range(retired)]
    result.errors = errors or []
    result.summary = (
        f"{' '.join([f'Deprecated {deprecated}' if deprecated else '', f'Retired {retired}' if retired else ''])}"
        or "All skills performing adequately."
    )
    return result


class TestSchedulerStartStop:
    """Tests for starting and stopping the scheduler."""

    @pytest.mark.asyncio
    async def test_start_stop_scheduler(self):
        """Verify scheduler starts and stops cleanly."""
        with patch(
            "app.services.skill_performance_service.SkillPerformanceService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.evaluate_all_skills = AsyncMock(
                return_value=_make_eval_result()
            )

            mock_db_factory, _ = _make_db_factory()
            task = await mod.start_evaluation_scheduler(
                db_factory=mock_db_factory,
                interval_hours=24,
                dry_run=True,
            )
            # Give the startup evaluation a moment to complete
            await asyncio.sleep(0.05)

            assert task is not None
            assert not task.done()

            await mod.stop_evaluation_scheduler()
            assert mod._scheduler_task is None or mod._scheduler_task.done()

    @pytest.mark.asyncio
    async def test_start_twice_does_not_duplicate(self):
        """Verify starting twice returns same task."""
        with patch(
            "app.services.skill_performance_service.SkillPerformanceService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.evaluate_all_skills = AsyncMock(
                return_value=_make_eval_result()
            )

            mock_db_factory, _ = _make_db_factory()
            task1 = await mod.start_evaluation_scheduler(
                db_factory=mock_db_factory,
                interval_hours=24,
                dry_run=True,
            )
            await asyncio.sleep(0.02)

            task2 = await mod.start_evaluation_scheduler(
                db_factory=mock_db_factory,
                interval_hours=24,
                dry_run=True,
            )
            # Second call should return the same task (not None)
            assert task1 is task2

            await mod.stop_evaluation_scheduler()

    @pytest.mark.asyncio
    async def test_stop_without_start(self):
        """Verify stopping when not running does not error."""
        await mod.stop_evaluation_scheduler()

    @pytest.mark.asyncio
    async def test_scheduler_status_default(self):
        """Verify default status when not running."""
        status = mod.get_scheduler_status()
        assert status["running"] is False
        assert status["run_count"] == 0
        assert status["last_run_at"] is None
        assert status["last_run_result"] is None

    @pytest.mark.asyncio
    async def test_scheduler_status_while_running(self):
        """Verify status reflects running state."""
        with patch(
            "app.services.skill_performance_service.SkillPerformanceService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.evaluate_all_skills = AsyncMock(
                return_value=_make_eval_result()
            )

            mock_db_factory, _ = _make_db_factory()
            await mod.start_evaluation_scheduler(
                db_factory=mock_db_factory,
                interval_hours=24,
                dry_run=True,
            )
            await asyncio.sleep(0.02)

            status = mod.get_scheduler_status()
            assert status["running"] is True
            assert status["run_count"] >= 1

            await mod.stop_evaluation_scheduler()


class TestRunEvaluation:
    """Tests for the _run_evaluation function using direct calls (no background loop)."""

    @pytest.mark.asyncio
    async def test_run_evaluation_updates_globals(self):
        """Verify _run_evaluation updates last_run_at and result."""
        with patch(
            "app.services.skill_performance_service.SkillPerformanceService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.evaluate_all_skills = AsyncMock(
                return_value=_make_eval_result(evaluated=5)
            )

            mock_db_factory, _ = _make_db_factory()
            await mod._run_evaluation(mock_db_factory, dry_run=True)

            assert mod._last_run_at is not None
            assert mod._last_run_result is not None
            assert mod._last_run_result["evaluated_count"] == 5
            assert mod._last_run_result["dry_run"] is True
            assert mod._run_count == 1

    @pytest.mark.asyncio
    async def test_run_evaluation_with_deprecations(self):
        """Verify _run_evaluation records deprecated count."""
        with patch(
            "app.services.skill_performance_service.SkillPerformanceService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.evaluate_all_skills = AsyncMock(
                return_value=_make_eval_result(evaluated=10, deprecated=2, retired=1)
            )

            mock_db_factory, _ = _make_db_factory()
            await mod._run_evaluation(mock_db_factory, dry_run=False)

            assert mod._last_run_result["deprecated_count"] == 2
            assert mod._last_run_result["retired_count"] == 1
            assert mod._run_count == 1

    @pytest.mark.asyncio
    async def test_run_evaluation_with_errors(self):
        """Verify _run_evaluation captures errors."""
        with patch(
            "app.services.skill_performance_service.SkillPerformanceService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.evaluate_all_skills = AsyncMock(
                return_value=_make_eval_result(
                    evaluated=3,
                    errors=["Skill xyz: timeout", "Skill abc: invalid"],
                )
            )

            mock_db_factory, _ = _make_db_factory()
            await mod._run_evaluation(mock_db_factory, dry_run=True)

            assert mod._last_run_result["error_count"] == 2
            assert len(mod._last_run_result["errors"]) == 2

    @pytest.mark.asyncio
    async def test_run_evaluation_records_error_on_failure(self):
        """Verify _run_evaluation captures service exceptions and updates globals."""
        with patch(
            "app.services.skill_performance_service.SkillPerformanceService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.evaluate_all_skills = AsyncMock(
                side_effect=RuntimeError("DB connection lost")
            )

            mock_db_factory, _ = _make_db_factory()
            await mod._run_evaluation(mock_db_factory, dry_run=True)

            # On failure, globals should still be updated
            assert mod._last_run_result is not None
            assert mod._last_run_result["error_count"] >= 1
            assert mod._run_count == 1

    @pytest.mark.asyncio
    async def test_run_evaluation_records_audit_log(self):
        """Verify audit logging occurs on evaluation."""
        with patch(
            "app.services.skill_performance_service.SkillPerformanceService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.evaluate_all_skills = AsyncMock(
                return_value=_make_eval_result(evaluated=5)
            )

            mock_db_factory, mock_db = _make_db_factory()
            await mod._run_evaluation(mock_db_factory, dry_run=True)

            # Verify commit was called (implies audit log was recorded)
            mock_db.commit.assert_called_once()


class TestRunCountTracking:
    """Tests for run count tracking."""

    @pytest.mark.asyncio
    async def test_run_count_increments(self):
        """Verify run count increments on each evaluation."""
        with patch(
            "app.services.skill_performance_service.SkillPerformanceService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.evaluate_all_skills = AsyncMock(
                return_value=_make_eval_result(evaluated=0)
            )

            mock_db_factory, _ = _make_db_factory()

            assert mod._run_count == 0

            await mod._run_evaluation(mock_db_factory, dry_run=True)
            assert mod._run_count == 1

            await mod._run_evaluation(mock_db_factory, dry_run=True)
            assert mod._run_count == 2

            await mod._run_evaluation(mock_db_factory, dry_run=True)
            assert mod._run_count == 3

    @pytest.mark.asyncio
    async def test_error_does_not_block_status_update(self):
        """Verify that even on error, the status endpoint shows the attempt."""
        with patch(
            "app.services.skill_performance_service.SkillPerformanceService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.evaluate_all_skills = AsyncMock(
                side_effect=RuntimeError("Timeout")
            )

            mock_db_factory, _ = _make_db_factory()
            await mod._run_evaluation(mock_db_factory, dry_run=True)

            status = mod.get_scheduler_status()
            assert status["run_count"] == 1
            assert status["last_run_result"] is not None
            assert status["last_run_result"]["error_count"] >= 1
