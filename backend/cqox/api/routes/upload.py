"""
Upload and column mapping endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import pandas as pd
import tempfile
from pathlib import Path
from loguru import logger

from cqox.data.loader import DataLoader
from cqox.data.column_mapping import (
    suggest_mapping,
    validate_mapping,
    apply_mapping,
    validate_normalized_data,
    MappingProfileManager
)

router = APIRouter()


class MappingRequest(BaseModel):
    """Request to apply column mapping"""
    upload_id: str
    mapping: Dict[str, str]
    save_profile: bool = False
    profile_name: Optional[str] = None


class MappingResponse(BaseModel):
    """Response with mapping suggestions"""
    upload_id: str
    columns: List[str]
    suggested_mapping: Dict[str, Optional[str]]
    required_columns: List[str]
    missing_required: List[str]


@router.post("/", response_model=Dict)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload CSV/Parquet file and get column mapping suggestions

    Returns upload ID and suggested column mappings
    """
    logger.info(f"Uploading file: {file.filename}")

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Load file to get column names
        df = DataLoader.load_auto(tmp_path)
        upload_id = Path(tmp_path).stem

        # Get column suggestions
        suggested = suggest_mapping(list(df.columns))

        # Validate
        is_valid, missing = validate_mapping(suggested)

        response = MappingResponse(
            upload_id=upload_id,
            columns=list(df.columns),
            suggested_mapping=suggested,
            required_columns=["unit_id", "time", "treatment", "y"],
            missing_required=missing
        )

        logger.info(f"Upload successful: {upload_id}")
        return response.dict()

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/apply-mapping")
async def apply_column_mapping(request: MappingRequest):
    """
    Apply column mapping and validate normalized data

    If successful, saves normalized dataset
    """
    logger.info(f"Applying mapping for upload: {request.upload_id}")

    try:
        # Load upload file (from temp path)
        upload_path = Path(tempfile.gettempdir()) / f"{request.upload_id}{Path(request.upload_id).suffix}"

        if not upload_path.exists():
            # Try common extensions
            for ext in ['.csv', '.parquet']:
                test_path = Path(tempfile.gettempdir()) / f"{request.upload_id}{ext}"
                if test_path.exists():
                    upload_path = test_path
                    break

        if not upload_path.exists():
            raise HTTPException(status_code=404, detail="Upload not found")

        df = DataLoader.load_auto(upload_path)

        # Validate mapping
        is_valid, missing = validate_mapping(request.mapping)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing}"
            )

        # Apply mapping
        df_normalized = apply_mapping(df, request.mapping)

        # Validate normalized data
        is_valid, validation_report = validate_normalized_data(df_normalized)

        if not is_valid:
            return {
                "success": False,
                "validation_report": validation_report,
                "errors": validation_report['errors']
            }

        # Save normalized dataset
        from cqox.config import settings
        dataset_id = f"dataset_{request.upload_id}"
        normalized_path = settings.artifacts_dir / dataset_id / "normalized.parquet"
        normalized_path.parent.mkdir(parents=True, exist_ok=True)

        DataLoader.save_parquet(df_normalized, normalized_path)

        # Save profile if requested
        if request.save_profile and request.profile_name:
            profile_manager = MappingProfileManager()
            profile_manager.save_profile(
                request.profile_name,
                request.mapping,
                metadata={'upload_id': request.upload_id, 'dataset_id': dataset_id}
            )

        logger.info(f"Mapping applied successfully: {dataset_id}")

        return {
            "success": True,
            "dataset_id": dataset_id,
            "normalized_path": str(normalized_path),
            "validation_report": validation_report,
            "row_count": len(df_normalized),
            "column_count": len(df_normalized.columns)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Apply mapping failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profiles")
async def list_mapping_profiles():
    """List available mapping profiles"""
    try:
        profile_manager = MappingProfileManager()
        profiles = profile_manager.list_profiles()
        return {"profiles": profiles}
    except Exception as e:
        logger.error(f"List profiles failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{profile_name}")
async def get_mapping_profile(profile_name: str):
    """Get a specific mapping profile"""
    try:
        profile_manager = MappingProfileManager()
        mapping = profile_manager.load_profile(profile_name)
        return {"profile_name": profile_name, "mapping": mapping}
    except Exception as e:
        logger.error(f"Get profile failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
