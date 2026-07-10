"""Dataset API endpoints."""

import csv
import io
import json
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.dataset_connectors import DatasetManager
from app.dependencies import get_db
from app.dependencies.auth import get_current_user, require_project_role
from app.models.collaboration import User
from app.models.report import Dataset as DatasetModel
from app.schemas.dataset import DatasetCreate, DatasetResponse, DatasetUploadResponse
from app.services.dataset_upload_service import DatasetValidationError, validate_and_infer

router = APIRouter()
dataset_manager = DatasetManager()


@router.get("/search", response_model=list[dict])
async def search_datasets(
    query: Annotated[str, Query()],
    limit: Annotated[int, Query()] = 20,
):
    """Search for datasets across multiple sources."""
    results = await dataset_manager.search_all(query, limit)
    return results


@router.get("/external")
async def get_external_dataset(
    source: Annotated[str, Query(description="Connector name: huggingface, zenodo, kaggle")],
    identifier: Annotated[str, Query(description="Dataset ID (slashes allowed, e.g. owner/name)")],
):
    """Get dataset details from an external source."""
    result = await dataset_manager.get_dataset(source, identifier)
    if not result:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return result


@router.get("/export")
async def export_datasets(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Annotated[str, Query()],
    format: Annotated[str, Query(pattern="^(json|csv)$")] = "json",
):
    """Export project datasets as JSON or CSV."""
    result = await db.execute(
        select(DatasetModel)
        .where(DatasetModel.project_id == project_id)
        .order_by(DatasetModel.created_at.desc()),
    )
    rows = result.scalars().all()
    payload = [
        {
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "source_url": d.source_url,
            "format": d.format,
            "row_count": d.row_count,
            "column_count": d.column_count,
            "size_bytes": d.size_bytes,
        }
        for d in rows
    ]
    if format == "csv":
        buffer = io.StringIO()
        if payload:
            writer = csv.DictWriter(buffer, fieldnames=payload[0].keys())
            writer.writeheader()
            writer.writerows(payload)
        return Response(
            content=buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="datasets-{project_id}.csv"'},
        )
    return Response(
        content=json.dumps(payload, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="datasets-{project_id}.json"'},
    )


@router.get("", response_model=list[DatasetResponse])
async def list_datasets(
    project_id: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List datasets for a project."""
    result = await db.execute(
        select(DatasetModel)
        .where(DatasetModel.project_id == project_id)
        .order_by(DatasetModel.created_at.desc()),
    )
    return result.scalars().all()


@router.post("", response_model=DatasetResponse)
async def create_dataset(
    data: DatasetCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Create a dataset record linked to a project."""
    await require_project_role(db, data.project_id, user.id, "editor")
    dataset = DatasetModel(
        id=str(uuid4()),
        project_id=data.project_id,
        name=data.name,
        description=data.description,
        source_url=data.source_url,
        format=data.format,
        size_bytes=data.size_bytes,
        row_count=data.row_count,
        column_count=data.column_count,
        schema_json=data.column_schema,
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return dataset


@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(
    project_id: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Upload a CSV or JSON file, validate it, infer schema, and persist."""
    await require_project_role(db, project_id, user.id, "editor")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("csv", "json", "jsonl"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Accepted: .csv, .json, .jsonl",
        )

    try:
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8-sig")  # handles BOM
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400, detail="File encoding not supported. Use UTF-8.",
        ) from exc

    if not content.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        result = await validate_and_infer(
            content=content,
            file_format=ext,
            db=db,
            project_id=project_id,
            uploaded_by=user.display_name or user.email,
            original_filename=file.filename,
        )
    except DatasetValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    await db.commit()
    return result


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a dataset by ID."""
    result = await db.execute(
        select(DatasetModel).where(DatasetModel.id == dataset_id),
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset
