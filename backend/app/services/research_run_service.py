"""Research run service layer."""

from datetime import UTC, datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.research_run import ResearchRun, ResearchRunEvent, ToolCall
from app.schemas.research_run import ResearchRunCreate, ResearchRunUpdate


class ResearchRunService:
    """Service for research run operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_runs(
        self,
        project_id: str,
        state: str | None = None,
        run_type: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[ResearchRun]:
        """List research runs for a project."""
        query = select(ResearchRun).where(ResearchRun.project_id == project_id)

        if state:
            query = query.where(ResearchRun.state == state)
        if run_type:
            query = query.where(ResearchRun.run_type == run_type)

        offset = (page - 1) * per_page
        query = query.order_by(ResearchRun.created_at.desc()).offset(offset).limit(per_page)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_run(
        self,
        project_id: str,
        data: ResearchRunCreate,
    ) -> ResearchRun:
        """Create a new research run."""
        run = ResearchRun(
            id=str(uuid4()),
            project_id=project_id,
            idea_id=data.idea_id,
            run_type=data.run_type,
            state="created",
            max_minutes=data.max_minutes,
            max_sources=data.max_sources,
            max_cost_usd=data.max_cost_usd,
        )
        self.db.add(run)

        # Create initial event
        event = ResearchRunEvent(
            id=str(uuid4()),
            run_id=run.id,
            event_type="run_created",
            actor="system",
            details={"run_type": data.run_type},
        )
        self.db.add(event)

        await self.db.flush()
        return run

    async def get_run(self, run_id: str) -> ResearchRun | None:
        """Get a research run by ID."""
        result = await self.db.execute(select(ResearchRun).where(ResearchRun.id == run_id))
        return result.scalar_one_or_none()

    async def update_run(self, run_id: str, data: ResearchRunUpdate) -> ResearchRun | None:
        """Update a research run."""
        run = await self.get_run(run_id)
        if not run:
            return None

        old_state = run.state
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(run, field, value)

        # Track state transitions
        if "state" in update_data and update_data["state"] != old_state:
            new_state = update_data["state"]

            # Set timestamps based on state
            if new_state == "running" and not run.started_at:
                run.started_at = datetime.now(UTC)
            elif new_state in ("completed", "failed", "cancelled"):
                run.completed_at = datetime.now(UTC)

            event = ResearchRunEvent(
                id=str(uuid4()),
                run_id=run_id,
                event_type="state_changed",
                actor="system",
                details={
                    "old_state": old_state,
                    "new_state": new_state,
                },
            )
            self.db.add(event)

        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def start_run(self, run_id: str) -> ResearchRun | None:
        """Start a research run."""
        return await self.update_run(run_id, ResearchRunUpdate(state="running"))

    async def pause_run(self, run_id: str) -> ResearchRun | None:
        """Pause a research run."""
        return await self.update_run(run_id, ResearchRunUpdate(state="paused"))

    async def resume_run(self, run_id: str) -> ResearchRun | None:
        """Resume a research run."""
        return await self.update_run(run_id, ResearchRunUpdate(state="running"))

    async def complete_run(self, run_id: str) -> ResearchRun | None:
        """Complete a research run."""
        return await self.update_run(run_id, ResearchRunUpdate(state="completed"))

    async def fail_run(self, run_id: str, error_msg: str | None = None) -> ResearchRun | None:
        """Mark a research run as failed."""
        run = await self.get_run(run_id)
        if run:
            run.state = "failed"
            if error_msg:
                event = ResearchRunEvent(
                    id=str(uuid4()),
                    run_id=run_id,
                    event_type="run_failed",
                    actor="system",
                    details={"error": error_msg},
                )
                self.db.add(event)
            await self.db.flush()
        return run

    async def cancel_run(self, run_id: str) -> ResearchRun | None:
        """Cancel a research run."""
        return await self.update_run(run_id, ResearchRunUpdate(state="cancelled"))

    async def get_run_events(self, run_id: str) -> list[ResearchRunEvent]:
        """Get events for a research run."""
        result = await self.db.execute(
            select(ResearchRunEvent)
            .where(ResearchRunEvent.run_id == run_id)
            .order_by(ResearchRunEvent.created_at),
        )
        return list(result.scalars().all())

    async def add_run_event(
        self,
        run_id: str,
        event_type: str,
        actor: str | None = None,
        details: dict | None = None,
    ) -> ResearchRunEvent:
        """Add an event to a research run."""
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

    async def get_tool_calls(self, run_id: str) -> list[ToolCall]:
        """Get tool calls for a research run."""
        result = await self.db.execute(
            select(ToolCall)
            .where(ToolCall.run_id == run_id)
            .order_by(ToolCall.created_at),
        )
        return list(result.scalars().all())

    async def update_step_history(self, run_id: str, step_history: list[dict]) -> ResearchRun | None:
        """Persist workflow step history for observability."""
        run = await self.get_run(run_id)
        if not run:
            return None
        run.step_history = step_history
        await self.db.flush()
        return run

    async def update_cognitive_metrics(
        self,
        run_id: str,
        *,
        cognitive_entropy: float | None = None,
        cognitive_mode: str | None = None,
    ) -> ResearchRun | None:
        """Update live cognitive metrics on a research run."""
        run = await self.get_run(run_id)
        if not run:
            return None
        if cognitive_entropy is not None:
            run.cognitive_entropy = cognitive_entropy
        if cognitive_mode is not None:
            run.cognitive_mode = cognitive_mode
        await self.db.flush()
        return run

    async def add_tool_call(
        self,
        run_id: str,
        tool_name: str,
        agent_role: str | None = None,
        input_json: dict | None = None,
        output_json: dict | None = None,
        duration_ms: int | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> ToolCall:
        """Add a tool call record."""
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
