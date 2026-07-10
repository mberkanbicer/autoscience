"""Artifact storage for analysis results."""

import json
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import AnalysisArtifact, AnalysisRun


class ArtifactStorage:
    """Storage for analysis artifacts."""

    def __init__(self, base_dir: str = "artifacts"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_run_dir(self, hypothesis_id: str) -> Path:
        """Create a directory for an analysis run."""
        run_id = str(uuid4())
        run_dir = self.base_dir / hypothesis_id / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def save_script(self, run_dir: Path, script: str) -> Path:
        """Save analysis script."""
        script_path = run_dir / "analysis.py"
        script_path.write_text(script)
        return script_path

    def save_output(self, run_dir: Path, filename: str, content: bytes) -> Path:
        """Save output file."""
        output_dir = run_dir / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / filename
        output_path.write_bytes(content)
        return output_path

    def save_results(self, run_dir: Path, results: dict[str, Any]) -> Path:
        """Save results as JSON."""
        results_path = run_dir / "results.json"
        results_path.write_text(json.dumps(results, indent=2, default=str))
        return results_path

    def save_figure(
        self,
        run_dir: Path,
        figure_data: bytes,
        filename: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Save a figure and return artifact info."""
        output_dir = run_dir / "figures"
        output_dir.mkdir(exist_ok=True)

        filepath = output_dir / filename
        filepath.write_bytes(figure_data)

        return {
            "id": str(uuid4()),
            "type": "figure",
            "filename": filename,
            "filepath": str(filepath),
            "description": description,
            "size_bytes": len(figure_data),
            "created_at": datetime.now(UTC).isoformat(),
        }

    def save_table(
        self,
        run_dir: Path,
        table_data: str,
        filename: str,
        format: str = "csv",
        description: str = "",
    ) -> dict[str, Any]:
        """Save a table and return artifact info."""
        output_dir = run_dir / "tables"
        output_dir.mkdir(exist_ok=True)

        filepath = output_dir / filename
        filepath.write_text(table_data)

        return {
            "id": str(uuid4()),
            "type": "table",
            "filename": filename,
            "filepath": str(filepath),
            "format": format,
            "description": description,
            "size_bytes": len(table_data),
            "created_at": datetime.now(UTC).isoformat(),
        }

    def get_run_artifacts(self, run_dir: Path) -> list[dict[str, Any]]:
        """Get all artifacts from a run directory."""
        artifacts = []

        for artifact_dir in ["output", "figures", "tables"]:
            dir_path = run_dir / artifact_dir
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        artifacts.append({
                            "type": artifact_dir.rstrip("s"),
                            "filename": file_path.name,
                            "filepath": str(file_path.relative_to(run_dir)),
                            "size_bytes": file_path.stat().st_size,
                        })

        return artifacts


class ArtifactService:
    """Service for storing artifacts in database."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_run(
        self,
        hypothesis_id: str,
        script: str,
        status: str,
        dataset_id: str | None = None,
    ) -> AnalysisRun:
        """Store an analysis run."""
        run = AnalysisRun(
            id=str(uuid4()),
            hypothesis_id=hypothesis_id,
            dataset_id=dataset_id,
            script=script,
            status=status,
        )
        self.db.add(run)
        await self.db.flush()
        return run

    async def update_run_status(
        self,
        run_id: str,
        status: str,
        error_message: str | None = None,
    ) -> AnalysisRun | None:
        """Update run status."""
        result = await self.db.execute(
            select(AnalysisRun).where(AnalysisRun.id == run_id),
        )
        run = result.scalar_one_or_none()

        if run:
            run.status = status
            if error_message:
                run.error_message = error_message
            await self.db.flush()

        return run

    async def store_artifact(
        self,
        run_id: str,
        artifact_type: str,
        file_path: str,
        description: str = "",
    ) -> AnalysisArtifact:
        """Store an analysis artifact."""
        artifact = AnalysisArtifact(
            id=str(uuid4()),
            analysis_run_id=run_id,
            artifact_type=artifact_type,
            file_path=file_path,
            description=description,
        )
        self.db.add(artifact)
        await self.db.flush()
        return artifact

    async def get_run_artifacts(
        self,
        run_id: str,
    ) -> list[AnalysisArtifact]:
        """Get all artifacts for a run."""
        result = await self.db.execute(
            select(AnalysisArtifact).where(
                AnalysisArtifact.analysis_run_id == run_id,
            ),
        )
        return list(result.scalars().all())

    async def get_hypothesis_runs(
        self,
        hypothesis_id: str,
    ) -> list[AnalysisRun]:
        """Get all runs for a hypothesis."""
        result = await self.db.execute(
            select(AnalysisRun).where(
                AnalysisRun.hypothesis_id == hypothesis_id,
            ),
        )
        return list(result.scalars().all())
