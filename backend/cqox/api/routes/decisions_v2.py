"""
Decision API endpoints (v2) with authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from cqox.db.database import get_db
from cqox.db.models import User
from cqox.api.dependencies.auth import get_current_active_user
from cqox.models.decision import (
    DecisionResponse,
    DecisionCreate,
    DecisionUpdate,
    DecisionSummary
)
from cqox.services.decision_service import DecisionService

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.post("/", response_model=DecisionResponse)
async def create_decision(
    request: DecisionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a decision from a completed analysis
    """
    try:
        decision = DecisionService.create_decision_from_analysis(
            db=db,
            analysis_id=request.analysis_id,
            user_id=current_user.id,
            policy_name=request.policy_name
        )
        return decision

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[DecisionResponse])
async def list_decisions(
    skip: int = 0,
    limit: int = 100,
    verdict: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all decisions for the current user with optional filters
    """
    # Parse dates if provided
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    decisions = DecisionService.get_decisions_by_user(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        verdict=verdict,
        start_date=start_dt,
        end_date=end_dt
    )
    return decisions


@router.get("/summary", response_model=DecisionSummary)
async def get_decision_summary(
    days: int = Query(7, description="Number of days to include in summary"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for decisions over the past N days
    """
    summary = DecisionService.get_decision_summary(db, current_user.id, days)
    return summary


@router.get("/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    decision_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get decision details by ID
    """
    decision = DecisionService.get_decision_by_id(db, decision_id, current_user.id)
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found"
        )
    return decision


@router.put("/{decision_id}", response_model=DecisionResponse)
async def update_decision(
    decision_id: int,
    update_data: DecisionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a decision
    """
    try:
        decision = DecisionService.update_decision(
            db=db,
            decision_id=decision_id,
            user_id=current_user.id,
            verdict=update_data.verdict,
            policy_name=update_data.policy_name
        )
        return decision

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{decision_id}")
async def delete_decision(
    decision_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a decision
    """
    success = DecisionService.delete_decision(db, decision_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found"
        )

    return {
        "message": "Decision deleted successfully",
        "decision_id": decision_id
    }
