"""Column suggestion API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, List, Any, Optional
import os
import uuid as uuid_lib
import pandas as pd

from cqox.auth.dependencies import get_current_user
from cqox.database.connection import get_db
from cqox.database.models import Dataset
from cqox.engine.column_inference import infer_column_roles, ColumnSuggestion
from pydantic import BaseModel

router = APIRouter()


class ColumnSuggestionDTO(BaseModel):
    role: str
    column: str
    score: float
    reason: str


class ColumnInferenceResponse(BaseModel):
    dataset_id: str
    suggestions: Dict[str, List[ColumnSuggestionDTO]]


def _resolve_dataset_path(dataset_path: str) -> str:
    if not dataset_path:
        raise FileNotFoundError("Dataset file path is empty")

    candidates = [
        dataset_path,
        os.path.join("/app/data/uploads", os.path.basename(dataset_path)),
        os.path.join("/home/hirokionodera/CQOx_gen/backend/data/uploads", os.path.basename(dataset_path)),
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    raise FileNotFoundError(f"Dataset file not found in expected locations: {dataset_path}")


def _load_dataset(path: str, max_rows: int = 5000) -> pd.DataFrame:
    _, ext = os.path.splitext(path.lower())

    if ext in {".parquet", ".pq"}:
        df = pd.read_parquet(path)
    elif ext in {".csv", ".txt"}:
        df = pd.read_csv(path, nrows=max_rows)
    elif ext in {".json"}:
        df = pd.read_json(path)
    elif ext in {".xls", ".xlsx"}:
        df = pd.read_excel(path, nrows=max_rows)
    else:
        df = pd.read_csv(path, nrows=max_rows)

    if len(df) > max_rows:
        df = df.head(max_rows)

    return df


def _resolve_tenant_id(current_user: Any) -> Optional[uuid_lib.UUID]:
    if isinstance(current_user, dict):
        candidate = current_user.get("tenant_id")
    else:
        candidate = getattr(current_user, "tenant_id", None)

    if not candidate:
        return None

    try:
        return uuid_lib.UUID(str(candidate))
    except (ValueError, TypeError):
        return None


@router.get("/datasets/{dataset_id}/column-suggestions", response_model=ColumnInferenceResponse)
async def get_column_suggestions(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> ColumnInferenceResponse:
    tenant_id = _resolve_tenant_id(current_user)

    filters = [Dataset.id == dataset_id]
    if tenant_id is not None:
        filters.append(Dataset.tenant_id == tenant_id)

    result = await db.execute(select(Dataset).where(*filters))
    dataset = result.scalar_one_or_none()

    if not dataset or not dataset.file_path:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        file_path = _resolve_dataset_path(dataset.file_path)
        df = _load_dataset(file_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=f"Failed to load dataset: {exc}") from exc

    suggestions = infer_column_roles(df)

    payload = {
        role: [
            ColumnSuggestionDTO(role=s.role, column=s.column, score=s.score, reason=s.reason)
            for s in items
        ]
        for role, items in suggestions.items()
    }

    return ColumnInferenceResponse(dataset_id=dataset_id, suggestions=payload)
