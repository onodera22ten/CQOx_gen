"""
Analysis API endpoints (v2) with authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from cqox.db.database import get_db
from cqox.db.models import User
from cqox.api.dependencies.auth import get_current_active_user
from cqox.models.analysis import (
    AnalysisResponse,
    AnalysisRunRequest
)
from cqox.services.analysis_service import AnalysisService
from cqox.services.dataset_service import DatasetService

router = APIRouter(prefix="/analysis", tags=["analysis"])


def run_analysis_background(
    db: Session,
    analysis_id: int,
    dataset_path: str,
    treatment_col: str,
    outcome_col: str,
    feature_cols: List[str],
    estimators: List[str]
):
    """Background task to run analysis"""
    try:
        AnalysisService.run_causal_analysis(
            db=db,
            analysis_id=analysis_id,
            dataset_path=dataset_path,
            treatment_col=treatment_col,
            outcome_col=outcome_col,
            feature_cols=feature_cols,
            estimators=estimators
        )
    except Exception as e:
        print(f"Background analysis failed: {e}")


@router.post("/run", response_model=AnalysisResponse)
async def run_analysis(
    request: AnalysisRunRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Start a new causal analysis

    This endpoint:
    1. Creates an analysis record
    2. Starts background processing
    3. Returns immediately with analysis_id and status
    """
    # Validate dataset exists and user has access
    try:
        dataset_id = int(request.dataset_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset_id format"
        )

    dataset = DatasetService.get_dataset_by_id(db, dataset_id, current_user.id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    # Create analysis record
    estimator_type = ','.join(request.estimators)
    analysis = AnalysisService.create_analysis(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
        estimator_type=estimator_type,
        treatment_col=request.treatment_col,
        outcome_col=request.outcome_col,
        feature_cols=request.feature_cols
    )

    # Start background analysis
    background_tasks.add_task(
        run_analysis_background,
        db=db,
        analysis_id=analysis.id,
        dataset_path=dataset.file_path,
        treatment_col=request.treatment_col,
        outcome_col=request.outcome_col,
        feature_cols=request.feature_cols,
        estimators=request.estimators
    )

    return AnalysisResponse(
        analysis_id=analysis.id,
        dataset_id=analysis.dataset_id,
        user_id=analysis.user_id,
        estimator_type=analysis.estimator_type,
        treatment_col=analysis.treatment_col,
        outcome_col=analysis.outcome_col,
        feature_cols=analysis.feature_cols,
        status=analysis.status,
        started_at=analysis.started_at
    )


@router.get("/", response_model=List[AnalysisResponse])
async def list_analyses(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all analyses for the current user
    """
    analyses = AnalysisService.get_analyses_by_user(
        db, current_user.id, skip, limit, status
    )
    return [AnalysisResponse(
        analysis_id=a.id,
        dataset_id=a.dataset_id,
        user_id=a.user_id,
        estimator_type=a.estimator_type,
        treatment_col=a.treatment_col,
        outcome_col=a.outcome_col,
        feature_cols=a.feature_cols,
        status=a.status,
        started_at=a.started_at,
        completed_at=a.completed_at,
        results=a.results,
        error_message=a.error_message
    ) for a in analyses]


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get analysis status and results by ID
    """
    analysis = AnalysisService.get_analysis_by_id(db, analysis_id, current_user.id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    return AnalysisResponse(
        analysis_id=analysis.id,
        dataset_id=analysis.dataset_id,
        user_id=analysis.user_id,
        estimator_type=analysis.estimator_type,
        treatment_col=analysis.treatment_col,
        outcome_col=analysis.outcome_col,
        feature_cols=analysis.feature_cols,
        status=analysis.status,
        started_at=analysis.started_at,
        completed_at=analysis.completed_at,
        results=analysis.results,
        error_message=analysis.error_message
    )


@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an analysis
    """
    success = AnalysisService.delete_analysis(db, analysis_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    return {
        "message": "Analysis deleted successfully",
        "analysis_id": analysis_id
    }
