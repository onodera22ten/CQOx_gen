"""
v1 Console API Routes

Decision Console用のサマリーAPI（Δ¥ランキング、判定内訳等）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal
import logging

from cqox.api.models.v1.decision_card import (
    DeltaYenSummary,
    DeltaYenHistoryItem,
    VerdictDistribution,
    DecisionCard
)
from cqox.database.connection import get_db
from cqox.auth.dependencies import get_current_user


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/console", tags=["v1-console"])


@router.get("/delta-yen-summary", response_model=DeltaYenSummary)
async def get_delta_yen_summary(
    period_days: int = Query(7, ge=1, le=365, description="集計期間（日数）"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Δ¥サマリー取得（Decision Console用）

    **内容**:
    - 総Decision数
    - Go/Canary/Hold判定数
    - 平均Δ¥、最大Δ¥、最小Δ¥
    - ベストシナリオ（最大Δ¥のDecisionCard）
    """
    from cqox.database.models import Decision

    # 期間フィルタ
    since = datetime.utcnow() - timedelta(days=period_days)

    # 集計クエリ
    query = select(
        func.count(Decision.id).label("total_decisions"),
        func.count().filter(Decision.verdict == "Go").label("go_count"),
        func.count().filter(Decision.verdict == "Canary").label("canary_count"),
        func.count().filter(Decision.verdict == "Hold").label("hold_count"),
        func.avg(Decision.delta_yen).label("avg_delta_yen"),
        func.max(Decision.delta_yen).label("best_delta_yen"),
        func.min(Decision.delta_yen).label("worst_delta_yen")
    ).where(
        Decision.tenant_id == current_user.get("tenant_id", "default_tenant"),
        Decision.created_at >= since
    )

    result = await db.execute(query)
    row = result.one()

    # ベストシナリオ取得
    best_query = select(Decision).where(
        Decision.tenant_id == current_user.get("tenant_id", "default_tenant"),
        Decision.created_at >= since
    ).order_by(desc(Decision.delta_yen)).limit(1)

    best_result = await db.execute(best_query)
    best_decision = best_result.scalar_one_or_none()

    return DeltaYenSummary(
        total_decisions=row.total_decisions or 0,
        go_count=row.go_count or 0,
        canary_count=row.canary_count or 0,
        hold_count=row.hold_count or 0,
        avg_delta_yen=Decimal(row.avg_delta_yen or 0),
        best_delta_yen=Decimal(row.best_delta_yen or 0),
        worst_delta_yen=Decimal(row.worst_delta_yen or 0),
        best_scenario=DecisionCard.from_orm(best_decision) if best_decision else None
    )


@router.get("/delta-yen-history", response_model=list[DeltaYenHistoryItem])
async def get_delta_yen_history(
    period: Literal["week", "month"] = Query("week", description="集計期間単位"),
    weeks: int = Query(6, ge=1, le=52, description="週数（週単位の場合）"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Δ¥履歴取得（週次）

    **用途**: Decision Console の棒グラフ表示
    """
    from cqox.database.models import Decision

    # 週次集計（簡易実装: 7日ごと）
    history = []
    now = datetime.utcnow()

    for i in range(weeks):
        week_end = now - timedelta(days=i * 7)
        week_start = week_end - timedelta(days=7)

        query = select(
            func.avg(Decision.delta_yen).label("avg_delta_yen"),
            func.count(Decision.id).label("decision_count")
        ).where(
            Decision.tenant_id == current_user.get("tenant_id", "default_tenant"),
            Decision.created_at >= week_start,
            Decision.created_at < week_end
        )

        result = await db.execute(query)
        row = result.one()

        week_label = f"W{weeks - i}"
        history.append(DeltaYenHistoryItem(
            week=week_label,
            delta_yen=Decimal(row.avg_delta_yen or 0),
            decision_count=row.decision_count or 0
        ))

    # 古い順に並び替え
    history.reverse()

    return history


@router.get("/verdict-distribution", response_model=VerdictDistribution)
async def get_verdict_distribution(
    period_days: int = Query(7, ge=1, le=365, description="集計期間（日数）"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    判定内訳取得（Go/Canary/Hold）

    **用途**: Decision Console の円グラフ表示
    """
    from cqox.database.models import Decision

    since = datetime.utcnow() - timedelta(days=period_days)

    query = select(
        func.count().filter(Decision.verdict == "Go").label("go"),
        func.count().filter(Decision.verdict == "Canary").label("canary"),
        func.count().filter(Decision.verdict == "Hold").label("hold"),
        func.count(Decision.id).label("total")
    ).where(
        Decision.tenant_id == current_user.get("tenant_id", "default_tenant"),
        Decision.created_at >= since
    )

    result = await db.execute(query)
    row = result.one()

    return VerdictDistribution(
        go=row.go or 0,
        canary=row.canary or 0,
        hold=row.hold or 0,
        total=row.total or 0
    )
