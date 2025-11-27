"""
v1 Policies API Routes

ポリシー管理（作成、一覧、詳細、実行）
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from typing import Optional, List
from uuid import uuid4
from datetime import datetime
import logging
import uuid as uuid_lib

from cqox.models.v1 import PolicyConfig
from cqox.database.connection import get_db
from cqox.auth.dependencies import get_current_user
from cqox.database.models import Policy
from cqox.config import settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/policies", tags=["v1-policies"])
DEFAULT_TENANT_ID = uuid_lib.UUID("00000000-0000-0000-0000-000000000001")
DEFAULT_POLICY_NAMES = [
    "Email Campaign A",
    "Multi-Channel B",
    "Retention Offer C"
]


async def _seed_default_policies(db: AsyncSession, tenant_uuid: uuid_lib.UUID) -> None:
    """DBが空の場合にデフォルトポリシーを自動投入する"""
    if not getattr(settings, "auto_seed_demo_policies", False):
        logger.info("auto_seed_demo_policies is disabled; skipping seeding.")
        return
    from cqox.database.models import Dataset

    dataset_result = await db.execute(
        select(Dataset).where(Dataset.tenant_id == tenant_uuid).order_by(desc(Dataset.created_at))
    )
    dataset = dataset_result.scalars().first()
    if not dataset:
        logger.warning("No datasets available. Skipping default policy seeding.")
        return

    now = datetime.utcnow()
    default_specs = [
        {
            "name": "Email Campaign A",
            "description": "High-value customers via personalised email",
            "channels": ["Email"],
            "frequency_cap": 3,
            "budget_limit": 500_000,
            "status": "draft",
            "objectives": {"primary": "incremental_profit", "type": "email_push"},
            "risk_constraints": {"max_cpi": 800}
        },
        {
            "name": "Multi-Channel B",
            "description": "Push + SMS for propensity > 0.6",
            "channels": ["Push", "SMS"],
            "frequency_cap": 2,
            "budget_limit": 800_000,
            "status": "draft",
            "objectives": {"primary": "conversion_rate", "type": "multi_channel"},
            "risk_constraints": {"max_hold_rate": 0.1}
        },
        {
            "name": "Retention Offer C",
            "description": "Coupon offer for churn-risk users",
            "channels": ["In-App", "LINE"],
            "frequency_cap": 1,
            "budget_limit": 1_200_000,
            "status": "draft",
            "objectives": {"primary": "ltv", "type": "retention"},
            "risk_constraints": {"max_discount_rate": 0.2}
        }
    ]

    for spec in default_specs:
        policy = Policy(
            id=str(uuid4()),
            name=spec["name"],
            description=spec["description"],
            dataset_id=dataset.id,
            target_rule="propensity_score >= 0.5",
            offer_config={"type": "coupon", "value": 1000},
            channels=spec["channels"],
            frequency_cap=spec["frequency_cap"],
            budget_limit=spec["budget_limit"],
            objectives=spec["objectives"],
            risk_constraints=spec["risk_constraints"],
            status=spec["status"],
            tenant_id=tenant_uuid,
            created_at=now,
            updated_at=now
        )
        db.add(policy)

    await db.commit()
    logger.info("Seeded default policies for tenant %s", tenant_uuid)


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
    tenant_id_raw = current_user.get("tenant_id")
    if tenant_id_raw is None:
        tenant_uuid = DEFAULT_TENANT_ID
    elif isinstance(tenant_id_raw, uuid_lib.UUID):
        tenant_uuid = tenant_id_raw
    else:
        tenant_uuid = uuid_lib.UUID(str(tenant_id_raw))
    
    filters = [Policy.tenant_id == tenant_uuid]
    if status:
        filters.append(Policy.status == status)
    
    if not getattr(settings, "auto_seed_demo_policies", False):
        placeholders = ", ".join([f":name_{idx}" for idx in range(len(DEFAULT_POLICY_NAMES))])
        params = {f"name_{idx}": name for idx, name in enumerate(DEFAULT_POLICY_NAMES)}
        params["tenant_id"] = tenant_uuid
        await db.execute(
            text(f"DELETE FROM policies WHERE tenant_id = :tenant_id AND name IN ({placeholders})"),
            params
        )
        await db.commit()

    count_stmt = select(func.count()).select_from(Policy).where(*filters)
    total_count = (await db.execute(count_stmt)).scalar() or 0
    
    if total_count == 0:
        return {
            "policies": [],
            "count": 0,
            "page": page,
            "page_size": page_size
        }
    
    offset = (page - 1) * page_size
    data_stmt = (
        select(Policy)
        .where(*filters)
        .order_by(desc(Policy.created_at))
        .offset(offset)
        .limit(page_size)
    )
    
    result = await db.execute(data_stmt)
    policy_rows = result.scalars().all()
    
    policies = []
    for policy in policy_rows:
        objectives = policy.objectives or {}
        if isinstance(objectives, str):
            try:
                import json
                objectives = json.loads(objectives)
            except Exception:
                objectives = {}
        policies.append({
            "id": str(policy.id),
            "name": policy.name,
            "description": policy.description,
            "policy_type": objectives.get("type") or objectives.get("policy_type") or "custom",
            "objective": objectives.get("primary") or objectives.get("goal") or "",
            "status": policy.status,
            "created_at": policy.created_at.isoformat() if policy.created_at else None,
            "updated_at": policy.updated_at.isoformat() if policy.updated_at else None
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
