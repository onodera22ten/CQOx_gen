"""
v1 Results API Routes

DecisionCard（Δ¥ + Go/Canary/Hold判定）の取得・一覧表示
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc
from typing import Optional, Literal
from uuid import UUID, uuid4
import logging

from cqox.models.v1 import (
    DecisionCard,
    DecisionCardListResponse,
    DecisionCardList,
    DecisionCardCreate
)
from cqox.database.connection import get_db
from cqox.auth.dependencies import get_current_user


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/results", tags=["v1-results"])

@router.post("", response_model=DecisionCard, status_code=201)
async def create_decision_card(
    request: DecisionCardCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    DecisionCard作成

    因果推論実行後に、Δ¥とverdict（Go/Canary/Hold）を保存
    """
    from cqox.database.models import Decision

    # DecisionCardを作成
    decision = Decision(
        id=str(uuid4()),
        policy_id=str(UUID(request.policy_id)),
        scenario_id=str(UUID(request.scenario_id)) if request.scenario_id else None,
        scenario_name=request.scenario_name,
        delta_yen=request.delta_yen,
        delta_yen_ci_low=request.delta_yen_ci_low,
        delta_yen_ci_high=request.delta_yen_ci_high,
        delta_yen_std=request.delta_yen_std,
        verdict=request.verdict,
        reason=request.reason,
        channel=request.channel,
        segment=request.segment,
        quality_scores=request.quality_scores.dict() if request.quality_scores else None,
        scenario_spec=request.scenario_spec.dict(),
        estimator_results=request.estimator_results.dict(),
        tenant_id=current_user.get("tenant_id", "default_tenant")
    )

    db.add(decision)
    await db.commit()
    await db.refresh(decision)

    logger.info(f"DecisionCard created: {decision.id} (verdict={decision.verdict}, Δ¥={decision.delta_yen})")

    return DecisionCard.from_orm(decision)


@router.get("", response_model=DecisionCardList)
async def list_decision_cards(
    sort_by: Literal["delta_yen", "created_at"] = Query("delta_yen", description="ソート項目"),
    order: Literal["asc", "desc"] = Query("desc", description="ソート順"),
    verdict: Optional[Literal["Go", "Canary", "Hold"]] = Query(None, description="判定フィルタ"),
    channel: Optional[str] = Query(None, description="チャネルフィルタ"),
    segment: Optional[str] = Query(None, description="セグメントフィルタ"),
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(10, ge=1, le=100, description="ページサイズ"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    DecisionCard一覧取得

    **デフォルト**: Δ¥ランキング順（降順）
    **フィルタ**: verdict（Go/Canary/Hold）、channel、segment
    """
    from cqox.database.models import Decision

    # クエリ構築
    tenant_id = current_user.get("tenant_id", "default_tenant")
    query = select(Decision).where(Decision.tenant_id == tenant_id)

    # フィルタ適用
    if verdict:
        query = query.where(Decision.verdict == verdict)
    if channel:
        query = query.where(Decision.channel == channel)
    if segment:
        query = query.where(Decision.segment == segment)

    # ソート適用
    sort_column = Decision.delta_yen if sort_by == "delta_yen" else Decision.created_at
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # ページネーション
    total_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.limit(page_size).offset(offset)

    # 実行
    result = await db.execute(query)
    decisions = result.scalars().all()

    items = [DecisionCard.from_orm(d) for d in decisions]

    return DecisionCardList(
        total=total,
        items=items,
        page=page,
        page_size=page_size
    )


@router.get("/{decision_id}", response_model=DecisionCard)
async def get_decision_card(
    decision_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    DecisionCard詳細取得
    """
    from cqox.database.models import Decision

    query = select(Decision).where(
        Decision.id == UUID(decision_id),
        Decision.tenant_id == current_user.get("tenant_id", "default_tenant")
    )

    result = await db.execute(query)
    decision = result.scalar_one_or_none()

    if not decision:
        raise HTTPException(status_code=404, detail="DecisionCard not found")

    return DecisionCard.from_orm(decision)


@router.delete("/{decision_id}", status_code=204)
async def delete_decision_card(
    decision_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    DecisionCard削除

    **権限**: Admin または作成者のみ
    """
    from cqox.database.models import Decision

    query = select(Decision).where(
        Decision.id == UUID(decision_id),
        Decision.tenant_id == current_user.get("tenant_id", "default_tenant")
    )

    result = await db.execute(query)
    decision = result.scalar_one_or_none()

    if not decision:
        raise HTTPException(status_code=404, detail="DecisionCard not found")

    await db.delete(decision)
    await db.commit()

    logger.info(f"DecisionCard deleted: {decision_id}")

    return None
