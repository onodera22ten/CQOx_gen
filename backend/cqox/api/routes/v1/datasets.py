"""
v1 Datasets API Routes

データセット管理（アップロード、一覧、詳細、削除）
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List
from uuid import uuid4
from datetime import datetime, timedelta
import logging

from cqox.models.v1 import (
    DatasetInfo,
    DatasetUploadRequest,
    DatasetUploadResponse
)
from cqox.database.connection import get_db
from cqox.auth.dependencies import get_current_user


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/datasets", tags=["v1-datasets"])


@router.post("/upload", response_model=DatasetUploadResponse, status_code=201)
async def create_dataset_upload(
    request: DatasetUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    データセットアップロード開始
    
    **手順**:
    1. このAPIでメタデータを登録し、Pre-signed URLを取得
    2. クライアントが直接S3にファイルをアップロード
    3. アップロード完了後、confirm APIを呼ぶ（実装省略）
    """
    from cqox.database.models import Dataset
    
    dataset_id = str(uuid4())
    
    # Dataset metadata作成
    dataset = Dataset(
        id=dataset_id,
        name=request.name,
        description=request.description,
        file_path=None,  # アップロード完了後に更新
        row_count=None,
        column_count=None,
        schema=None,
        tenant_id=current_user.get("tenant_id", "default_tenant"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    
    # Pre-signed URL生成（簡略版: 実際はS3/MinIO使用）
    upload_url = f"s3://cqox-datasets/{dataset_id}/{request.name}.parquet"
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    logger.info(f"Dataset created: {dataset_id} (name={request.name})")
    
    return DatasetUploadResponse(
        dataset_id=dataset_id,
        upload_url=upload_url,
        expires_at=expires_at,
        candidate_profiles=[]  # TODO: 自動推定されたColumn Mapping候補
    )


@router.get("", response_model=List[DatasetInfo])
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """データセット一覧取得"""
    from cqox.database.models import Dataset
    
    tenant_id = current_user.get("tenant_id", "default_tenant")
    
    # ページネーション
    offset = (page - 1) * page_size
    query = select(Dataset).where(
        Dataset.tenant_id == tenant_id
    ).order_by(desc(Dataset.created_at)).limit(page_size).offset(offset)
    
    result = await db.execute(query)
    datasets = result.scalars().all()
    
    return [DatasetInfo.from_orm(d) for d in datasets]


@router.get("/{dataset_id}", response_model=DatasetInfo)
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """データセット詳細取得"""
    from cqox.database.models import Dataset
    
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.tenant_id == current_user.get("tenant_id", "default_tenant")
        )
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return DatasetInfo.from_orm(dataset)


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """データセット削除"""
    from cqox.database.models import Dataset
    
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.tenant_id == current_user.get("tenant_id", "default_tenant")
        )
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    await db.delete(dataset)
    await db.commit()
    
    logger.info(f"Dataset deleted: {dataset_id}")
    return None


@router.get("/{dataset_id}/columns")
async def get_dataset_columns(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    データセットのカラム情報取得

    Returns:
        - columns: List of column names
        - schema: Column name -> type mapping
        - suggestions: Suggested column mapping for treatment/outcome/features
    """
    from cqox.database.models import Dataset
    import pandas as pd
    import os
    import uuid as uuid_lib

    try:
        # Try to parse UUID
        dataset_uuid = uuid_lib.UUID(dataset_id)
    except (ValueError, AttributeError) as e:
        logger.error(f"Invalid dataset ID format: {dataset_id}")
        raise HTTPException(status_code=400, detail=f"Invalid dataset ID format: {str(e)}")

    try:
        # Query only necessary columns to avoid schema mismatch
        result = await db.execute(
            select(Dataset.id, Dataset.name, Dataset.file_path).where(Dataset.id == dataset_uuid)
        )
        row = result.first()

        if not row:
            raise HTTPException(status_code=404, detail="Dataset not found")

        dataset_file_path = row[2]  # file_path

        if not dataset_file_path:
            raise HTTPException(status_code=400, detail="File not yet uploaded")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Read file to get column info
    try:
        # Convert relative path to absolute if needed
        file_path = dataset_file_path
        if not os.path.isabs(file_path):
            # Try multiple possible locations
            possible_paths = [
                os.path.join("/app/data/uploads", os.path.basename(file_path)),
                os.path.join("/home/hirokionodera/CQOx_gen/backend/data/uploads", os.path.basename(file_path)),
                file_path  # Try as-is
            ]

            file_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    file_path = path
                    break

            if not file_path:
                raise FileNotFoundError(f"Dataset file not found in any expected location: {dataset_file_path}")

        # Read first few rows to get columns and infer types
        # Support multiple file formats
        if file_path.endswith('.parquet'):
            df = pd.read_parquet(file_path)
            df = df.head(100)  # Limit to first 100 rows
        elif file_path.endswith(('.csv', '.txt')):
            df = pd.read_csv(file_path, nrows=100)
        elif file_path.endswith('.json'):
            df = pd.read_json(file_path, lines=True, nrows=100)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path, nrows=100)
        else:
            # Try CSV as default
            df = pd.read_csv(file_path, nrows=100)

        columns = df.columns.tolist()
        schema = {col: str(dtype) for col, dtype in df.dtypes.items()}

        # Auto-suggest column mapping based on common patterns
        suggestions = {
            "treatment_col": None,
            "outcome_col": None,
            "feature_cols": []
        }

        # Treatment column detection
        treatment_keywords = ['treatment', 'treat', 'intervention', 'exposed', 'group']
        for col in columns:
            if any(kw in col.lower() for kw in treatment_keywords):
                suggestions["treatment_col"] = col
                break

        # Outcome column detection
        outcome_keywords = ['outcome', 'revenue', 'conversion', 'result', 'sales', 'profit', 'y']
        for col in columns:
            if any(kw in col.lower() for kw in outcome_keywords):
                suggestions["outcome_col"] = col
                break

        # Feature columns: exclude treatment and outcome, prefer numeric only
        excluded = set()
        if suggestions["treatment_col"]:
            excluded.add(suggestions["treatment_col"])
        if suggestions["outcome_col"]:
            excluded.add(suggestions["outcome_col"])

        # Exclude ID-like and date-like columns
        id_keywords = ['id', 'user_id', 'customer_id', 'index', 'date', 'time', 'timestamp']
        for col in columns:
            if any(kw == col.lower() or col.lower().endswith(kw) for kw in id_keywords):
                excluded.add(col)

        # Only include numeric columns as features
        numeric_types = ['int64', 'float64', 'int32', 'float32', 'int16', 'float16', 'int8']
        suggestions["feature_cols"] = [
            col for col in columns
            if col not in excluded and schema.get(col, 'object') in numeric_types
        ]

        # If no treatment/outcome found, try fallback patterns
        if not suggestions["treatment_col"] and 'x0' in columns:
            # Fallback: if columns are named x0, x1, ... assume x0 is treatment
            numeric_x_cols = [c for c in columns if c.startswith('x') and c[1:].isdigit()]
            if numeric_x_cols:
                suggestions["treatment_col"] = numeric_x_cols[0] if len(numeric_x_cols) > 0 else None
                suggestions["feature_cols"] = numeric_x_cols[1:] if len(numeric_x_cols) > 1 else []

        if not suggestions["outcome_col"] and 'y' in columns:
            suggestions["outcome_col"] = 'y'

        logger.info(f"Dataset columns fetched: {dataset_id}, columns={len(columns)}")

        return {
            "dataset_id": dataset_id,
            "columns": columns,
            "schema": schema,
            "suggestions": suggestions,
            "row_count": len(df),
            "total_rows": len(df)
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset file not found: {dataset_file_path}")
    except Exception as e:
        logger.error(f"Failed to read dataset columns: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read dataset: {str(e)}")


@router.post("/{dataset_id}/preview")
async def preview_dataset(
    dataset_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    データセットプレビュー

    先頭N行を返す（Parquetファイルから読み込み）
    """
    from cqox.database.models import Dataset

    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.tenant_id == current_user.get("tenant_id", "default_tenant")
        )
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if not dataset.file_path:
        raise HTTPException(status_code=400, detail="File not yet uploaded")

    # TODO: 実際のParquet読み込み実装
    # import pyarrow.parquet as pq
    # table = pq.read_table(dataset.file_path, columns=None)
    # df = table.to_pandas().head(limit)

    return {
        "dataset_id": dataset_id,
        "rows": [],  # df.to_dict('records')
        "schema": dataset.schema or {},
        "total_rows": dataset.row_count or 0
    }

