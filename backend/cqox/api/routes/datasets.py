"""
Dataset management endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from loguru import logger

from cqox.data.loader import DatasetRegistry

router = APIRouter()


class DatasetCreate(BaseModel):
    """Dataset creation request"""
    dataset_id: str
    name: str
    description: Optional[str] = None
    file_path: str


@router.get("/")
async def list_datasets():
    """List all registered datasets"""
    try:
        registry = DatasetRegistry()
        datasets = registry.list_datasets()
        return {"datasets": datasets}
    except Exception as e:
        logger.error(f"List datasets failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str):
    """Get dataset details"""
    try:
        registry = DatasetRegistry()
        dataset = registry.get_dataset(dataset_id)
        return dataset
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Get dataset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_dataset(request: DatasetCreate):
    """Register a new dataset"""
    try:
        registry = DatasetRegistry()

        metadata = {
            "name": request.name,
            "description": request.description,
            "file_path": request.file_path
        }

        registry.register_dataset(request.dataset_id, metadata)

        return {
            "success": True,
            "dataset_id": request.dataset_id
        }
    except Exception as e:
        logger.error(f"Create dataset failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """Delete a dataset"""
    try:
        registry = DatasetRegistry()
        registry.delete_dataset(dataset_id)

        logger.info(f"Dataset deleted: {dataset_id}")
        return {
            "success": True,
            "message": f"Dataset {dataset_id} deleted successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Delete dataset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
