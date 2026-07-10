"""Audit logging service."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog, SystemEvent
from app.models.research_run import ResearchRunEvent, ToolCall


class AuditService:
    """Service for audit logging operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        event_type: str,
        project_id: str | None = None,
        run_id: str | None = None,
        actor: str | None = None,
        action: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log an audit event."""
        from uuid import uuid4

        log = AuditLog(
            id=str(uuid4()),
            project_id=project_id,
            run_id=run_id,
            event_type=event_type,
            actor=actor,
            action=action,
            details=details,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def log_run_event(
        self,
        run_id: str,
        event_type: str,
        actor: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> ResearchRunEvent:
        """Log a research run event."""
        from uuid import uuid4

        event = ResearchRunEvent(
            id=str(uuid4()),
            run_id=run_id,
            event_type=event_type,
            actor=actor,
            details=details,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def log_tool_call(
        self,
        run_id: str,
        tool_name: str,
        agent_role: str | None = None,
        input_json: dict[str, Any] | None = None,
        output_json: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> ToolCall:
        """Log a tool call."""
        from uuid import uuid4

        tool_call = ToolCall(
            id=str(uuid4()),
            run_id=run_id,
            agent_role=agent_role,
            tool_name=tool_name,
            input_json=input_json,
            output_json=output_json,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
        )
        self.db.add(tool_call)
        await self.db.flush()
        return tool_call

    async def log_system_event(
        self,
        event_type: str,
        details: dict[str, Any] | None = None,
    ) -> SystemEvent:
        """Log a system-level event."""
        from uuid import uuid4

        event = SystemEvent(
            id=str(uuid4()),
            event_type=event_type,
            details=details,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def log_idea_scored(
        self,
        project_id: str,
        idea_id: str,
        score: float,
        classification: str,
        run_id: str | None = None,
    ) -> AuditLog:
        """Log when an idea is scored."""
        return await self.log_event(
            event_type="idea_scored",
            project_id=project_id,
            run_id=run_id,
            actor="scoring_engine",
            action=f"Idea {idea_id} scored {score:.2f} and classified as {classification}",
            details={
                "idea_id": idea_id,
                "score": score,
                "classification": classification,
            },
        )

    async def log_conflict_detected(
        self,
        project_id: str,
        conflict_id: str,
        conflict_type: str,
        run_id: str | None = None,
    ) -> AuditLog:
        """Log when a conflict is detected."""
        return await self.log_event(
            event_type="conflict_detected",
            project_id=project_id,
            run_id=run_id,
            actor="conflict_engine",
            action=f"Detected {conflict_type} conflict",
            details={
                "conflict_id": conflict_id,
                "conflict_type": conflict_type,
            },
        )

    async def log_question_generated(
        self,
        project_id: str,
        question_id: str,
        run_id: str | None = None,
    ) -> AuditLog:
        """Log when a research question is generated."""
        return await self.log_event(
            event_type="question_generated",
            project_id=project_id,
            run_id=run_id,
            actor="question_engine",
            action="Generated research question",
            details={"question_id": question_id},
        )

    async def log_hypothesis_formed(
        self,
        project_id: str,
        hypothesis_id: str,
        run_id: str | None = None,
    ) -> AuditLog:
        """Log when a hypothesis is formed."""
        return await self.log_event(
            event_type="hypothesis_formed",
            project_id=project_id,
            run_id=run_id,
            actor="hypothesis_engine",
            action="Formed hypothesis",
            details={"hypothesis_id": hypothesis_id},
        )

    async def log_skill_created(
        self,
        project_id: str,
        skill_id: str,
        skill_name: str,
        run_id: str | None = None,
    ) -> AuditLog:
        """Log when a skill is created."""
        return await self.log_event(
            event_type="skill_created",
            project_id=project_id,
            run_id=run_id,
            actor="skill_curator",
            action=f"Created skill: {skill_name}",
            details={"skill_id": skill_id, "skill_name": skill_name},
        )

    async def log_approval_requested(
        self,
        project_id: str,
        action_type: str,
        action_description: str,
        run_id: str | None = None,
    ) -> AuditLog:
        """Log when an approval is requested."""
        return await self.log_event(
            event_type="approval_requested",
            project_id=project_id,
            run_id=run_id,
            actor="system",
            action=f"Approval requested for: {action_type}",
            details={
                "action_type": action_type,
                "action_description": action_description,
            },
        )

    async def log_approval_decision(
        self,
        project_id: str,
        action_type: str,
        approved: bool,
        reviewer_notes: str | None = None,
        run_id: str | None = None,
    ) -> AuditLog:
        """Log when an approval decision is made."""
        return await self.log_event(
            event_type="approval_decision",
            project_id=project_id,
            run_id=run_id,
            actor="user",
            action=f"Approval {'granted' if approved else 'denied'} for: {action_type}",
            details={
                "action_type": action_type,
                "approved": approved,
                "reviewer_notes": reviewer_notes,
            },
        )

    async def log_idle_cycle_started(
        self,
        project_id: str,
        cycle_id: str,
        idle_mode: str,
    ) -> AuditLog:
        """Log when an idle cycle starts."""
        return await self.log_event(
            event_type="idle_cycle_started",
            project_id=project_id,
            actor="idle_engine",
            action=f"Started idle cycle: {idle_mode}",
            details={"cycle_id": cycle_id, "idle_mode": idle_mode},
        )

    async def log_idle_cycle_completed(
        self,
        project_id: str,
        cycle_id: str,
        ideas_generated: int,
        questions_generated: int,
    ) -> AuditLog:
        """Log when an idle cycle completes."""
        return await self.log_event(
            event_type="idle_cycle_completed",
            project_id=project_id,
            actor="idle_engine",
            action="Completed idle cycle",
            details={
                "cycle_id": cycle_id,
                "ideas_generated": ideas_generated,
                "questions_generated": questions_generated,
            },
        )

    async def get_project_audit_logs(
        self,
        project_id: str,
        event_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs for a project."""
        from sqlalchemy import select

        query = select(AuditLog).where(AuditLog.project_id == project_id)

        if event_type:
            query = query.where(AuditLog.event_type == event_type)

        query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_run_audit_logs(
        self,
        run_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs for a specific run."""
        from sqlalchemy import select

        query = (
            select(AuditLog)
            .where(AuditLog.run_id == run_id)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())
