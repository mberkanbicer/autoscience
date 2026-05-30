"""Idea service layer."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.idea import Idea, IdeaVersion, IdeaScore, IdeaClassification, IdeaDecision
from ..schemas.idea import IdeaCreate, IdeaUpdate


class IdeaService:
    """Service for idea operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_ideas(
        self,
        project_id: str,
        status: str | None = None,
        classification: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[Idea]:
        """List ideas for a project with optional filters."""
        query = select(Idea).where(Idea.project_id == project_id)

        if status:
            query = query.where(Idea.status == status)
        if classification:
            query = query.where(Idea.classification == classification)

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_idea(
        self,
        project_id: str,
        data: IdeaCreate,
        origin: str = "user_prompt",
    ) -> Idea:
        """Create a new idea."""
        idea = Idea(
            id=str(uuid4()),
            project_id=project_id,
            origin=origin,
            initial_text=data.text,
            current_text=data.text,
            flexibility=data.flexibility,
            status="active",
        )
        self.db.add(idea)

        # Create initial version
        version = IdeaVersion(
            id=str(uuid4()),
            idea_id=idea.id,
            version_number=1,
            text=data.text,
            change_reason="Initial idea",
        )
        self.db.add(version)

        await self.db.flush()
        return idea

    async def get_idea(self, idea_id: str) -> Idea | None:
        """Get an idea by ID."""
        result = await self.db.execute(select(Idea).where(Idea.id == idea_id))
        return result.scalar_one_or_none()

    async def update_idea(self, idea_id: str, data: IdeaUpdate) -> Idea | None:
        """Update an idea."""
        idea = await self.get_idea(idea_id)
        if not idea:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # If text changed, create a new version
        if "current_text" in update_data and update_data["current_text"] != idea.current_text:
            # Get current version number
            version_result = await self.db.execute(
                select(IdeaVersion)
                .where(IdeaVersion.idea_id == idea_id)
                .order_by(IdeaVersion.version_number.desc())
                .limit(1)
            )
            current_version = version_result.scalar_one_or_none()
            next_version = (current_version.version_number + 1) if current_version else 1

            new_version = IdeaVersion(
                id=str(uuid4()),
                idea_id=idea_id,
                version_number=next_version,
                text=update_data["current_text"],
                change_reason="Updated via API",
            )
            self.db.add(new_version)

        for field, value in update_data.items():
            setattr(idea, field, value)

        await self.db.flush()
        await self.db.refresh(idea)
        return idea

    async def delete_idea(self, idea_id: str) -> bool:
        """Delete an idea and all related records."""
        idea = await self.get_idea(idea_id)
        if not idea:
            return False

        # Delete related records first
        from sqlalchemy import delete as sql_delete
        await self.db.execute(sql_delete(IdeaVersion).where(IdeaVersion.idea_id == idea_id))
        await self.db.execute(sql_delete(IdeaScore).where(IdeaScore.idea_id == idea_id))
        await self.db.execute(sql_delete(IdeaClassification).where(IdeaClassification.idea_id == idea_id))
        await self.db.execute(sql_delete(IdeaDecision).where(IdeaDecision.idea_id == idea_id))

        await self.db.delete(idea)
        await self.db.flush()
        return True

    async def get_idea_versions(self, idea_id: str) -> list[IdeaVersion]:
        """Get version history for an idea."""
        result = await self.db.execute(
            select(IdeaVersion)
            .where(IdeaVersion.idea_id == idea_id)
            .order_by(IdeaVersion.version_number)
        )
        return list(result.scalars().all())

    async def get_idea_scores(self, idea_id: str) -> list[IdeaScore]:
        """Get score history for an idea."""
        result = await self.db.execute(
            select(IdeaScore)
            .where(IdeaScore.idea_id == idea_id)
            .order_by(IdeaScore.created_at)
        )
        return list(result.scalars().all())

    async def get_idea_decisions(self, idea_id: str) -> list[IdeaDecision]:
        """Get decision history for an idea."""
        result = await self.db.execute(
            select(IdeaDecision)
            .where(IdeaDecision.idea_id == idea_id)
            .order_by(IdeaDecision.created_at)
        )
        return list(result.scalars().all())

    async def add_idea_score(
        self,
        idea_id: str,
        scores: dict,
        rationale: str | None = None,
    ) -> IdeaScore:
        """Add a score record to an idea."""
        score = IdeaScore(
            id=str(uuid4()),
            idea_id=idea_id,
            novelty=scores.get("novelty"),
            feasibility=scores.get("feasibility"),
            importance=scores.get("importance"),
            evidence_support=scores.get("evidence_support"),
            validation_clarity=scores.get("validation_clarity"),
            differentiation=scores.get("differentiation"),
            data_availability=scores.get("data_availability"),
            skill_leverage=scores.get("skill_leverage"),
            user_alignment=scores.get("user_alignment"),
            prior_art_risk=scores.get("prior_art_risk"),
            safety_risk=scores.get("safety_risk"),
            cost_risk=scores.get("cost_risk"),
            overall_value=scores.get("overall_value"),
            scoring_rationale=rationale,
        )
        self.db.add(score)

        # Update idea's overall score and classification
        idea = await self.get_idea(idea_id)
        if idea and scores.get("overall_value") is not None:
            idea.overall_score = scores["overall_value"]
            # Auto-classify based on score
            score_val = scores["overall_value"]
            if score_val >= 8.0:
                idea.classification = "high_value"
            elif score_val >= 6.5:
                idea.classification = "promising"
            elif score_val >= 5.0:
                idea.classification = "incremental"
            elif score_val >= 3.5:
                idea.classification = "weak"
            else:
                idea.classification = "reject"

        await self.db.flush()
        return score

    async def add_idea_decision(
        self,
        idea_id: str,
        decision: str,
        reason: str | None = None,
        run_id: str | None = None,
    ) -> IdeaDecision:
        """Add a decision record to an idea."""
        decision_record = IdeaDecision(
            id=str(uuid4()),
            idea_id=idea_id,
            run_id=run_id,
            decision=decision,
            reason=reason,
        )
        self.db.add(decision_record)

        # Update idea status based on decision
        idea = await self.get_idea(idea_id)
        if idea:
            if decision == "reject":
                idea.status = "rejected"
            elif decision == "promote":
                idea.status = "promoted"
            elif decision == "archive":
                idea.status = "archived"

        await self.db.flush()
        return decision_record
