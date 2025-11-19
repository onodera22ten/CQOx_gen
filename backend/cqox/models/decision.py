"""
Pydantic models for Decision API
"""
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class DecisionBase(BaseModel):
    """Base decision model"""
    policy_name: str = Field(..., description="Policy name")
    verdict: Literal['Go', 'Canary', 'Hold'] = Field(..., description="Decision verdict")


class DecisionCreate(BaseModel):
    """Decision creation request"""
    analysis_id: int = Field(..., description="Analysis ID to create decision from")
    policy_name: Optional[str] = None


class DecisionUpdate(BaseModel):
    """Decision update request"""
    verdict: Optional[Literal['Go', 'Canary', 'Hold']] = None
    policy_name: Optional[str] = None


class DecisionResponse(BaseModel):
    """Decision response model"""
    id: int
    analysis_id: int
    user_id: int
    policy_name: str
    verdict: Literal['Go', 'Canary', 'Hold']
    delta_yen: Optional[float] = None
    confidence_interval_low: Optional[float] = None
    confidence_interval_high: Optional[float] = None
    cas_score: Optional[float] = None
    risk_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class DecisionSummary(BaseModel):
    """Summary statistics for decisions"""
    total_decisions: int
    go_count: int
    canary_count: int
    hold_count: int
    total_delta_yen: float
    go_delta_yen: float
    canary_delta_yen: float
    hold_delta_yen: float
    avg_cas_score: float
    avg_risk_score: float
    period_days: int
    start_date: str
