"""Sandbox analysis utilities — power analysis and Plotly visualization."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import get_db
from app.dependencies.auth import get_current_user, require_project_role
from app.engine.power_analysis import proportion_test_power, two_sample_ttest_power
from app.models.collaboration import User
from app.sandbox.executor import SandboxExecutor

router = APIRouter()


class PowerAnalysisRequest(BaseModel):
    project_id: str
    test_type: str = Field(..., pattern="^(two_sample_ttest|two_proportion)$")
    effect_size: float | None = Field(None, gt=0)
    p1: float | None = Field(None, gt=0, lt=1)
    p2: float | None = Field(None, gt=0, lt=1)
    alpha: float = Field(0.05, gt=0, lt=1)
    power: float = Field(0.8, gt=0, lt=1)


class PlotlySandboxRequest(BaseModel):
    project_id: str
    code: str = Field(..., min_length=1)
    title: str = "Plotly Figure"


@router.post("/power-analysis")
async def compute_power_analysis(
    data: PowerAnalysisRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Compute statistical power / required sample size."""
    await require_project_role(db, data.project_id, user.id, "viewer")
    try:
        if data.test_type == "two_sample_ttest":
            if data.effect_size is None:
                raise ValueError("effect_size is required for two_sample_ttest")
            result = two_sample_ttest_power(
                data.effect_size, alpha=data.alpha, power=data.power,
            )
        else:
            if data.p1 is None or data.p2 is None:
                raise ValueError("p1 and p2 are required for two_proportion")
            result = proportion_test_power(
                data.p1, data.p2, alpha=data.alpha, power=data.power,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.as_dict()


@router.post("/plotly")
async def run_plotly_sandbox(
    data: PlotlySandboxRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Execute Plotly visualization code in the isolated sandbox."""
    await require_project_role(db, data.project_id, user.id, "editor")

    settings = get_settings()
    title_json = json.dumps(data.title)
    wrapper = f"""
import json
import sys
{data.code}
if "fig" not in dir():
    raise RuntimeError("Define a Plotly figure as `fig`")
try:
    html = fig.to_html(include_plotlyjs="cdn", full_html=False)
    print(json.dumps({{"html": html, "title": {title_json}}}))
except Exception as exc:
    print(json.dumps({{"error": str(exc)}}), file=sys.stderr)
    sys.exit(1)
"""
    executor = SandboxExecutor(
        docker_image=settings.sandbox_docker_image,
        timeout_seconds=min(settings.sandbox_timeout_seconds, 120),
        memory_limit=settings.sandbox_memory_limit,
        cpu_limit=settings.sandbox_cpu_limit,
    )
    result = await executor.run_python(
        wrapper,
        requirements=["plotly"],
        timeout_seconds=120,
    )

    if not result.success:
        raise HTTPException(
            status_code=422,
            detail=result.error_message or result.stderr or "Plotly sandbox failed",
        )

    try:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid sandbox output: {result.stdout[:500]}",
        ) from exc

    if payload.get("error"):
        raise HTTPException(status_code=422, detail=payload["error"])

    return {
        "title": payload.get("title", data.title),
        "html": payload["html"],
        "duration_ms": result.duration_ms,
    }
