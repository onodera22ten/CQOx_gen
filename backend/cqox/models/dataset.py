"""
Pydantic models for Dataset API
"""
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, ConfigDict


class DatasetBase(BaseModel):
    """Base dataset model"""
    name: str = Field(..., description="Dataset name")
    description: Optional[str] = Field(None, description="Dataset description")


class DatasetCreate(DatasetBase):
    """Dataset creation request"""
    pass


class DatasetUpdate(BaseModel):
    """Dataset update request"""
    name: Optional[str] = None
    description: Optional[str] = None


class DatasetResponse(DatasetBase):
    """Dataset response model"""
    id: int
    user_id: int
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    columns_info: Optional[Dict[str, str]] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetUploadResponse(BaseModel):
    """Response after dataset upload"""
    dataset_id: int
    message: str
    row_count: int
    column_count: int
    columns: List[str]
    suggestions: Dict[str, Any]


class DatasetColumnsResponse(BaseModel):
    """Dataset columns information"""
    dataset_id: int
    columns: List[str]
    schema: Dict[str, str]
    suggestions: Dict[str, Any]
    row_count: int


class DatasetPreviewResponse(BaseModel):
    """Dataset preview response"""
    columns: List[str]
    data: List[Dict[str, Any]]
    row_count: int
    total_rows: int
