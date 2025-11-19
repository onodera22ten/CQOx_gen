"""
Dataset management endpoints (v2) with authentication
"""
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from cqox.db.database import get_db
from cqox.db.models import User
from cqox.api.dependencies.auth import get_current_active_user
from cqox.models.dataset import (
    DatasetResponse,
    DatasetCreate,
    DatasetUpdate,
    DatasetUploadResponse,
    DatasetColumnsResponse,
    DatasetPreviewResponse
)
from cqox.services.dataset_service import DatasetService

router = APIRouter(prefix="/datasets", tags=["datasets"])

# Upload directory
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/", response_model=List[DatasetResponse])
async def list_datasets(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all datasets for the current user
    """
    datasets = DatasetService.get_datasets_by_user(db, current_user.id, skip, limit)
    return datasets


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get dataset details by ID
    """
    dataset = DatasetService.get_dataset_by_id(db, dataset_id, current_user.id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    return dataset


@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a new dataset (CSV or Parquet)
    """
    # Validate file extension
    if not (file.filename.endswith('.csv') or file.filename.endswith('.parquet')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and Parquet files are supported"
        )

    # Create user-specific upload directory
    user_upload_dir = os.path.join(UPLOAD_DIR, f"user_{current_user.id}")
    os.makedirs(user_upload_dir, exist_ok=True)

    # Save uploaded file
    file_path = os.path.join(user_upload_dir, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create dataset record
        dataset = DatasetService.create_dataset(
            db=db,
            user_id=current_user.id,
            name=name,
            file_path=file_path,
            description=description
        )

        # Process file to extract metadata
        file_stats = DatasetService.process_uploaded_file(file_path)

        # Update dataset with stats
        dataset = DatasetService.update_dataset_stats(
            db=db,
            dataset_id=dataset.id,
            row_count=file_stats['row_count'],
            column_count=file_stats['column_count'],
            columns_info=file_stats['columns_info']
        )

        return DatasetUploadResponse(
            dataset_id=dataset.id,
            message="Dataset uploaded successfully",
            row_count=file_stats['row_count'],
            column_count=file_stats['column_count'],
            columns=list(file_stats['columns_info'].keys()),
            suggestions=file_stats['suggestions']
        )

    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload dataset: {str(e)}"
        )


@router.get("/{dataset_id}/columns", response_model=DatasetColumnsResponse)
async def get_dataset_columns(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get column information for a dataset
    """
    dataset = DatasetService.get_dataset_by_id(db, dataset_id, current_user.id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    if not dataset.columns_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset metadata not available"
        )

    # Re-process file for suggestions
    file_stats = DatasetService.process_uploaded_file(dataset.file_path)

    return DatasetColumnsResponse(
        dataset_id=dataset.id,
        columns=list(dataset.columns_info.keys()),
        schema=dataset.columns_info,
        suggestions=file_stats['suggestions'],
        row_count=dataset.row_count or 0
    )


@router.post("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
async def preview_dataset(
    dataset_id: int,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Preview dataset contents
    """
    dataset = DatasetService.get_dataset_by_id(db, dataset_id, current_user.id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    try:
        preview_data = DatasetService.get_dataset_preview(dataset.file_path, limit)

        return DatasetPreviewResponse(
            columns=preview_data['columns'],
            data=preview_data['data'],
            row_count=preview_data['row_count'],
            total_rows=dataset.row_count or 0
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview dataset: {str(e)}"
        )


@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: int,
    update_data: DatasetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update dataset metadata
    """
    dataset = DatasetService.get_dataset_by_id(db, dataset_id, current_user.id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    # Update fields
    if update_data.name is not None:
        dataset.name = update_data.name
    if update_data.description is not None:
        dataset.description = update_data.description

    db.commit()
    db.refresh(dataset)

    return dataset


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a dataset
    """
    success = DatasetService.delete_dataset(db, dataset_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    return {
        "message": "Dataset deleted successfully",
        "dataset_id": dataset_id
    }
