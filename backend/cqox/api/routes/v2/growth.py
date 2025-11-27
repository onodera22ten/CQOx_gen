"""V2 Module C API - Growth & LTV Planning"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from pydantic import BaseModel
import pandas as pd

from cqox.auth.dependencies import get_current_user
from cqox.database.connection import get_db
from cqox.database.models import User
from cqox.engine.ltv.ltv_estimator import SimpleCLVEstimator

router = APIRouter()


class CLVRequest(BaseModel):
    discount_rate: float = 0.01
    data: List[Dict[str, Any]]  # [{"user_id": "u1", "t": 1, "revenue": 100, "treated": true}, ...]


class CLVResponse(BaseModel):
    clv_treated: float
    clv_control: float
    delta_clv: float


@router.post("/clv", response_model=CLVResponse)
async def calculate_clv(
    request: CLVRequest,
    current_user: User = Depends(get_current_user)
):
    """Calculate CLV with Survival + Discounting"""
    df = pd.DataFrame(request.data)

    estimator = SimpleCLVEstimator(discount_rate=request.discount_rate)
    estimator.fit(df)

    clv_t = estimator.clv(treated=True)
    clv_c = estimator.clv(treated=False)
    delta = clv_t - clv_c

    return CLVResponse(
        clv_treated=clv_t,
        clv_control=clv_c,
        delta_clv=delta
    )


@router.post("/cohorts")
async def cohort_analysis(
    request: CLVRequest,
    cohort_column: str = "cohort",
    current_user: User = Depends(get_current_user)
):
    """Cohort-level CLV analysis"""
    df = pd.DataFrame(request.data)

    estimator = SimpleCLVEstimator(discount_rate=request.discount_rate)
    estimator.fit(df)

    cohort_df = estimator.cohort_analysis(cohort_column)

    return {"cohorts": cohort_df.to_dict(orient='records')}


@router.post("/retention")
async def retention_curve(
    request: CLVRequest,
    treated: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Get retention curve"""
    df = pd.DataFrame(request.data)

    estimator = SimpleCLVEstimator(discount_rate=request.discount_rate)
    estimator.fit(df)

    retention_df = estimator.retention_curve(treated=treated)

    return {"retention": retention_df.to_dict(orient='records')}
