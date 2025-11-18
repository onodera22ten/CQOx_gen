"""
v1 Analysis API Routes

因果推論分析実行とモニタリング
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, List, Literal
import uuid as uuid_lib
from datetime import datetime
import logging
from pydantic import BaseModel, Field

from cqox.database.connection import get_db
from cqox.auth.dependencies import get_current_user


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analysis", tags=["v1-analysis"])

DEFAULT_TENANT_ID = uuid_lib.UUID("00000000-0000-0000-0000-000000000001")


def _parse_uuid(value: str, field: str) -> uuid_lib.UUID:
    try:
        return uuid_lib.UUID(value)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid {field} UUID")


# Request/Response Models
class AnalysisRequest(BaseModel):
    """因果推論分析リクエスト"""
    dataset_id: str = Field(..., description="Dataset ID")
    policy_id: str = Field(..., description="Policy ID")
    
    # Estimator selection
    estimators: List[Literal["DR", "IPW", "DiD", "IV", "CF", "SCM", "RD"]] = Field(
        ["DR", "IPW"],
        description="使用する推定器"
    )
    
    # Treatment/Outcome specification
    treatment_col: str = Field(..., description="Treatment column name")
    outcome_col: str = Field(..., description="Outcome column name")
    feature_cols: List[str] = Field(..., description="Feature columns")
    
    # Scenario comparison
    scenario_spec: dict = Field(..., description="S0 vs S1 scenario definition")
    
    # Options
    bootstrap_iterations: int = Field(1000, ge=100, le=10000)
    confidence_level: float = Field(0.95, ge=0.8, le=0.99)


class AnalysisStatus(BaseModel):
    """分析ステータス"""
    analysis_id: str
    policy_id: str
    dataset_id: str
    status: Literal["pending", "running", "completed", "failed"]
    progress: float = Field(0.0, ge=0, le=1, description="Progress (0-1)")
    
    # Results (if completed)
    delta_yen: Optional[float] = None
    delta_yen_ci_low: Optional[float] = None
    delta_yen_ci_high: Optional[float] = None
    verdict: Optional[Literal["Go", "Canary", "Hold"]] = None
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Error (if failed)
    error_message: Optional[str] = None


@router.post("/run", response_model=AnalysisStatus, status_code=202)
async def start_analysis(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    因果推論分析を開始
    
    **処理フロー**:
    1. Dataset読み込み
    2. 各推定器（DR/IPW/DiD等）で因果効果推定
    3. Bootstrap CI計算
    4. Δ¥計算（Money View）
    5. Go/Canary/Hold判定
    6. DecisionCard生成
    
    **非同期実行**: Celeryタスクで実行
    """
    from cqox.database.models import AnalysisRun
    
    analysis_uuid = uuid_lib.uuid4()
    policy_uuid = _parse_uuid(request.policy_id, "policy_id")
    dataset_uuid = _parse_uuid(request.dataset_id, "dataset_id")
    
    # Get tenant_id from current_user or use default
    tenant_id_raw = current_user.get("tenant_id", None)
    if tenant_id_raw is None:
        tenant_uuid = DEFAULT_TENANT_ID
    elif isinstance(tenant_id_raw, uuid_lib.UUID):
        tenant_uuid = tenant_id_raw
    else:
        tenant_uuid = _parse_uuid(str(tenant_id_raw), "tenant_id")
    
    # AnalysisRun作成
    analysis_run = AnalysisRun(
        id=analysis_uuid,
        policy_id=policy_uuid,
        dataset_id=dataset_uuid,
        estimators=request.estimators,
        treatment_col=request.treatment_col,
        outcome_col=request.outcome_col,
        feature_cols=request.feature_cols,
        scenario_spec=request.scenario_spec,
        status="pending",
        progress=0.0,
        tenant_id=tenant_uuid,
        started_at=datetime.utcnow()
    )
    
    db.add(analysis_run)
    await db.commit()
    await db.refresh(analysis_run)
    
    # Get dataset file path
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT file_path FROM datasets WHERE id = :dataset_id"),
        {"dataset_id": dataset_uuid}
    )
    dataset_row = result.fetchone()
    
    if not dataset_row:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    dataset_path = dataset_row[0]
    
    # Celeryタスク起動
    from cqox.tasks.analysis_tasks import run_causal_analysis
    
    # Map estimator names (DR → dr_learner, etc.)
    estimator_map = {
        'DR': 'dr_learner',
        'IPW': 'dr_learner',  # IPW is part of DR-Learner
        'DiD': 'did',          # ✅ Fully integrated
        'IV': 'iv',            # ✅ Fully integrated
        'CF': 'causal_forest',
        'SCM': 'scm',          # ✅ Fully integrated
        'RD': 'rd'             # ✅ Fully integrated
    }
    mapped_estimators = [estimator_map.get(e, 's_learner') for e in request.estimators]
    
    task = run_causal_analysis.delay(
        analysis_id=str(analysis_uuid),
        dataset_path=dataset_path,
        treatment_col=request.treatment_col,
        outcome_col=request.outcome_col,
        feature_cols=request.feature_cols,
        estimators=mapped_estimators
    )
    
    logger.info(f"Analysis started: {analysis_uuid} (policy={policy_uuid}, task_id={task.id})")
    
    return AnalysisStatus(
        analysis_id=str(analysis_uuid),
        policy_id=str(policy_uuid),
        dataset_id=str(dataset_uuid),
        status="pending",
        progress=0.0,
        started_at=datetime.utcnow()
    )


@router.get("/{analysis_id}", response_model=AnalysisStatus)
async def get_analysis_status(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """分析ステータス取得"""
    from cqox.database.models import AnalysisRun
    
    # Get tenant_id from current_user or use default
    tenant_id_raw = current_user.get("tenant_id", None)
    if tenant_id_raw is None:
        tenant_uuid = DEFAULT_TENANT_ID
    elif isinstance(tenant_id_raw, uuid_lib.UUID):
        tenant_uuid = tenant_id_raw
    else:
        tenant_uuid = _parse_uuid(str(tenant_id_raw), "tenant_id")
    
    analysis_uuid = _parse_uuid(analysis_id, "analysis_id")
    
    result = await db.execute(
        select(AnalysisRun).where(
            AnalysisRun.id == analysis_uuid,
            AnalysisRun.tenant_id == tenant_uuid
        )
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return AnalysisStatus(
        analysis_id=str(analysis.id),
        policy_id=str(analysis.policy_id),
        dataset_id=str(analysis.dataset_id),
        status=analysis.status,
        progress=analysis.progress or 0.0,
        delta_yen=analysis.delta_yen,
        delta_yen_ci_low=analysis.delta_yen_ci_low,
        delta_yen_ci_high=analysis.delta_yen_ci_high,
        verdict=analysis.verdict,
        started_at=analysis.started_at,
        completed_at=analysis.completed_at,
        error_message=analysis.error_message
    )


@router.get("", response_model=List[AnalysisStatus])
async def list_analyses(
    status: Optional[str] = Query(None),
    policy_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """分析一覧取得"""
    from cqox.database.models import AnalysisRun
    
    # Get tenant_id from current_user or use default
    tenant_id_raw = current_user.get("tenant_id", None)
    if tenant_id_raw is None:
        tenant_uuid = DEFAULT_TENANT_ID
    elif isinstance(tenant_id_raw, uuid_lib.UUID):
        tenant_uuid = tenant_id_raw
    else:
        tenant_uuid = _parse_uuid(str(tenant_id_raw), "tenant_id")
    
    query = select(AnalysisRun).where(AnalysisRun.tenant_id == tenant_uuid)
    
    if status:
        query = query.where(AnalysisRun.status == status)
    if policy_id:
        query = query.where(AnalysisRun.policy_id == policy_id)
    
    offset = (page - 1) * page_size
    query = query.order_by(desc(AnalysisRun.started_at)).limit(page_size).offset(offset)
    
    result = await db.execute(query)
    analyses = result.scalars().all()
    
    return [
        AnalysisStatus(
            analysis_id=str(a.id),
            policy_id=str(a.policy_id),
            dataset_id=str(a.dataset_id),
            status=a.status,
            progress=a.progress or 0.0,
            delta_yen=a.delta_yen,
            delta_yen_ci_low=a.delta_yen_ci_low,
            delta_yen_ci_high=a.delta_yen_ci_high,
            verdict=a.verdict,
            started_at=a.started_at,
            completed_at=a.completed_at,
            error_message=a.error_message
        )
        for a in analyses
    ]


@router.delete("/{analysis_id}", status_code=204)
async def cancel_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    分析キャンセル（実行中のみ）
    """
    from cqox.database.models import AnalysisRun
    
    # Get tenant_id from current_user or use default
    tenant_id_raw = current_user.get("tenant_id", None)
    if tenant_id_raw is None:
        tenant_uuid = DEFAULT_TENANT_ID
    elif isinstance(tenant_id_raw, uuid_lib.UUID):
        tenant_uuid = tenant_id_raw
    else:
        tenant_uuid = _parse_uuid(str(tenant_id_raw), "tenant_id")
    
    analysis_uuid = _parse_uuid(analysis_id, "analysis_id")
    
    result = await db.execute(
        select(AnalysisRun).where(
            AnalysisRun.id == analysis_uuid,
            AnalysisRun.tenant_id == tenant_uuid
        )
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if analysis.status not in ["pending", "running"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed/failed analysis")
    
    # Celeryタスクキャンセル（TODO: 実装）
    # from celery import current_app
    # current_app.control.revoke(analysis.task_id, terminate=True)
    
    analysis.status = "cancelled"
    analysis.completed_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"Analysis cancelled: {analysis_id}")
    return None

