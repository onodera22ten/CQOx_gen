"""
Decision Console API endpoints (Viz.pdf仕様準拠)
Global Growth Console - 世界レベルの意思決定コンソール

仕様:
- Viz.pdf完全準拠
- 既存 Decision Console / Portfolio / Digital Twin には読み取り専用で指標追加表示のみ
- 本ページは独立した高度な意思決定コンソール
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from collections import defaultdict

from cqox.auth.dependencies import get_current_user
from cqox.database.connection import get_db
from cqox.database.models import AnalysisRun, Segment
from cqox.api.models.console import (
    GlobalSummary,
    DeltaTrendPoint,
    SegmentBubble,
    ChannelPoint,
    DecisionCard,
    DecisionConsoleSummary
)
from cqox.api.services.console_metrics import (
    compute_cvar,
    assign_bcg_quadrant,
    compute_bcg_thresholds,
    compute_iso_week,
    resolve_date_range
)

router = APIRouter()


@router.get("/summary", response_model=DecisionConsoleSummary)
async def get_console_summary(
    window: str = Query("28d", regex="^(14d|28d|56d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    GET /api/v1/console/summary

    Viz.pdf仕様: Global Growth Console summary

    Args:
        window: "14d", "28d", or "56d"
        db: Database session
        current_user: Authenticated user

    Returns:
        DecisionConsoleSummary with KPIs, trend, segment portfolio, channel performance, and decision cards
    """
    try:
        from_date, to_date = resolve_date_range(window)

        # ==================== Query analysis_runs (completed, with policy_id) ====================
        query = text("""
            SELECT
                a.id,
                a.policy_id,
                a.delta_yen,
                a.delta_yen_ci_low,
                a.delta_yen_ci_high,
                a.roi,
                a.cas,
                a.risk,
                a.channel,
                a.segment_label,
                a.budget,
                a.reach_users,
                a.period_start,
                a.period_end,
                a.verdict,
                a.completed_at,
                p.name as policy_name,
                d.name as dataset_name
            FROM analysis_runs a
            LEFT JOIN policies p ON a.policy_id = p.id AND a.tenant_id = p.tenant_id
            LEFT JOIN datasets d ON a.dataset_id = d.id AND a.tenant_id = d.tenant_id
            WHERE a.tenant_id = :tenant_id
            AND a.status = 'completed'
            AND a.delta_yen IS NOT NULL
            AND a.policy_id IS NOT NULL
            AND a.completed_at >= :from_date
            AND a.completed_at <= :to_date
            ORDER BY a.completed_at DESC
        """)

        result = await db.execute(
            query,
            {"tenant_id": str(current_user["tenant_id"]), "from_date": from_date, "to_date": to_date}
        )
        rows = result.fetchall()

        if not rows:
            # Empty state: 正常なレスポンスを返す（Viz.pdf仕様）
            return DecisionConsoleSummary(
                window={"start": from_date.isoformat(), "end": to_date.isoformat()},
                kpis=GlobalSummary(
                    total_delta_yen=0.0,
                    avg_delta_yen_per_policy=0.0,
                    mean_cas=0.0,
                    cvar_worst10=0.0,
                    budget_used=0.0
                ),
                trend=[],
                segment_portfolio=[],
                channel_performance=[],
                decision_cards=[]
            )

        # ==================== Compute KPIs ====================
        delta_values = [float(row.delta_yen) for row in rows]
        cas_values = [float(row.cas) for row in rows if row.cas is not None]
        budget_values = [float(row.budget) for row in rows if row.budget is not None]

        total_delta_yen = sum(delta_values)
        avg_delta_yen = total_delta_yen / len(delta_values)
        mean_cas = sum(cas_values) / len(cas_values) if cas_values else 0.0
        cvar = compute_cvar(delta_values, alpha=0.1)
        budget_used = sum(budget_values)

        kpis = GlobalSummary(
            total_delta_yen=total_delta_yen,
            avg_delta_yen_per_policy=avg_delta_yen,
            mean_cas=mean_cas,
            cvar_worst10=cvar,
            budget_used=budget_used
        )

        # ==================== Compute Trend (weekly) ====================
        trend_map: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            "delta_yen": 0.0,
            "go_delta_yen": 0.0,
            "canary_delta_yen": 0.0,
            "hold_delta_yen": 0.0
        })

        for row in rows:
            if row.completed_at:
                week_label = compute_iso_week(row.completed_at)
                trend_map[week_label]["delta_yen"] += float(row.delta_yen)

                if row.verdict == "go":
                    trend_map[week_label]["go_delta_yen"] += float(row.delta_yen)
                elif row.verdict == "canary":
                    trend_map[week_label]["canary_delta_yen"] += float(row.delta_yen)
                elif row.verdict == "hold":
                    trend_map[week_label]["hold_delta_yen"] += float(row.delta_yen)

        trend = [
            DeltaTrendPoint(
                week_label=week,
                delta_yen=data["delta_yen"],
                go_delta_yen=data["go_delta_yen"],
                canary_delta_yen=data["canary_delta_yen"],
                hold_delta_yen=data["hold_delta_yen"]
            )
            for week, data in sorted(trend_map.items())
        ]

        # ==================== Query Segments ====================
        segments_query = select(Segment).where(Segment.tenant_id == current_user["tenant_id"])
        segments_result = await db.execute(segments_query)
        segments_rows = segments_result.scalars().all()

        # Aggregate delta_yen by segment
        segment_delta_map: Dict[str, List[float]] = defaultdict(list)
        segment_cas_map: Dict[str, List[float]] = defaultdict(list)

        for row in rows:
            if row.segment_label:
                segment_delta_map[row.segment_label].append(float(row.delta_yen))
                if row.cas is not None:
                    segment_cas_map[row.segment_label].append(float(row.cas))

        # Compute BCG thresholds
        segments_data = [
            {
                "incremental_clv": float(s.incremental_clv) if s.incremental_clv else 0.0,
                "user_count": int(s.user_count) if s.user_count else 0
            }
            for s in segments_rows
        ]
        clv_threshold, size_threshold = compute_bcg_thresholds(segments_data, percentile=0.7)

        # Build segment portfolio
        segment_portfolio = []
        for segment in segments_rows:
            total_delta_yen = sum(segment_delta_map.get(segment.name, []))
            cas_vals = segment_cas_map.get(segment.name, [])
            mean_cas = sum(cas_vals) / len(cas_vals) if cas_vals else 0.0

            bcg_quadrant = assign_bcg_quadrant(
                incremental_clv=float(segment.incremental_clv) if segment.incremental_clv else 0.0,
                user_count=int(segment.user_count) if segment.user_count else 0,
                clv_threshold=clv_threshold,
                size_threshold=size_threshold
            )

            segment_portfolio.append(SegmentBubble(
                segment_id=segment.segment_id,
                name=segment.name,
                incremental_clv=float(segment.incremental_clv) if segment.incremental_clv else 0.0,
                user_count=int(segment.user_count) if segment.user_count else 0,
                total_delta_yen=total_delta_yen,
                mean_cas=mean_cas,
                bcg_quadrant=bcg_quadrant
            ))

        # ==================== Channel Performance ====================
        channel_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "delta_values": [],
            "risk_values": [],
            "cas_values": []
        })

        for row in rows:
            if row.channel:
                channel_map[row.channel]["delta_values"].append(float(row.delta_yen))
                if row.risk is not None:
                    channel_map[row.channel]["risk_values"].append(float(row.risk))
                if row.cas is not None:
                    channel_map[row.channel]["cas_values"].append(float(row.cas))

        channel_performance = []
        for channel, data in channel_map.items():
            total_delta_yen = sum(data["delta_values"])
            risk = sum(data["risk_values"]) / len(data["risk_values"]) if data["risk_values"] else 0.0
            mean_cas = sum(data["cas_values"]) / len(data["cas_values"]) if data["cas_values"] else 0.0

            channel_performance.append(ChannelPoint(
                channel=channel,
                total_delta_yen=total_delta_yen,
                risk=risk,
                mean_cas=mean_cas
            ))

        # ==================== Decision Cards ====================
        decision_cards = [
            DecisionCard(
                policy_id=str(row.policy_id),
                policy_name=row.policy_name or "Unnamed Policy",
                dataset=row.dataset_name or "Unknown Dataset",
                channel=row.channel,
                segment_label=row.segment_label,
                delta_yen=float(row.delta_yen),
                roi=float(row.roi) if row.roi else 0.0,
                cas=float(row.cas) if row.cas else 0.0,
                risk=float(row.risk) if row.risk else 0.0,
                verdict=row.verdict or "hold",
                period_start=row.period_start or row.completed_at,
                period_end=row.period_end or row.completed_at
            )
            for row in rows
        ]

        return DecisionConsoleSummary(
            window={"start": from_date.isoformat(), "end": to_date.isoformat()},
            kpis=kpis,
            trend=trend,
            segment_portfolio=segment_portfolio,
            channel_performance=channel_performance,
            decision_cards=decision_cards
        )

    except Exception as e:
        logger.error(f"Error in get_console_summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
