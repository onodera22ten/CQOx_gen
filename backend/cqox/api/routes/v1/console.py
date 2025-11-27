"""
v1 Console API Routes

Decision Console用のサマリーAPI (修正.pdf仕様準拠)
- Policy Lab由来のポリシーのみ使用
- PortfolioFlag.include == true のポリシーを集計
- window パラメータで期間指定 (14d/28d/56d)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal
from typing import Literal, Dict, Any
from collections import defaultdict
import math
import logging
import uuid as uuid_lib
from types import SimpleNamespace
from dataclasses import dataclass
import json

from cqox.models.v1 import DecisionCard
from pydantic import BaseModel, Field
from typing import List, Optional
from cqox.database.connection import get_db
from cqox.auth.dependencies import get_current_user
from cqox.database.models import AnalysisRun, Dataset, Decision, Policy
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import ProgrammingError


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/console", tags=["v1-console"])
decision_console_router = APIRouter(prefix="/api/v1/decision-console", tags=["decision-console"])

# デフォルトテナントID
DEFAULT_TENANT_ID = uuid_lib.UUID("00000000-0000-0000-0000-000000000001")


def _get_tenant_uuid(current_user: dict) -> uuid_lib.UUID:
    tenant_id_raw = current_user.get("tenant_id")
    if tenant_id_raw is None:
        return DEFAULT_TENANT_ID
    if isinstance(tenant_id_raw, uuid_lib.UUID):
        return tenant_id_raw
    try:
        return uuid_lib.UUID(str(tenant_id_raw))
    except ValueError:
        return DEFAULT_TENANT_ID


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ==================== 修正.pdf仕様準拠モデル ====================

class ConsoleSummaryKPIs(BaseModel):
    """KPIカード4つ"""
    total_delta_yen: float = 0.0
    avg_delta_yen: float = 0.0
    mean_cas: Optional[float] = None
    portfolio_cvar_10: float = 0.0  # CVaR (worst 10%)


class ConsoleTrendPoint(BaseModel):
    """Δ¥ Trend (週次集計)"""
    week: str  # ISO week format: "2025-W48"
    delta_yen: float


class ConsoleSegmentPortfolio(BaseModel):
    """Segment Portfolio (セグメント別ポートフォリオ)"""
    segment_label: str
    population: int
    total_delta_yen: float
    policy_count: int
    mean_cas: Optional[float] = None


class ConsoleChannelPerformance(BaseModel):
    """Channel Performance (チャネル別パフォーマンス)"""
    channel: str
    total_delta_yen: float
    roi: Optional[float] = None


class ConsoleDecisionCard(BaseModel):
    """Decision Card (個別施策)"""
    id: str
    policy_name: str
    dataset_name: str
    channel: Optional[str] = None
    segment: Optional[str] = None
    delta_yen: float
    roi: Optional[float] = None
    cas: Optional[float] = None
    risk: Optional[float] = None
    verdict: str
    decided_at: datetime


class DecisionConsoleSummaryResponse(BaseModel):
    """修正.pdf仕様準拠レスポンス - GET /api/v1/console/summary"""
    window: Dict[str, str]  # {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
    kpis: ConsoleSummaryKPIs
    trend: List[ConsoleTrendPoint]
    segment_portfolio: List[ConsoleSegmentPortfolio]
    channel_performance: List[ConsoleChannelPerformance]
    decision_cards: List[ConsoleDecisionCard]


# ==================== 修正.pdf仕様準拠エンドポイント ====================

@router.get("/summary", response_model=DecisionConsoleSummaryResponse)
async def get_console_summary(
    window: str = Query("28d", regex="^(14d|28d|56d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Decision Console Summary (修正.pdf仕様準拠)

    Policy Lab由来のポリシーのみを集計
    - PortfolioFlag.include == true のポリシー
    - または、分析完了済み (status == 'completed') のanalysis_runs

    パラメータ:
        window: 集計期間 (14d/28d/56d)

    レスポンス:
        - window: 期間情報
        - kpis: 4つのKPIカード (total_delta_yen, avg_delta_yen, mean_cas, portfolio_cvar_10)
        - trend: 週次Δ¥トレンド
        - segment_portfolio: セグメント別ポートフォリオ
        - channel_performance: チャネル別パフォーマンス
        - decision_cards: 個別施策リスト
    """
    tenant_uuid = _get_tenant_uuid(current_user)

    # Parse window period
    window_days = int(window.replace("d", ""))
    end_date = datetime.utcnow().replace(tzinfo=None)
    start_date = end_date - timedelta(days=window_days)

    logger.info(f"Console summary: tenant={tenant_uuid}, window={window}, period={start_date} to {end_date}")

    # Query completed analysis runs from Policy Lab
    # 修正.pdf: Policy Lab由来のポリシーのみ使用
    query = text("""
        SELECT
            a.id,
            a.policy_id,
            a.dataset_id,
            a.delta_yen,
            a.delta_yen_ci_low,
            a.delta_yen_ci_high,
            a.verdict,
            a.completed_at,
            a.scenario_spec,
            a.diagnostics_snapshot,
            a.impact_metrics,
            p.name as policy_name,
            p.channels,
            p.target_rule,
            d.name as dataset_name
        FROM analysis_runs a
        LEFT JOIN policies p ON a.policy_id = p.id AND a.tenant_id = p.tenant_id
        LEFT JOIN datasets d ON a.dataset_id = d.id AND a.tenant_id = d.tenant_id
        WHERE a.tenant_id = :tenant_id
        AND a.status = 'completed'
        AND a.delta_yen IS NOT NULL
        AND a.completed_at >= :start_date
        AND a.completed_at <= :end_date
        ORDER BY a.completed_at DESC
    """)

    result = await db.execute(query, {
        "tenant_id": tenant_uuid,
        "start_date": start_date,
        "end_date": end_date
    })
    rows = result.fetchall()

    if not rows:
        # Empty state
        return DecisionConsoleSummaryResponse(
            window={
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            },
            kpis=ConsoleSummaryKPIs(),
            trend=[],
            segment_portfolio=[],
            channel_performance=[],
            decision_cards=[]
        )

    # Build decision records
    decisions = []
    delta_values = []
    cas_values = []

    for row in rows:
        delta_yen = _safe_float(row[3])
        delta_values.append(delta_yen)

        # Extract CAS from diagnostics_snapshot
        diagnostics = row[9] or {}
        cas = _safe_float(diagnostics.get("cas_score"), None) if isinstance(diagnostics, dict) else None
        if cas is not None:
            cas_values.append(cas)

        # Extract risk
        risk = None
        if row[4] is not None and row[5] is not None:
            ci_width = abs(_safe_float(row[5]) - _safe_float(row[4]))
            if delta_yen != 0:
                risk = min(1.0, ci_width / abs(delta_yen))

        # Extract ROI from impact_metrics
        impact_metrics = row[10] or {}
        roi = None
        if isinstance(impact_metrics, dict):
            cost = _safe_float(impact_metrics.get("estimated_cost"), 0.0)
            if cost > 0:
                roi = delta_yen / cost

        # Extract channel
        channels = row[12]
        channel = None
        if isinstance(channels, list) and channels:
            channel = str(channels[0])
        elif isinstance(channels, str):
            try:
                decoded = json.loads(channels)
                if isinstance(decoded, list) and decoded:
                    channel = str(decoded[0])
            except:
                channel = channels

        # Extract segment from target_rule or scenario_spec
        segment = row[13]  # target_rule
        if not segment:
            scenario_spec = row[8] or {}
            if isinstance(scenario_spec, dict):
                target_segment = scenario_spec.get("target_segment")
                if isinstance(target_segment, dict):
                    segment = target_segment.get("label") or target_segment.get("name")
                elif isinstance(target_segment, str):
                    segment = target_segment

        policy_name = row[11] or row[14] or f"Policy {str(row[0])[:8]}"
        dataset_name = row[14] or "Dataset"

        decisions.append({
            "id": str(row[0]),
            "policy_name": policy_name,
            "dataset_name": dataset_name,
            "channel": channel,
            "segment": segment,
            "delta_yen": delta_yen,
            "roi": roi,
            "cas": cas,
            "risk": risk,
            "verdict": (row[6] or "hold").lower(),
            "completed_at": row[7] or datetime.utcnow().replace(tzinfo=None)
        })

    # Calculate KPIs
    total_delta_yen = sum(delta_values)
    avg_delta_yen = total_delta_yen / len(decisions) if decisions else 0.0
    mean_cas = sum(cas_values) / len(cas_values) if cas_values else None

    # Calculate CVaR (worst 10%)
    sorted_deltas = sorted(delta_values)
    tail_count = max(1, math.ceil(len(sorted_deltas) * 0.1))
    tail = sorted_deltas[:tail_count]
    cvar = abs(sum(tail) / len(tail)) if tail and sum(tail) < 0 else 0.0

    kpis = ConsoleSummaryKPIs(
        total_delta_yen=total_delta_yen,
        avg_delta_yen=avg_delta_yen,
        mean_cas=mean_cas,
        portfolio_cvar_10=cvar
    )

    # Build trend (weekly aggregation)
    weekly_map: Dict[str, float] = defaultdict(float)
    for decision in decisions:
        dt = decision["completed_at"]
        iso_year, iso_week, _ = dt.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"
        weekly_map[week_key] += decision["delta_yen"]

    trend = [
        ConsoleTrendPoint(week=week, delta_yen=delta)
        for week, delta in sorted(weekly_map.items())
    ]

    # Build segment portfolio
    segment_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "delta": 0.0,
        "count": 0,
        "cas_sum": 0.0,
        "cas_count": 0,
        "population": 0
    })

    for decision in decisions:
        segment_label = decision["segment"] or "–"
        entry = segment_map[segment_label]
        entry["delta"] += decision["delta_yen"]
        entry["count"] += 1
        if decision["cas"] is not None:
            entry["cas_sum"] += decision["cas"]
            entry["cas_count"] += 1
        # TODO: 実際のpopulation計算が必要

    segment_portfolio = [
        ConsoleSegmentPortfolio(
            segment_label=label,
            population=data["population"],
            total_delta_yen=data["delta"],
            policy_count=data["count"],
            mean_cas=data["cas_sum"] / data["cas_count"] if data["cas_count"] > 0 else None
        )
        for label, data in segment_map.items()
    ]

    # Build channel performance
    channel_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "delta": 0.0,
        "roi_sum": 0.0,
        "roi_count": 0
    })

    for decision in decisions:
        channel = decision["channel"] or "Unknown"
        entry = channel_map[channel]
        entry["delta"] += decision["delta_yen"]
        if decision["roi"] is not None:
            entry["roi_sum"] += decision["roi"]
            entry["roi_count"] += 1

    channel_performance = [
        ConsoleChannelPerformance(
            channel=channel,
            total_delta_yen=data["delta"],
            roi=data["roi_sum"] / data["roi_count"] if data["roi_count"] > 0 else None
        )
        for channel, data in channel_map.items()
    ]

    # Build decision cards
    decision_cards = [
        ConsoleDecisionCard(
            id=d["id"],
            policy_name=d["policy_name"],
            dataset_name=d["dataset_name"],
            channel=d["channel"],
            segment=d["segment"],
            delta_yen=d["delta_yen"],
            roi=d["roi"],
            cas=d["cas"],
            risk=d["risk"],
            verdict=d["verdict"],
            decided_at=d["completed_at"]
        )
        for d in decisions[:100]  # Limit to 100 latest
    ]

    logger.info(f"Console summary: {len(decisions)} decisions, total_delta_yen={total_delta_yen:.2f}")

    return DecisionConsoleSummaryResponse(
        window={
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d")
        },
        kpis=kpis,
        trend=trend,
        segment_portfolio=segment_portfolio,
        channel_performance=channel_performance,
        decision_cards=decision_cards
    )


# ==================== 既存エンドポイント（後方互換性のため残す） ====================

def _calculate_cvar(decisions: List[Decision], percentile: float = 0.1) -> float:
    if not decisions:
        return 0.0
    deltas = sorted([_safe_float(d.delta_yen) for d in decisions])
    if not deltas:
        return 0.0
    tail_count = max(1, math.ceil(len(deltas) * percentile))
    tail = deltas[:tail_count]
    tail_mean = sum(tail) / len(tail)
    return abs(tail_mean) if tail_mean < 0 else 0.0


def _extract_cas(decision: Decision) -> Optional[float]:
    if hasattr(decision, "cas_score") and decision.cas_score is not None:
        return _safe_float(decision.cas_score)
    scores = decision.quality_scores or {}
    if isinstance(scores, dict):
        value = scores.get("cas_score") or scores.get("cas")
        if value is not None:
            return _safe_float(value)
    return None


def _extract_risk(decision: Decision) -> Optional[float]:
    if hasattr(decision, "risk_score") and decision.risk_score is not None:
        return _safe_float(decision.risk_score)
    scores = decision.quality_scores or {}
    if isinstance(scores, dict) and scores.get("risk_score") is not None:
        return _safe_float(scores.get("risk_score"))
    if decision.delta_yen_ci_low is not None and decision.delta_yen is not None:
        ci_width = abs(_safe_float(decision.delta_yen_ci_high) - _safe_float(decision.delta_yen_ci_low))
        if ci_width and decision.delta_yen:
            return min(1.0, ci_width / abs(decision.delta_yen))
    return None


def _extract_estimated_users(decision: Decision) -> int:
    if decision.estimator_results:
        impact = decision.estimator_results.get("impact_metrics") if isinstance(decision.estimator_results, dict) else None
        if impact and isinstance(impact, dict):
            users = impact.get("users_affected") or impact.get("total_users")
            if users:
                return int(users)
    spec = decision.scenario_spec or {}
    if isinstance(spec, dict):
        segment_info = spec.get("target_segment") or {}
        if isinstance(segment_info, dict) and segment_info.get("estimated_users"):
            return int(segment_info.get("estimated_users"))
    return 0


def _extract_roi(decision: Decision) -> Optional[float]:
    scores = decision.quality_scores or {}
    if isinstance(scores, dict) and scores.get("roi") is not None:
        return _safe_float(scores.get("roi"))
    impact = decision.estimator_results.get("impact_metrics") if isinstance(decision.estimator_results, dict) else None
    if impact and isinstance(impact, dict):
        cost = _safe_float(impact.get("estimated_cost"), 0.0)
        if cost:
            return _safe_float(decision.delta_yen) / cost
    return None


def _extract_cas_from_analysis(run: AnalysisRun) -> Optional[float]:
    diagnostics = run.diagnostics_snapshot or {}
    if isinstance(diagnostics, dict):
        value = diagnostics.get("cas_score") or diagnostics.get("cas")
        if value is not None:
            return _safe_float(value)
    return None


def _extract_risk_from_analysis(run: AnalysisRun) -> Optional[float]:
    impact = run.impact_metrics or {}
    if isinstance(impact, dict):
        cost = _safe_float(impact.get("estimated_cost"), 0.0)
        if cost and run.delta_yen:
            return min(1.0, cost / abs(run.delta_yen))
    return None


def _extract_roi_from_analysis(run: AnalysisRun) -> Optional[float]:
    metrics = run.impact_metrics or {}
    if isinstance(metrics, dict):
        cost = _safe_float(metrics.get("estimated_cost"), 0.0)
        if cost:
            return _safe_float(run.delta_yen) / cost
    return None


def _extract_users_from_analysis(run: AnalysisRun) -> int:
    impact = run.impact_metrics or {}
    if isinstance(impact, dict):
        users = impact.get("users_affected") or impact.get("total_users")
        if users:
            return int(users)
    spec = run.scenario_spec or {}
    if isinstance(spec, dict):
        target = spec.get("target_segment")
        if isinstance(target, dict) and target.get("estimated_users"):
            return int(target.get("estimated_users"))
    return 0


@dataclass
class DecisionConsoleRecordV2:
    """Normalized decision row used by both analysis runs and legacy decision cards."""
    id: str
    dataset_label: str
    policy_name: str
    channel: Optional[str]
    segment_label: Optional[str]
    segment_population: Optional[int]
    delta_yen: float
    roi: Optional[float]
    cas_score: Optional[float]
    risk_score: Optional[float]
    verdict: str
    period_start: date
    period_end: date
    decided_at: datetime


class DecisionTrendPointV2(BaseModel):
    bucket: str
    delta_yen: float
    target_yen: Optional[float] = None


class DecisionSegmentPortfolioPointV2(BaseModel):
    segment_id: str
    segment_label: str
    population: int
    total_delta_yen: float
    policy_count: int
    mean_cas: Optional[float] = None


class DecisionChannelPointV2(BaseModel):
    channel: str
    total_delta_yen: float
    roi: Optional[float] = None


class DecisionPolicyRowV2(BaseModel):
    id: str
    dataset_label: str
    policy_name: str
    channel: Optional[str] = None
    segment_label: Optional[str] = None
    delta_yen: float
    roi: Optional[float] = None
    cas_score: Optional[float] = None
    risk_score: Optional[float] = None
    verdict: str
    start_date: str
    end_date: str
    decided_at: datetime


class DecisionConsoleSummaryV2(BaseModel):
    total_delta_yen: float
    avg_delta_yen_per_policy: float
    mean_cas: Optional[float] = None
    cvar_yen_p10: Optional[float] = None
    trend: List[DecisionTrendPointV2]
    segment_portfolio: List[DecisionSegmentPortfolioPointV2]
    channel_performance: List[DecisionChannelPointV2]
    decisions: List[DecisionPolicyRowV2]


async def _load_decision_like_from_analysis(
    db: AsyncSession,
    tenant_uuid: uuid_lib.UUID,
    start_dt: datetime,
    end_dt: datetime
) -> List[Any]:
    # Convert to naive datetime for PostgreSQL compatibility (DB stores timestamp with time zone)
    # but SQLAlchemy sometimes sends it without timezone info
    start_naive = start_dt.replace(tzinfo=None) if start_dt.tzinfo else start_dt
    end_naive = end_dt.replace(tzinfo=None) if end_dt.tzinfo else end_dt

    logger.info(f"Loading analysis runs: tenant={tenant_uuid}, start={start_naive}, end={end_naive}")
    query = (
        select(AnalysisRun)
        .where(
            AnalysisRun.tenant_id == tenant_uuid,
            AnalysisRun.completed_at >= start_naive,
            AnalysisRun.completed_at <= end_naive,
            AnalysisRun.status == "completed",
            AnalysisRun.delta_yen.isnot(None)
        )
        .options(joinedload(AnalysisRun.dataset))
        .order_by(desc(AnalysisRun.completed_at))
    )
    result = await db.execute(query)
    runs = result.scalars().all()
    logger.info(f"Found {len(runs)} analysis runs")
    decision_like: List[Any] = []
    for run in runs:
        dataset_name = run.dataset.name if run.dataset else None
        scenario_name = dataset_name or "Scenario"
        if run.treatment_col and run.outcome_col:
            scenario_name = f"{scenario_name} ({run.treatment_col}->{run.outcome_col})"
        created_at = run.completed_at or run.started_at or datetime.now(timezone.utc)
        decision_like.append(SimpleNamespace(
            id=str(run.id),
            delta_yen=_safe_float(run.delta_yen),
            delta_yen_ci_low=_safe_float(run.delta_yen_ci_low) if run.delta_yen_ci_low else None,
            delta_yen_ci_high=_safe_float(run.delta_yen_ci_high) if run.delta_yen_ci_high else None,
            cas_score=_extract_cas_from_analysis(run),
            risk_score=_extract_risk_from_analysis(run),
            verdict=run.verdict or "Hold",
            channel=dataset_name,
            segment=None,
            scenario_name=scenario_name,
            policy_name=scenario_name,
            scenario_spec=run.scenario_spec,
            quality_scores=run.diagnostics_snapshot or {},
            estimator_results={"impact_metrics": run.impact_metrics} if run.impact_metrics else {},
            created_at=created_at,
            roi=_extract_roi_from_analysis(run),
            impact_users=_extract_users_from_analysis(run)
        ))
    return decision_like


def _ensure_utc(dt_value: Optional[datetime]) -> datetime:
    if dt_value is None:
        return datetime.now(timezone.utc)
    if dt_value.tzinfo is None:
        return dt_value.replace(tzinfo=timezone.utc)
    return dt_value


def _coerce_dict(payload: Any) -> Dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return {}
    return {}


def _extract_spec_payload(spec: Any) -> Dict[str, Any]:
    data = _coerce_dict(spec or {})
    inner = data.get("spec")
    if isinstance(inner, dict):
        return inner
    return data


def _extract_segment_label_from_spec(spec: Any) -> Optional[str]:
    payload = _extract_spec_payload(spec)
    segment_info = payload.get("target_segment")
    if isinstance(segment_info, dict):
        return (
            segment_info.get("label")
            or segment_info.get("name")
            or segment_info.get("segment")
            or segment_info.get("id")
            or segment_info.get("condition")
        )
    if isinstance(segment_info, str):
        return segment_info
    return None


def _extract_channels_from_policy(policy: Optional[Any]) -> Optional[str]:
    if policy is None:
        return None
    channels = getattr(policy, "channels", None)
    if isinstance(channels, list) and channels:
        return str(channels[0])
    if isinstance(channels, str):
        try:
            decoded = json.loads(channels)
            if isinstance(decoded, list) and decoded:
                return str(decoded[0])
        except json.JSONDecodeError:
            return channels
    return None


def _extract_channel_from_spec(spec: Any) -> Optional[str]:
    payload = _extract_spec_payload(spec)
    channels = payload.get("channels")
    if isinstance(channels, list) and channels:
        return str(channels[0])
    if isinstance(channels, str):
        return channels
    return None


async def _collect_console_decisions_from_runs(
    db: AsyncSession,
    tenant_uuid: uuid_lib.UUID,
    start_dt: datetime,
    end_dt: datetime
) -> List[DecisionConsoleRecordV2]:
    start_naive = start_dt.replace(tzinfo=None) if start_dt.tzinfo else start_dt
    end_naive = end_dt.replace(tzinfo=None) if end_dt.tzinfo else end_dt

    query = (
        select(AnalysisRun)
        .where(
            AnalysisRun.tenant_id == tenant_uuid,
            AnalysisRun.status == "completed",
            AnalysisRun.completed_at.isnot(None),
            AnalysisRun.completed_at >= start_naive,
            AnalysisRun.completed_at < end_naive,
            AnalysisRun.delta_yen.isnot(None)
        )
        .options(joinedload(AnalysisRun.dataset), joinedload(AnalysisRun.policy))
        .order_by(desc(AnalysisRun.completed_at))
    )
    result = await db.execute(query)
    runs = result.scalars().all()

    decisions: List[DecisionConsoleRecordV2] = []
    for run in runs:
        delta = _safe_float(run.delta_yen)
        decided_at = _ensure_utc(run.completed_at or run.started_at)
        dataset_label = run.dataset.name if run.dataset else "Dataset"
        policy_name = run.policy.name if run.policy else dataset_label
        channel = _extract_channel_from_spec(run.scenario_spec) or _extract_channels_from_policy(run.policy)
        segment_label = _extract_segment_label_from_spec(run.scenario_spec)
        if segment_label is None:
            target_rule = getattr(run.policy, "target_rule", None) if run.policy else None
            segment_label = target_rule
        population = _extract_users_from_analysis(run)
        period_start = _ensure_utc(run.started_at or run.completed_at or datetime.now(timezone.utc)).date()
        period_end = _ensure_utc(run.completed_at or run.started_at or datetime.now(timezone.utc)).date()

        decisions.append(DecisionConsoleRecordV2(
            id=str(run.id),
            dataset_label=dataset_label,
            policy_name=policy_name,
            channel=channel,
            segment_label=segment_label,
            segment_population=population,
            delta_yen=delta,
            roi=_extract_roi_from_analysis(run),
            cas_score=_extract_cas_from_analysis(run),
            risk_score=_extract_risk_from_analysis(run),
            verdict=(run.verdict or "hold").lower(),
            period_start=period_start,
            period_end=period_end,
            decided_at=decided_at
        ))
    return decisions


async def _collect_console_decisions_from_cards(
    db: AsyncSession,
    tenant_uuid: uuid_lib.UUID,
    start_dt: datetime,
    end_dt: datetime
) -> List[DecisionConsoleRecordV2]:
    query = (
        select(Decision)
        .where(
            Decision.tenant_id == tenant_uuid,
            Decision.created_at >= start_dt,
            Decision.created_at < end_dt
        )
        .order_by(desc(Decision.created_at))
    )
    try:
        result = await db.execute(query)
    except ProgrammingError:
        await db.rollback()
        return []

    cards = result.scalars().all()
    decisions: List[DecisionConsoleRecordV2] = []
    for card in cards:
        decided_at = _ensure_utc(card.created_at)
        delta = _safe_float(card.delta_yen)
        population = _extract_estimated_users(card)
        period_date = decided_at.date()
        decisions.append(DecisionConsoleRecordV2(
            id=str(card.id),
            dataset_label=card.scenario_name or "Scenario",
            policy_name=card.scenario_name or "Policy",
            channel=card.channel,
            segment_label=card.segment,
            segment_population=population,
            delta_yen=delta,
            roi=_extract_roi(card),
            cas_score=_extract_cas(card),
            risk_score=_extract_risk(card),
            verdict=(card.verdict or "hold").lower(),
            period_start=period_date,
            period_end=period_date,
            decided_at=decided_at
        ))
    return decisions


async def _load_console_decisions(
    db: AsyncSession,
    tenant_uuid: uuid_lib.UUID,
    start_dt: datetime,
    end_dt: datetime
) -> List[DecisionConsoleRecordV2]:
    decisions = await _collect_console_decisions_from_runs(db, tenant_uuid, start_dt, end_dt)
    if decisions:
        return decisions
    return await _collect_console_decisions_from_cards(db, tenant_uuid, start_dt, end_dt)


def _calculate_cvar_from_values(deltas: List[float], percentile: float = 0.1) -> Optional[float]:
    if not deltas:
        return None
    sorted_values = sorted(deltas)
    tail_count = max(1, math.floor(len(sorted_values) * percentile))
    tail = sorted_values[:tail_count]
    if not tail:
        return None
    tail_mean = sum(tail) / len(tail)
    if tail_mean >= 0:
        return 0.0
    return tail_mean


def _week_bucket(dt_value: datetime) -> str:
    iso_year, iso_week, _ = dt_value.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _aggregate_trend(decisions: List[DecisionConsoleRecordV2], per_bucket_target: Optional[float] = None) -> List[DecisionTrendPointV2]:
    bucket_map: Dict[str, float] = defaultdict(float)
    for decision in decisions:
        bucket = _week_bucket(decision.decided_at)
        bucket_map[bucket] += decision.delta_yen
    trend_points: List[DecisionTrendPointV2] = []
    for bucket, value in sorted(bucket_map.items()):
        trend_points.append(DecisionTrendPointV2(
            bucket=bucket,
            delta_yen=value,
            target_yen=per_bucket_target
        ))
    return trend_points


def _segment_slug(label: str) -> str:
    normalized = label.strip().lower().replace(" ", "_")
    return normalized or "segment"


def _aggregate_segments(decisions: List[DecisionConsoleRecordV2]) -> List[DecisionSegmentPortfolioPointV2]:
    segment_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "delta": 0.0,
        "cas_sum": 0.0,
        "cas_count": 0,
        "population": 0,
        "policy_count": 0
    })
    for decision in decisions:
        key = decision.segment_label or "–"
        entry = segment_map[key]
        entry["delta"] += decision.delta_yen
        entry["policy_count"] += 1
        if decision.segment_population:
            entry["population"] += int(decision.segment_population)
        if decision.cas_score is not None:
            entry["cas_sum"] += decision.cas_score
            entry["cas_count"] += 1

    segment_points: List[DecisionSegmentPortfolioPointV2] = []
    for name, values in segment_map.items():
        label = name or "–"
        cas_mean = values["cas_sum"] / values["cas_count"] if values["cas_count"] else None
        segment_points.append(DecisionSegmentPortfolioPointV2(
            segment_id=_segment_slug(label),
            segment_label=label,
            population=values["population"],
            total_delta_yen=values["delta"],
            policy_count=values["policy_count"],
            mean_cas=cas_mean
        ))
    return segment_points


def _aggregate_channels(decisions: List[DecisionConsoleRecordV2]) -> List[DecisionChannelPointV2]:
    channel_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "delta": 0.0,
        "roi_sum": 0.0,
        "roi_count": 0
    })
    for decision in decisions:
        key = decision.channel or "Unknown"
        entry = channel_map[key]
        entry["delta"] += decision.delta_yen
        if decision.roi is not None:
            entry["roi_sum"] += decision.roi
            entry["roi_count"] += 1

    channel_points: List[DecisionChannelPointV2] = []
    for name, values in channel_map.items():
        roi_mean = values["roi_sum"] / values["roi_count"] if values["roi_count"] else None
        channel_points.append(DecisionChannelPointV2(
            channel=name,
            total_delta_yen=values["delta"],
            roi=roi_mean
        ))
    return channel_points


def _build_decision_rows(decisions: List[DecisionConsoleRecordV2]) -> List[DecisionPolicyRowV2]:
    rows: List[DecisionPolicyRowV2] = []
    for record in decisions:
        start_str = record.period_start.isoformat()
        end_str = record.period_end.isoformat()
        rows.append(DecisionPolicyRowV2(
            id=record.id,
            dataset_label=record.dataset_label,
            policy_name=record.policy_name,
            channel=record.channel,
            segment_label=record.segment_label,
            delta_yen=record.delta_yen,
            roi=record.roi,
            cas_score=record.cas_score,
            risk_score=record.risk_score,
            verdict=record.verdict,
            start_date=start_str,
            end_date=end_str,
            decided_at=_ensure_utc(record.decided_at)
        ))
    return rows


def _build_summary_metrics(decisions: List[DecisionConsoleRecordV2]) -> tuple[float, float, Optional[float], Optional[float]]:
    total_delta = sum(record.delta_yen for record in decisions)
    avg_delta = total_delta / len(decisions) if decisions else 0.0
    cas_values = [record.cas_score for record in decisions if record.cas_score is not None]
    mean_cas = (sum(cas_values) / len(cas_values)) if cas_values else None
    cvar = _calculate_cvar_from_values([record.delta_yen for record in decisions], percentile=0.1)
    return total_delta, avg_delta, mean_cas, cvar


def _compute_weekly_target(total_delta: float, trend_points: int) -> Optional[float]:
    if trend_points <= 0:
        return None
    return total_delta / trend_points


@decision_console_router.get("/overview", response_model=DecisionConsoleSummaryV2)
async def get_decision_console_summary(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    locale: Optional[str] = Query(None, description="Locale hint (ja/en)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Aggregated summary endpoint for Decision Console (spec: １.pdf).
    """
    if to_date < from_date:
        raise HTTPException(status_code=400, detail="'to' must be on or after 'from'")

    tenant_uuid = _get_tenant_uuid(current_user)
    start_dt = datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(to_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

    decisions = await _load_console_decisions(db, tenant_uuid, start_dt, end_dt)
    if not decisions:
        return DecisionConsoleSummaryV2(
            total_delta_yen=0.0,
            avg_delta_yen_per_policy=0.0,
            mean_cas=None,
            cvar_yen_p10=None,
            trend=[],
            segment_portfolio=[],
            channel_performance=[],
            decisions=[]
        )

    total_delta, avg_delta, mean_cas, cvar = _build_summary_metrics(decisions)
    bucket_count = len({ _week_bucket(record.decided_at) for record in decisions })
    target_per_week = _compute_weekly_target(total_delta, bucket_count)
    trend = _aggregate_trend(decisions, target_per_week)
    segment_portfolio = _aggregate_segments(decisions)
    channel_performance = _aggregate_channels(decisions)
    decision_rows = _build_decision_rows(sorted(decisions, key=lambda record: record.decided_at, reverse=True)[:200])

    return DecisionConsoleSummaryV2(
        total_delta_yen=total_delta,
        avg_delta_yen_per_policy=avg_delta,
        mean_cas=mean_cas,
        cvar_yen_p10=cvar,
        trend=trend,
        segment_portfolio=segment_portfolio,
        channel_performance=channel_performance,
        decisions=decision_rows
    )


# Console-specific models
class DeltaYenHistoryItem(BaseModel):
    """Δ¥履歴項目 (週次)"""
    week: str = Field(..., description="Week ending date (YYYY-MM-DD)")
    delta_yen: float = Field(..., description="Average Δ¥ for the week")
    decision_count: int = Field(..., description="Number of completed analyses in the week")


class VerdictDistribution(BaseModel):
    """判定分布"""
    go: int = Field(0, description="Go count")
    canary: int = Field(0, description="Canary count")
    hold: int = Field(0, description="Hold count")


class DeltaYenSummary(BaseModel):
    """Δ¥サマリー"""
    period_days: int = Field(..., description="Period in days")
    total_decisions: int = Field(..., description="Total number of decisions")
    verdict_distribution: VerdictDistribution = Field(..., description="Verdict distribution")
    avg_delta_yen: float = Field(..., description="Average Δ¥")
    max_delta_yen: float = Field(..., description="Maximum Δ¥")
    min_delta_yen: float = Field(..., description="Minimum Δ¥")
    best_scenario: Optional[DecisionCard] = Field(None, description="Best scenario (highest Δ¥)")
    history: List[DeltaYenHistoryItem] = Field(default_factory=list, description="Daily history")


class SummaryBlock(BaseModel):
    """仕様書準拠: total_incremental_profit, average_delta, mean_cas, risk_cvar"""
    total_incremental_profit: float = 0.0
    average_delta: float = 0.0
    mean_cas: float = 0.0
    risk_cvar: float = 0.0  # 仕様書: risk_cvar (負の円値)


class WeeklyDeltaPoint(BaseModel):
    """仕様書準拠: week, delta_yen, target_yen"""
    week: str
    delta_yen: float
    target_yen: float = 0.0  # 仕様書: target_yen (目標線)
    decision_count: int = 0  # 追加情報


class SegmentPoint(BaseModel):
    """仕様書準拠: segment_id, segment_name, population, delta_yen, policy_count, cas_mean"""
    segment_id: str
    segment_name: str
    population: int
    delta_yen: float
    policy_count: int
    cas_mean: float


class ChannelPerformance(BaseModel):
    """仕様書準拠: channel, delta_yen, roi"""
    channel: str
    delta_yen: float
    roi: float


class PolicyCard(BaseModel):
    """仕様書準拠: policy_id, policy_name, segment_id, channel, delta_yen, roi, cas, risk_score, verdict, start_date, end_date"""
    policy_id: str
    policy_name: str
    segment_id: Optional[str] = None
    channel: Optional[str] = None
    delta_yen: float
    roi: float = 0.0
    cas: float = 0.0
    risk_score: float = 0.0
    verdict: str  # "go" | "canary" | "hold"
    start_date: str
    end_date: str


class DecisionConsoleOverview(BaseModel):
    """仕様書準拠のレスポンスモデル"""
    summary: SummaryBlock
    time_series: Dict[str, List[WeeklyDeltaPoint]]
    segments: List[SegmentPoint]
    channels: List[ChannelPerformance]
    policies: List[PolicyCard]


@dataclass
class ConsoleDecisionRecord:
    """Normalized decision row used by both analysis runs and legacy decision cards."""
    id: str
    dataset_label: str
    policy_name: str
    channel: Optional[str]
    segment_label: Optional[str]
    segment_population: Optional[int]
    delta_yen: float
    roi: Optional[float]
    cas_score: Optional[float]
    risk_score: Optional[float]
    verdict: str
    period_start: date
    period_end: date
    decided_at: datetime


class TrendPoint(BaseModel):
    bucket: str
    delta_yen: float
    target_yen: Optional[float] = None


class SegmentPortfolioPoint(BaseModel):
    segment_id: str
    segment_label: str
    population: int
    total_delta_yen: float
    policy_count: int
    mean_cas: Optional[float] = None


class ChannelPoint(BaseModel):
    channel: str
    total_delta_yen: float
    roi: Optional[float] = None


class DecisionPolicyRow(BaseModel):
    id: str
    dataset_label: str
    policy_name: str
    channel: Optional[str] = None
    segment_label: Optional[str] = None
    delta_yen: float
    roi: Optional[float] = None
    cas_score: Optional[float] = None
    risk_score: Optional[float] = None
    verdict: str
    start_date: str
    end_date: str


class DecisionConsoleSummary(BaseModel):
    total_delta_yen: float
    avg_delta_yen_per_policy: float
    mean_cas: Optional[float] = None
    cvar_yen_p10: Optional[float] = None
    trend: List[TrendPoint]
    segment_portfolio: List[SegmentPortfolioPoint]
    channel_performance: List[ChannelPoint]
    decisions: List[DecisionPolicyRow]


@router.get("/delta-yen-summary", response_model=DeltaYenSummary)
async def get_delta_yen_summary(
    period_days: int = Query(7, ge=1, le=365, description="集計期間（日数）"),
    analysis_ids: Optional[str] = Query(None, description="Comma-separated analysis IDs to filter"),
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
    # 期間フィルタ - naive datetime for PostgreSQL compatibility
    since = (datetime.now(timezone.utc) - timedelta(days=period_days)).replace(tzinfo=None)

    tenant_id_raw = current_user.get("tenant_id")
    if tenant_id_raw is None:
        tenant_uuid = DEFAULT_TENANT_ID
    elif isinstance(tenant_id_raw, uuid_lib.UUID):
        tenant_uuid = tenant_id_raw
    else:
        tenant_uuid = uuid_lib.UUID(str(tenant_id_raw))

    filters = [
        AnalysisRun.tenant_id == tenant_uuid,
        AnalysisRun.status == "completed",
        AnalysisRun.completed_at >= since
    ]
    
    # Filter by analysis_ids if provided
    if analysis_ids:
        try:
            id_list = [uuid_lib.UUID(aid.strip()) for aid in analysis_ids.split(",") if aid.strip()]
            if id_list:
                filters.append(AnalysisRun.id.in_(id_list))
        except ValueError:
            pass  # Ignore invalid UUIDs
    
    # Filter by analysis_ids if provided
    if analysis_ids:
        id_list = [uuid_lib.UUID(aid.strip()) for aid in analysis_ids.split(",") if aid.strip()]
        if id_list:
            filters.append(AnalysisRun.id.in_(id_list))

    # 集計クエリ
    query = select(
        func.count(AnalysisRun.id).label("total_decisions"),
        func.count().filter(AnalysisRun.verdict == "Go").label("go_count"),
        func.count().filter(AnalysisRun.verdict == "Canary").label("canary_count"),
        func.count().filter(AnalysisRun.verdict == "Hold").label("hold_count"),
        func.avg(AnalysisRun.delta_yen).label("avg_delta_yen"),
        func.max(AnalysisRun.delta_yen).label("best_delta_yen"),
        func.min(AnalysisRun.delta_yen).label("worst_delta_yen")
    ).where(*filters)

    result = await db.execute(query)
    row = result.one()

    # ベストシナリオ取得（Δ¥最大のAnalysisRun）
    best_query = (
        select(AnalysisRun)
        .options(joinedload(AnalysisRun.dataset))
        .where(*filters)
        .order_by(desc(AnalysisRun.delta_yen))
        .limit(1)
    )

    best_result = await db.execute(best_query)
    best_run = best_result.scalar_one_or_none()

    best_card = None
    if best_run:
        dataset_name = best_run.dataset.name if best_run.dataset else "Scenario"
        scenario_name = f"{dataset_name} ({best_run.treatment_col}->{best_run.outcome_col})"
        best_card = DecisionCard(
            id=str(best_run.id),
            created_at=best_run.started_at or datetime.now(timezone.utc),
            updated_at=best_run.completed_at or best_run.started_at or datetime.now(timezone.utc),
            tenant_id=str(best_run.tenant_id or tenant_uuid),
            policy_id=str(best_run.policy_id or best_run.dataset_id),
            scenario_id=str(best_run.dataset_id),
            scenario_name=scenario_name,
            delta_yen=float(best_run.delta_yen or 0),
            delta_yen_ci_low=float(best_run.delta_yen_ci_low or 0),
            delta_yen_ci_high=float(best_run.delta_yen_ci_high or 0),
            delta_yen_std=None,
            verdict=best_run.verdict or "Hold",
            reason=None,
            channel=dataset_name,
            segment=None,
            quality_scores=None,
            scenario_spec=best_run.scenario_spec,
            estimator_results=None
        )

    return DeltaYenSummary(
        period_days=period_days,
        total_decisions=row.total_decisions or 0,
        verdict_distribution=VerdictDistribution(
            go=row.go_count or 0,
            canary=row.canary_count or 0,
            hold=row.hold_count or 0
        ),
        avg_delta_yen=float(row.avg_delta_yen or 0),
        max_delta_yen=float(row.best_delta_yen or 0),
        min_delta_yen=float(row.worst_delta_yen or 0),
        best_scenario=best_card,
        history=[]  # TODO: 実装する
    )


@router.get("/delta-yen-history", response_model=list[DeltaYenHistoryItem])
async def get_delta_yen_history(
    period: Literal["week", "month"] = Query("week", description="集計期間単位"),
    weeks: int = Query(6, ge=1, le=52, description="週数（週単位の場合）"),
    analysis_ids: Optional[str] = Query(None, description="Comma-separated analysis IDs to filter"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Δ¥履歴取得（週次）

    **用途**: Decision Console の棒グラフ表示
    """
    # 週次集計（簡易実装: 7日ごと）- naive datetime for PostgreSQL
    history = []
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    tenant_id_raw = current_user.get("tenant_id")
    if tenant_id_raw is None:
        tenant_uuid = DEFAULT_TENANT_ID
    elif isinstance(tenant_id_raw, uuid_lib.UUID):
        tenant_uuid = tenant_id_raw
    else:
        tenant_uuid = uuid_lib.UUID(str(tenant_id_raw))

    for i in range(weeks):
        week_end = now - timedelta(days=i * 7)
        week_start = week_end - timedelta(days=7)

        week_filters = [
            AnalysisRun.tenant_id == tenant_uuid,
            AnalysisRun.status == "completed",
            AnalysisRun.completed_at >= week_start,
            AnalysisRun.completed_at < week_end
        ]
        
        # Add analysis_ids filter if provided
        if analysis_ids:
            try:
                id_list = [uuid_lib.UUID(aid.strip()) for aid in analysis_ids.split(",") if aid.strip()]
                if id_list:
                    week_filters.append(AnalysisRun.id.in_(id_list))
            except ValueError:
                pass

        query = select(
            func.avg(AnalysisRun.delta_yen).label("avg_delta_yen"),
            func.count(AnalysisRun.id).label("decision_count")
        ).where(*week_filters)

        result = await db.execute(query)
        row = result.one()

        # Format date as YYYY-MM-DD
        date_str = week_end.strftime("%Y-%m-%d")
        history.append(DeltaYenHistoryItem(
            week=date_str,
            delta_yen=float(row.avg_delta_yen or 0),
            decision_count=int(row.decision_count or 0)
        ))

    # 古い順に並び替え
    history.reverse()

    return history


@router.get("/verdict-distribution", response_model=VerdictDistribution)
async def get_verdict_distribution(
    period_days: int = Query(7, ge=1, le=365, description="集計期間（日数）"),
    analysis_ids: Optional[str] = Query(None, description="Comma-separated analysis IDs to filter"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    判定内訳取得（Go/Canary/Hold）

    **用途**: Decision Console の円グラフ表示
    """
    since = (datetime.now(timezone.utc) - timedelta(days=period_days)).replace(tzinfo=None)

    tenant_id_raw = current_user.get("tenant_id")
    if tenant_id_raw is None:
        tenant_uuid = DEFAULT_TENANT_ID
    elif isinstance(tenant_id_raw, uuid_lib.UUID):
        tenant_uuid = tenant_id_raw
    else:
        tenant_uuid = uuid_lib.UUID(str(tenant_id_raw))

    verdict_filters = [
        AnalysisRun.tenant_id == tenant_uuid,
        AnalysisRun.status == "completed",
        AnalysisRun.completed_at >= since
    ]
    
    # Add analysis_ids filter if provided
    if analysis_ids:
        try:
            id_list = [uuid_lib.UUID(aid.strip()) for aid in analysis_ids.split(",") if aid.strip()]
            if id_list:
                verdict_filters.append(AnalysisRun.id.in_(id_list))
        except ValueError:
            pass

    query = select(
        func.count().filter(AnalysisRun.verdict == "Go").label("go"),
        func.count().filter(AnalysisRun.verdict == "Canary").label("canary"),
        func.count().filter(AnalysisRun.verdict == "Hold").label("hold"),
        func.count(AnalysisRun.id).label("total")
    ).where(*verdict_filters)

    result = await db.execute(query)
    row = result.one()

    return VerdictDistribution(
        go=row.go or 0,
        canary=row.canary or 0,
        hold=row.hold or 0,
        total=row.total or 0
    )


@router.get("/overview", response_model=DecisionConsoleOverview)
async def get_decision_console_overview(
    start_date: Optional[datetime] = Query(None, description="Start date (UTC)"),
    end_date: Optional[datetime] = Query(None, description="End date (UTC)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Aggregated dataset for Decision Console v2
    """
    tenant_uuid = _get_tenant_uuid(current_user)
    end_dt = end_date or datetime.now(timezone.utc)
    start_dt = start_date or (end_dt - timedelta(days=28))

    logger.info(f"Console overview: user={current_user}, tenant_uuid={tenant_uuid}, range={start_dt} to {end_dt}")

    summary = SummaryBlock()

    decisions: List[Any] = []
    decisions_query = select(Decision).where(
        Decision.tenant_id == tenant_uuid,
        Decision.created_at >= start_dt,
        Decision.created_at <= end_dt
    ).order_by(desc(Decision.created_at))
    try:
        result = await db.execute(decisions_query)
        decisions = result.scalars().all()
    except ProgrammingError:
        await db.rollback()
        logger.warning("decisions table not found; falling back to analysis runs")
        decisions = []

    if not decisions:
        try:
            analysis_decisions = await _load_decision_like_from_analysis(db, tenant_uuid, start_dt, end_dt)
        except Exception as exc:
            await db.rollback()
            logger.error(f"Failed to load analysis fallbacks: {exc}")
            analysis_decisions = []
        decisions = analysis_decisions

    if not decisions:
        return DecisionConsoleOverview(
            summary=summary,
            time_series={"weekly_delta": []},
            segments=[],
            channels=[],
            policies=[]
        )

    total_delta = 0.0
    cas_values: List[float] = []
    weekly_map: Dict[str, Dict[str, Any]] = {}
    segments_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "delta": 0.0,
        "cas_sum": 0.0,
        "count": 0,
        "users": 0
    })
    channels_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "delta": 0.0,
        "roi_sum": 0.0,
        "count": 0
    })
    policies: List[PolicyCard] = []

    for decision in decisions:
        delta = _safe_float(decision.delta_yen)
        total_delta += delta
        cas_value = _extract_cas(decision)
        if cas_value is not None:
            cas_values.append(cas_value)

        created_at = decision.created_at or datetime.now(timezone.utc)
        iso_year, iso_week, _ = created_at.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"
        if week_key not in weekly_map:
            weekly_map[week_key] = {
                "delta_yen": 0.0,
                "decision_count": 0,
                "target_yen": 1000000.0  # 仕様書: 目標値（仮）
            }
        weekly_map[week_key]["delta_yen"] += delta
        weekly_map[week_key]["decision_count"] += 1

        segment_name = decision.segment or "Unknown"
        segment_entry = segments_map[segment_name]
        segment_entry["delta"] += delta
        segment_entry["count"] += 1
        estimated_users = getattr(decision, "impact_users", None)
        if estimated_users is None:
            estimated_users = _extract_estimated_users(decision) if isinstance(decision, Decision) else 0
        segment_entry["users"] += estimated_users
        if cas_value is not None:
            segment_entry["cas_sum"] += cas_value

        channel_name = decision.channel or "Unknown"
        channel_entry = channels_map[channel_name]
        channel_entry["delta"] += delta
        channel_entry["count"] += 1
        roi_value = _extract_roi(decision)
        if roi_value is not None:
            channel_entry["roi_sum"] += roi_value

        # 仕様書準拠: PolicyCard形式
        risk_value = _extract_risk(decision)
        start_date_str = created_at.strftime("%Y-%m-%d")
        end_date_str = start_date_str  # 単発分析の場合は同日

        policies.append(PolicyCard(
            policy_id=str(decision.id),
            policy_name=getattr(decision, "scenario_name", "Policy"),
            segment_id=segment_name.lower().replace(" ", "_"),
            channel=decision.channel,
            delta_yen=delta,
            roi=roi_value or 0.0,
            cas=cas_value or 0.0,
            risk_score=risk_value or 0.0,
            verdict=(decision.verdict or "Hold").lower(),
            start_date=start_date_str,
            end_date=end_date_str
        ))

    summary.total_incremental_profit = total_delta
    summary.average_delta = total_delta / len(decisions) if decisions else 0.0
    summary.mean_cas = sum(cas_values) / len(cas_values) if cas_values else 0.0
    summary.risk_cvar = -_calculate_cvar(decisions, percentile=0.1)  # 仕様書: 負の値

    # 仕様書準拠: WeeklyDeltaPoint
    weekly_series = []
    for week_key in sorted(weekly_map.keys()):
        data = weekly_map[week_key]
        weekly_series.append(WeeklyDeltaPoint(
            week=week_key,
            delta_yen=data["delta_yen"],
            target_yen=data["target_yen"],
            decision_count=data["decision_count"]
        ))

    # 仕様書準拠: SegmentPoint
    segments = []
    for name, data in segments_map.items():
        count = data["count"] or 1
        cas_mean = (data["cas_sum"] / count) if data["cas_sum"] else 0.0
        segments.append(SegmentPoint(
            segment_id=name.lower().replace(" ", "_"),
            segment_name=name,
            population=data["users"],
            delta_yen=data["delta"],
            policy_count=data["count"],
            cas_mean=cas_mean
        ))

    # 仕様書準拠: ChannelPerformance
    channels = []
    for name, data in channels_map.items():
        count = data["count"] or 1
        avg_roi = (data["roi_sum"] / count) if data["roi_sum"] else 0.0
        channels.append(ChannelPerformance(
            channel=name,
            delta_yen=data["delta"],
            roi=avg_roi
        ))

    policies_sorted = sorted(policies, key=lambda p: p.start_date, reverse=True)[:50]

    return DecisionConsoleOverview(
        summary=summary,
        time_series={"weekly_delta": weekly_series},
        segments=segments,
        channels=channels,
        policies=policies_sorted
    )
