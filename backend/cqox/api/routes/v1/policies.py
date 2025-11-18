"""
v1 Policies API Routes

ポリシー管理（作成、一覧、詳細、実行）
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List
from uuid import uuid4
from datetime import datetime
import logging

from cqox.models.v1 import PolicyConfig
from cqox.database.connection import get_db
from cqox.auth.dependencies import get_current_user


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/policies", tags=["v1-policies"])


@router.post("", response_model=PolicyConfig, status_code=201)
async def create_policy(
    request: PolicyConfig,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    ポリシー作成
    
    **ScenarioSpec**:
    - S0: 現行施策（baseline）
    - S1: 候補施策
    
    **Policy定義**:
    - Target rule（対象ルール）
    - Offer config（オファー設定）
    - Channels（チャネル）
    - Budget limit（予算制約）
    """
    from cqox.database.models import Policy
    
    policy_id = str(uuid4())
    
    policy = Policy(
        id=policy_id,
        name=request.name,
        description=request.description,
        dataset_id=request.dataset_id,
        target_rule=request.target_rule,
        offer_config=request.offer_config,
        channels=request.channels,
        frequency_cap=request.frequency_cap,
        budget_limit=request.budget_limit,
        objectives=request.objectives,
        risk_constraints=request.risk_constraints,
        status="draft",
        tenant_id=current_user.get("tenant_id", "default_tenant"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    
    logger.info(f"Policy created: {policy_id} (name={request.name})")
    
    return PolicyConfig.from_orm(policy)


@router.get("")
async def list_policies(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """ポリシー一覧取得（実データ）"""
    from sqlalchemy import text, func
    import uuid as uuid_lib
    
    tenant_id = uuid_lib.UUID("00000000-0000-0000-0000-000000000001")
    
    # Count query
    count_query = text("SELECT COUNT(*) FROM policies WHERE tenant_id = :tenant_id")
    if status:
        count_query = text(f"SELECT COUNT(*) FROM policies WHERE tenant_id = :tenant_id AND status = :status")
    
    count_result = await db.execute(
        count_query,
        {"tenant_id": tenant_id, "status": status} if status else {"tenant_id": tenant_id}
    )
    total_count = count_result.scalar()
    
    # Data query
    offset = (page - 1) * page_size
    data_query = text("""
        SELECT id, name, description, policy_type, objective, status, created_at, updated_at
        FROM policies
        WHERE tenant_id = :tenant_id
    """ + (f" AND status = :status" if status else "") + """
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    
    result = await db.execute(
        data_query,
        {
            "tenant_id": tenant_id,
            "status": status,
            "limit": page_size,
            "offset": offset
        } if status else {
            "tenant_id": tenant_id,
            "limit": page_size,
            "offset": offset
        }
    )
    
    policies = []
    for row in result:
        policies.append({
            "id": str(row[0]),
            "name": row[1],
            "description": row[2],
            "policy_type": row[3],
            "objective": row[4],
            "status": row[5],
            "created_at": row[6].isoformat() if row[6] else None,
            "updated_at": row[7].isoformat() if row[7] else None
        })
    
    logger.info(f"Listed {len(policies)} policies (total: {total_count})")
    
    return {
        "policies": policies,
        "count": total_count,
        "page": page,
        "page_size": page_size
    }


@router.get("/{policy_id}", response_model=PolicyConfig)
async def get_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """ポリシー詳細取得"""
    from cqox.database.models import Policy
    
    result = await db.execute(
        select(Policy).where(
            Policy.id == policy_id,
            Policy.tenant_id == current_user.get("tenant_id", "default_tenant")
        )
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return PolicyConfig.from_orm(policy)


@router.post("/{policy_id}/run", status_code=202)
async def run_policy_analysis(
    policy_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    ポリシー分析実行（因果推論）
    
    **手順**:
    1. PolicyとDatasetを読み込み
    2. 因果推論推定器を実行（DR, IPW, DiD等）
    3. Δ¥計算
    4. DecisionCard生成（Go/Canary/Hold判定）
    
    **非同期実行**: Celeryタスクとして実行
    """
    from cqox.database.models import Policy
    
    result = await db.execute(
        select(Policy).where(
            Policy.id == policy_id,
            Policy.tenant_id == current_user.get("tenant_id", "default_tenant")
        )
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Celeryタスク起動（TODO: 実装）
    # from cqox.tasks.causal_tasks import run_causal_analysis
    # task = run_causal_analysis.delay(policy_id=policy_id, dataset_id=policy.dataset_id)
    
    # ステータス更新
    policy.status = "running"
    policy.updated_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"Policy analysis started: {policy_id}")
    
    return {
        "policy_id": policy_id,
        "status": "running",
        "task_id": "mock-task-id-123",  # task.id
        "message": "Analysis started. Check /api/v1/results for completion."
    }


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """ポリシー削除"""
    from cqox.database.models import Policy
    
    result = await db.execute(
        select(Policy).where(
            Policy.id == policy_id,
            Policy.tenant_id == current_user.get("tenant_id", "default_tenant")
        )
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    await db.delete(policy)
    await db.commit()
    
    logger.info(f"Policy deleted: {policy_id}")
    return None

