"""
Pydantic models for Analysis API
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class AnalysisBase(BaseModel):
    """Base analysis model"""
    dataset_id: int = Field(..., description="Dataset ID")
    estimator_type: str = Field(..., description="Estimator type (DR, IPW, etc.)")
    treatment_col: str = Field(..., description="Treatment column name")
    outcome_col: str = Field(..., description="Outcome column name")
    feature_cols: List[str] = Field(..., description="Feature column names")


class AnalysisCreate(AnalysisBase):
    """Analysis creation request"""
    estimators: List[str] = Field(default=['DR'], description="List of estimators to run")
    policy_id: Optional[str] = None
    scenario_spec: Optional[Dict[str, Any]] = None
    bootstrap_iterations: int = Field(default=100, description="Bootstrap iterations")
    confidence_level: float = Field(default=0.95, description="Confidence level")


class AnalysisResponse(BaseModel):
    """Analysis response model"""
    id: int = Field(alias="analysis_id")
    dataset_id: int
    user_id: int
    estimator_type: str
    treatment_col: str
    outcome_col: str
    feature_cols: List[str]
    status: Literal['pending', 'running', 'completed', 'failed']
    started_at: datetime
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    # Derived fields from results
    delta_yen: Optional[float] = None
    delta_yen_ci_low: Optional[float] = None
    delta_yen_ci_high: Optional[float] = None
    verdict: Optional[Literal['Go', 'Canary', 'Hold']] = None
    progress: int = 0

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

    def __init__(self, **data):
        """Custom init to populate derived fields"""
        super().__init__(**data)

        # Extract derived fields from results
        if self.results:
            self.delta_yen = self.results.get('ate')
            self.delta_yen_ci_low = self.results.get('ci_low')
            self.delta_yen_ci_high = self.results.get('ci_high')
            self.verdict = self.results.get('verdict')

        # Calculate progress
        if self.status == 'completed':
            self.progress = 100
        elif self.status == 'running':
            self.progress = 50
        elif self.status == 'failed':
            self.progress = 0
        else:
            self.progress = 0


class AnalysisRunRequest(BaseModel):
    """Request to run causal analysis"""
    dataset_id: str
    policy_id: Optional[str] = None
    estimators: List[str] = Field(default=['DR'], description="Estimators to use")
    treatment_col: str
    outcome_col: str
    feature_cols: List[str]
    scenario_spec: Optional[Dict[str, Any]] = None
    bootstrap_iterations: int = 100
    confidence_level: float = 0.95
