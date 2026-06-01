"""Dataset API endpoints."""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..models.report import Dataset
from ..schemas.dataset import DatasetCreate, DatasetResponse, DatasetUpdate

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=list[DatasetResponse])
async def list_datasets(
    project_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List datasets, optionally filtered by project."""
    query = select(Dataset)
    if project_id:
        query = query.where(Dataset.project_id == project_id)
    query = query.order_by(Dataset.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    data: DatasetCreate,
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Create a dataset record."""
    dataset = Dataset(
        id=str(uuid4()),
        project_id=project_id,
        name=data.name,
        description=data.description,
        source_url=data.source_url,
        format=data.format,
        size_bytes=data.size_bytes,
        row_count=data.row_count,
        column_count=data.column_count,
        schema_json=data.schema_json,
    )
    db.add(dataset)
    await db.flush()
    await db.commit()
    return dataset


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a dataset by ID."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, detail="Dataset not found")
    return dataset


@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: str,
    data: DatasetUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a dataset."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, detail="Dataset not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(dataset, key, value)

    await db.flush()
    await db.commit()
    return dataset


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a dataset."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, detail="Dataset not found")
    await db.delete(dataset)
    await db.commit()
