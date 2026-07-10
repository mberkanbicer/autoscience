"""Dataset upload service — validation, schema inference, and provenance tracking."""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any
from uuid import uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Dataset as DatasetModel

logger = structlog.get_logger()

# Heuristic patterns for detecting column types
_INT_PATTERN = re.compile(r"^-?\d+$")
_FLOAT_PATTERN = re.compile(r"^-?\d*\.?\d+(?:[eE][-+]?\d+)?$")
_BOOL_PATTERN = re.compile(r"^(true|false|yes|no|0|1)$", re.IGNORECASE)
_DATE_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?$",
)


class DatasetValidationError(ValueError):
    """Raised when dataset validation fails."""


def _infer_column_type(values: list[str]) -> str:
    """Infer the most likely type for a column of string values."""
    non_empty = [v for v in values if v and v.strip()]
    if not non_empty:
        return "string"

    # Check for booleans
    bool_matches = sum(1 for v in non_empty if _BOOL_PATTERN.match(v.strip()))
    if bool_matches > len(non_empty) * 0.8:
        return "boolean"

    # Check for integers
    int_matches = sum(1 for v in non_empty if _INT_PATTERN.match(v.strip()))
    if int_matches > len(non_empty) * 0.8:
        return "integer"

    # Check for floats
    float_matches = sum(1 for v in non_empty if _FLOAT_PATTERN.match(v.strip()))
    if float_matches > len(non_empty) * 0.8:
        return "float"

    # Check for dates
    date_matches = sum(1 for v in non_empty if _DATE_PATTERN.match(v.strip()))
    if date_matches > len(non_empty) * 0.8:
        return "datetime"

    return "string"


def _infer_schema(headers: list[str], rows: list[list[str]]) -> dict[str, Any]:
    """Infer column schema from parsed data."""
    columns: list[dict[str, Any]] = []
    for i, header in enumerate(headers):
        col_values = [row[i] if i < len(row) else "" for row in rows]
        col_type = _infer_column_type(col_values)
        non_null = sum(1 for v in col_values if v and v.strip())
        columns.append(
            {
                "name": header,
                "type": col_type,
                "non_null_count": non_null,
                "null_count": len(rows) - non_null,
                "sample_values": list(
                    dict.fromkeys(v.strip() for v in col_values if v and v.strip())[:5],
                ),
            },
        )
    return {"columns": columns, "total_rows": len(rows), "total_columns": len(headers)}


def _parse_csv(content: str) -> tuple[list[str], list[list[str]]]:
    """Parse CSV content and return (headers, rows)."""
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        raise DatasetValidationError("CSV file is empty")

    headers = [h.strip() for h in rows[0]]
    data_rows = rows[1:]

    # Validate consistent column counts
    for i, row in enumerate(data_rows):
        if len(row) != len(headers):
            raise DatasetValidationError(
                f"Row {i + 1} has {len(row)} columns, expected {len(headers)}",
            )

    return headers, data_rows


def _parse_json(content: str) -> tuple[list[str], list[list[str]]]:
    """Parse JSON content as a list of records and return (headers, rows)."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise DatasetValidationError(f"Invalid JSON: {exc}") from exc

    if isinstance(data, dict):
        # If it's a single object, wrap it
        data = [data]

    if not isinstance(data, list) or not data:
        raise DatasetValidationError("JSON must be an array of objects")

    if not isinstance(data[0], dict):
        raise DatasetValidationError("JSON rows must be objects")

    # Extract headers from keys of all objects
    headers_set: set[str] = set()
    for row in data:
        headers_set.update(row.keys())
    headers = sorted(headers_set)

    # Convert to string rows
    data_rows: list[list[str]] = []
    for row in data:
        data_rows.append([str(row.get(h, "")) for h in headers])

    return headers, data_rows


async def validate_and_infer(
    content: str,
    file_format: str,
    db: AsyncSession,
    project_id: str,
    uploaded_by: str | None = None,
    original_filename: str | None = None,
) -> dict[str, Any]:
    """Parse, validate, and infer schema from uploaded dataset content.

    Returns a dict with dataset metadata and a preview of rows.
    """
    file_format = file_format.lower().strip(".")
    if file_format == "csv":
        headers, data_rows = _parse_csv(content)
    elif file_format in ("json", "jsonl"):
        headers, data_rows = _parse_json(content)
    else:
        raise DatasetValidationError(f"Unsupported format: {file_format}. Use csv or json.")

    if not data_rows:
        raise DatasetValidationError("File contains no data rows after headers")

    # Infer schema
    schema = _infer_schema(headers, data_rows)
    size_bytes = len(content.encode("utf-8"))

    # Build preview (first 10 rows)
    preview_rows: list[dict[str, Any]] = []
    for row in data_rows[:10]:
        preview_rows.append(dict(zip(headers, row)))

    # Auto-generate a name from filename if available
    name = (original_filename or "uploaded_dataset").rsplit(".", 1)[0]
    name = name.replace("_", " ").replace("-", " ").title()

    # Persist the dataset record
    dataset = DatasetModel(
        id=str(uuid4()),
        project_id=project_id,
        name=name,
        description=f"Uploaded from {original_filename or 'direct input'} ({file_format.upper()}, {len(data_rows)} rows)",
        format=file_format,
        size_bytes=size_bytes,
        row_count=len(data_rows),
        column_count=len(headers),
        schema_json=schema,
        uploaded_by=uploaded_by,
        original_filename=original_filename,
        provenance="upload",
    )
    db.add(dataset)
    await db.flush()
    await db.refresh(dataset)

    # Collect warnings
    warnings: list[str] = []
    for col in schema.get("columns", []):
        null_pct = col["null_count"] / max(schema["total_rows"], 1) * 100
        if null_pct > 50:
            warnings.append(
                f"Column '{col['name']}' is >50% empty ({col['null_count']}/{schema['total_rows']} nulls)",
            )

    return {
        "id": dataset.id,
        "name": name,
        "format": file_format,
        "row_count": schema["total_rows"],
        "column_count": schema["total_columns"],
        "size_bytes": size_bytes,
        "column_schema": schema,
        "preview_rows": preview_rows,
        "warnings": warnings,
    }
