"""
Portfolio and ROI endpoints - Marketing Portfolio & ROI 画面用
仕様: 修正.pdf に完全準拠

役割:
- Policy Lab由来のポリシーのみを使用
- PortfolioFlag.include による明示的なINCLUDE/EXCLUDE管理
- Pareto効率的なポートフォリオを推奨
- Empty/単一/複数ポリシーの全ケースで意味のあるUI表示
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any
from loguru import logger
import math
from datetime import datetime, timedelta

from cqox.auth.dependencies import get_current_user
from cqox.database.connection import get_db

router = APIRouter()


# ==================== 修正.pdf仕様準拠モデル ====================

class PortfolioConstraints(BaseModel):
    """ポートフォリオ制約"""
    min_cas: float = 0.15  # 最小CAS要件
    max_risk: float = 0.6  # 最大リスク許容


class PortfolioDiagnostics(BaseModel):
    """ポートフォリオ診断"""
    status: Literal["ok", "constraint_violation"]
    message: str


class PortfolioRecommended(BaseModel):
    """推奨ポートフォリオ"""
    included_policy_ids: List[str]
    expected_delta_yen: float
    portfolio_cas: float
    portfolio_risk: float
    portfolio_cvar_10: float  # CVaR (worst 10%)
    portfolio_roi: float
    diagnostics: PortfolioDiagnostics


class PortfolioSummaryResponse(BaseModel):
    """GET /api/v1/portfolio/summary レスポンス"""
    constraints: PortfolioConstraints
    recommended: PortfolioRecommended
    pareto_points: List[Dict[str, Any]]
    contribution: List[Dict[str, Any]]


class PortfolioContribution(BaseModel):
    """ポートフォリオ貢献度"""
    policy_id: str
    policy_name: str
    delta_yen: float
    contribution_pct: float


class ParetoFrontierPoint(BaseModel):
    """パレートフロンティア上の点"""
    portfolio_id: str
    risk: float
    delta_yen: float
    cas: float
    is_recommended: bool


class PortfolioPolicyItem(BaseModel):
    """GET /api/v1/portfolio/policies レスポンス項目"""
    id: str
    name: str
    dataset_name: str
    channel: Optional[str] = None
    segment: Optional[str] = None
    delta_yen: float
    roi: Optional[float] = None
    cas: Optional[float] = None
    risk: Optional[float] = None
    include: bool  # PortfolioFlag.include
    created_at: datetime


class PortfolioPoliciesResponse(BaseModel):
    """GET /api/v1/portfolio/policies レスポンス"""
    policies: List[PortfolioPolicyItem]
    total_count: int


class PortfolioIncludeRequest(BaseModel):
    """POST /api/v1/portfolio/policies/{policy_id}/include リクエスト"""
    include: bool


# ==================== 既存モデル（後方互換性のため残す） ====================

class PortfolioSummary(BaseModel):
    """推奨ポートフォリオ全体の集計値"""
    window: str  # "14d" | "28d" | "56d"
    expectedDeltaYen: float  # 推奨ポートフォリオの期待Δ¥
    totalCostYen: Optional[float] = None
    meanCas: float  # 0-1
    portfolioRisk: float  # 0-1
    roi: float  # x倍
    selectedPolicyIds: List[str]  # 採用されているPolicy IDs


class PortfolioPolicy(BaseModel):
    """ポートフォリオに含まれ得る個々の施策（Policy）"""
    id: str
    name: str
    datasetName: str
    channel: Optional[str] = "Multi-channel"
    segment: Optional[str] = None
    deltaYen: float
    roi: float
    risk: float
    cas: float
    verdict: Literal["include", "exclude", "test"]


class ParetoPoint(BaseModel):
    """フロンティア散布図の1点（1つの候補ポートフォリオ）"""
    portfolioId: str
    risk: float
    deltaYen: float
    meanCas: float
    isRecommended: bool


# ==================== Helpers ====================

def _safe_float(val, default=0.0) -> float:
    """Safely convert to float"""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _calculate_cvar(values: List[float], percentile: float = 0.1) -> float:
    """Calculate Conditional Value at Risk (CVaR)"""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    tail_count = max(1, math.ceil(len(sorted_vals) * percentile))
    tail = sorted_vals[:tail_count]
    tail_mean = sum(tail) / len(tail)
    return abs(tail_mean) if tail_mean < 0 else 0.0


def _calculate_risk_score(delta_yen: float, cas: float) -> float:
    """
    Calculate risk score from delta_yen and CAS
    Risk = (1 - CAS) * volatility_factor
    Range: 0-1
    """
    # Higher delta_yen -> potentially higher risk
    # Lower CAS -> higher risk
    volatility = min(abs(delta_yen) / 1000000, 0.5)  # Cap at 0.5
    cas_risk = 1 - cas
    return min((cas_risk * 0.7 + volatility * 0.3), 1.0)


def _is_pareto_efficient(point_idx: int, all_points: List[tuple]) -> bool:
    """
    Check if a point is Pareto efficient
    all_points: [(deltaYen, risk), ...]
    """
    delta_yen, risk = all_points[point_idx]
    for other_delta, other_risk in all_points:
        # Dominated if another point has higher profit AND lower risk
        if other_delta > delta_yen and other_risk < risk:
            return False
    return True


# ==================== 修正.pdf仕様準拠エンドポイント ====================

@router.get("/summary/v2", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary_v2(
    window: str = Query("28d", regex="^(14d|28d|56d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Portfolio Summary V2 (修正.pdf仕様準拠)

    推奨ポートフォリオの概要を返す
    - Policy Lab由来のポリシーのみ使用
    - PortfolioFlag.include に基づいて推奨ポートフォリオを構築
    - Pareto効率性を考慮

    パラメータ:
        window: 集計期間 (14d/28d/56d)

    レスポンス:
        - constraints: ポートフォリオ制約 (min_cas, max_risk)
        - recommended: 推奨ポートフォリオ情報
        - pareto_points: パレートフロンティア点
        - contribution: 貢献度ランキング (Top 5)
    """
    import uuid as uuid_lib

    try:
        tenant_id = uuid_lib.UUID("00000000-0000-0000-0000-000000000001")

        # Parse window
        window_days = int(window.replace("d", ""))
        cutoff_date = datetime.utcnow() - timedelta(days=window_days)

        # Query completed analyses with portfolio_include flag
        # 修正.pdf: Policy Lab由来のポリシーのみ使用 (policy_id IS NOT NULL)
        query = text("""
            SELECT
                a.id,
                a.policy_id,
                a.delta_yen,
                a.delta_yen_ci_low,
                a.delta_yen_ci_high,
                a.diagnostics_snapshot,
                a.impact_metrics,
                a.completed_at,
                p.name as policy_name,
                p.portfolio_include,
                p.channels,
                p.target_rule,
                d.name as dataset_name
            FROM analysis_runs a
            LEFT JOIN policies p ON a.policy_id = p.id AND a.tenant_id = p.tenant_id
            LEFT JOIN datasets d ON a.dataset_id = d.id AND a.tenant_id = d.tenant_id
            WHERE a.tenant_id = :tenant_id
            AND a.status = 'completed'
            AND a.delta_yen IS NOT NULL
            AND a.policy_id IS NOT NULL
            AND a.completed_at >= :cutoff_date
            ORDER BY a.completed_at DESC
        """)

        result = await db.execute(query, {
            "tenant_id": tenant_id,
            "cutoff_date": cutoff_date.replace(tzinfo=None)
        })
        rows = result.fetchall()

        if not rows:
            # Empty state
            return PortfolioSummaryResponse(
                constraints=PortfolioConstraints(),
                recommended=PortfolioRecommended(
                    included_policy_ids=[],
                    expected_delta_yen=0.0,
                    portfolio_cas=0.0,
                    portfolio_risk=0.0,
                    portfolio_cvar_10=0.0,
                    portfolio_roi=0.0,
                    diagnostics=PortfolioDiagnostics(
                        status="ok",
                        message="0件のポリシーから構成されています"
                    )
                ),
                pareto_points=[],
                contribution=[]
            )

        # Build policy records
        policies = []
        for row in rows:
            delta_yen = _safe_float(row[2])

            # Extract CAS from diagnostics_snapshot
            diagnostics = row[5] or {}
            cas = _safe_float(diagnostics.get("cas_score"), None) if isinstance(diagnostics, dict) else None

            # Calculate risk from CI
            risk = 0.0
            if row[3] is not None and row[4] is not None and delta_yen != 0:
                ci_width = abs(_safe_float(row[4]) - _safe_float(row[3]))
                risk = min(1.0, ci_width / abs(delta_yen))

            # Extract ROI from impact_metrics
            impact_metrics = row[6] or {}
            roi = 0.0
            if isinstance(impact_metrics, dict):
                cost = _safe_float(impact_metrics.get("estimated_cost"), 0.0)
                if cost > 0:
                    roi = delta_yen / cost

            portfolio_include = row[9] if row[9] is not None else False

            policies.append({
                "id": str(row[0]),
                "policy_id": str(row[1]) if row[1] else None,
                "delta_yen": delta_yen,
                "cas": cas,
                "risk": risk,
                "roi": roi,
                "portfolio_include": portfolio_include,
                "policy_name": row[8] or f"Policy {str(row[0])[:8]}",
                "dataset_name": row[12] or "Dataset"
            })

        # Filter eligible policies (meet constraints)
        constraints = PortfolioConstraints(min_cas=0.15, max_risk=0.6)
        eligible = [
            p for p in policies
            if (p["cas"] is None or p["cas"] >= constraints.min_cas)
            and p["risk"] <= constraints.max_risk
        ]

        if not eligible:
            # Relax constraints if no eligible policies
            eligible = policies

        # Select included policies (portfolio_include == true) or Pareto-efficient
        included = [p for p in eligible if p["portfolio_include"]]

        if not included:
            # Fallback: Select Pareto-efficient policies
            points = [(p["delta_yen"], p["risk"]) for p in eligible]
            pareto_indices = [i for i in range(len(eligible)) if _is_pareto_efficient(i, points)]

            if pareto_indices:
                # Select top 5 Pareto-efficient by delta_yen
                pareto_policies = [eligible[i] for i in pareto_indices]
                pareto_policies.sort(key=lambda x: x["delta_yen"], reverse=True)
                included = pareto_policies[:5]

        if not included:
            included = eligible[:1]  # At least one policy

        # Calculate portfolio metrics
        total_delta_yen = sum(p["delta_yen"] for p in included)
        delta_values = [p["delta_yen"] for p in included]
        cas_values = [p["cas"] for p in included if p["cas"] is not None]

        portfolio_cas = sum(cas_values) / len(cas_values) if cas_values else 0.0
        portfolio_risk = sum(p["risk"] * abs(p["delta_yen"]) for p in included) / sum(abs(p["delta_yen"]) for p in included) if included else 0.0

        # Calculate CVaR (worst 10%)
        sorted_deltas = sorted(delta_values)
        tail_count = max(1, math.ceil(len(sorted_deltas) * 0.1))
        tail = sorted_deltas[:tail_count]
        cvar = abs(sum(tail) / len(tail)) if tail and sum(tail) < 0 else 0.0

        # Calculate portfolio ROI
        total_cost = sum(abs(p["delta_yen"]) * 0.2 for p in included)  # Estimated cost
        portfolio_roi = total_delta_yen / total_cost if total_cost > 0 else 0.0

        # Build diagnostics
        violation_msgs = []
        if portfolio_cas < constraints.min_cas:
            violation_msgs.append(f"CAS {portfolio_cas:.2f} < min {constraints.min_cas}")
        if portfolio_risk > constraints.max_risk:
            violation_msgs.append(f"Risk {portfolio_risk:.2f} > max {constraints.max_risk}")

        diagnostics = PortfolioDiagnostics(
            status="constraint_violation" if violation_msgs else "ok",
            message="; ".join(violation_msgs) if violation_msgs else f"{len(included)}件のポリシーから構成されています"
        )

        # Build recommended
        included_ids = [p["policy_id"] or p["id"] for p in included]
        recommended = PortfolioRecommended(
            included_policy_ids=included_ids,
            expected_delta_yen=total_delta_yen,
            portfolio_cas=portfolio_cas,
            portfolio_risk=portfolio_risk,
            portfolio_cvar_10=cvar,
            portfolio_roi=portfolio_roi,
            diagnostics=diagnostics
        )

        # Build Pareto frontier points
        pareto_points = []
        for p in eligible:
            is_recommended = (p["policy_id"] or p["id"]) in included_ids
            pareto_points.append({
                "portfolio_id": p["policy_id"] or p["id"],
                "risk": p["risk"],
                "delta_yen": p["delta_yen"],
                "cas": p["cas"] if p["cas"] is not None else 0.0,
                "is_recommended": is_recommended
            })

        # Build contribution ranking (Top 5)
        included_sorted = sorted(included, key=lambda x: x["delta_yen"], reverse=True)[:5]
        contribution = []
        for p in included_sorted:
            contribution.append({
                "policy_id": p["policy_id"] or p["id"],
                "policy_name": p["policy_name"],
                "delta_yen": p["delta_yen"],
                "contribution_pct": (p["delta_yen"] / total_delta_yen * 100) if total_delta_yen > 0 else 0.0
            })

        logger.info(f"Portfolio summary v2: {len(included)} included policies, total_delta_yen={total_delta_yen:.2f}")

        return PortfolioSummaryResponse(
            constraints=constraints,
            recommended=recommended,
            pareto_points=pareto_points,
            contribution=contribution
        )

    except Exception as e:
        logger.error(f"Get portfolio summary v2 failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policies/v2", response_model=PortfolioPoliciesResponse)
async def get_portfolio_policies_v2(
    window: str = Query("28d", regex="^(14d|28d|56d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Portfolio Policies V2 (修正.pdf仕様準拠)

    全ポリシーのリストを返す (portfolio_include フラグ付き)

    パラメータ:
        window: 集計期間 (14d/28d/56d)

    レスポンス:
        - policies: ポリシーリスト
        - total_count: 総数
    """
    import uuid as uuid_lib

    try:
        tenant_id = uuid_lib.UUID("00000000-0000-0000-0000-000000000001")

        # Parse window
        window_days = int(window.replace("d", ""))
        cutoff_date = datetime.utcnow() - timedelta(days=window_days)

        # Query all completed analyses
        # 修正.pdf: Policy Lab由来のポリシーのみ使用 (policy_id IS NOT NULL)
        query = text("""
            SELECT
                a.id,
                a.policy_id,
                a.delta_yen,
                a.delta_yen_ci_low,
                a.delta_yen_ci_high,
                a.diagnostics_snapshot,
                a.impact_metrics,
                a.completed_at,
                a.created_at,
                p.name as policy_name,
                p.portfolio_include,
                p.channels,
                p.target_rule,
                d.name as dataset_name
            FROM analysis_runs a
            LEFT JOIN policies p ON a.policy_id = p.id AND a.tenant_id = p.tenant_id
            LEFT JOIN datasets d ON a.dataset_id = d.id AND a.tenant_id = d.tenant_id
            WHERE a.tenant_id = :tenant_id
            AND a.status = 'completed'
            AND a.delta_yen IS NOT NULL
            AND a.policy_id IS NOT NULL
            AND a.completed_at >= :cutoff_date
            ORDER BY a.delta_yen DESC
        """)

        result = await db.execute(query, {
            "tenant_id": tenant_id,
            "cutoff_date": cutoff_date.replace(tzinfo=None)
        })
        rows = result.fetchall()

        policies = []
        for row in rows:
            delta_yen = _safe_float(row[2])

            # Extract CAS
            diagnostics = row[5] or {}
            cas = _safe_float(diagnostics.get("cas_score"), None) if isinstance(diagnostics, dict) else None

            # Calculate risk
            risk = 0.0
            if row[3] is not None and row[4] is not None and delta_yen != 0:
                ci_width = abs(_safe_float(row[4]) - _safe_float(row[3]))
                risk = min(1.0, ci_width / abs(delta_yen))

            # Extract ROI
            impact_metrics = row[6] or {}
            roi = None
            if isinstance(impact_metrics, dict):
                cost = _safe_float(impact_metrics.get("estimated_cost"), 0.0)
                if cost > 0:
                    roi = delta_yen / cost

            # Extract channel
            channels = row[11]
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

            portfolio_include = row[10] if row[10] is not None else False
            policy_name = row[9] or row[13] or f"Policy {str(row[0])[:8]}"
            dataset_name = row[13] or "Dataset"

            policies.append(PortfolioPolicyItem(
                id=str(row[0]),
                name=policy_name,
                dataset_name=dataset_name,
                channel=channel,
                segment=row[12],
                delta_yen=delta_yen,
                roi=roi,
                cas=cas,
                risk=risk,
                include=portfolio_include,
                created_at=row[8] or datetime.utcnow().replace(tzinfo=None)
            ))

        logger.info(f"Portfolio policies v2: {len(policies)} policies for window={window}")

        return PortfolioPoliciesResponse(
            policies=policies,
            total_count=len(policies)
        )

    except Exception as e:
        logger.error(f"Get portfolio policies v2 failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/policies/{policy_id}/include")
async def toggle_portfolio_include(
    policy_id: str,
    request: PortfolioIncludeRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Toggle Portfolio Include Flag (修正.pdf仕様準拠)

    ポリシーのportfolio_includeフラグを更新

    パラメータ:
        policy_id: ポリシーID (analysis_run.id)
        request.include: true/false

    レスポンス:
        - success: bool
        - message: str
    """
    import uuid as uuid_lib

    try:
        tenant_id = uuid_lib.UUID("00000000-0000-0000-0000-000000000001")
        analysis_id = uuid_lib.UUID(policy_id)

        # Get the policy_id from analysis_run
        query_analysis = text("""
            SELECT policy_id
            FROM analysis_runs
            WHERE id = :analysis_id
            AND tenant_id = :tenant_id
        """)

        result = await db.execute(query_analysis, {
            "analysis_id": analysis_id,
            "tenant_id": tenant_id
        })
        row = result.fetchone()

        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Policy not found")

        actual_policy_id = row[0]

        # Update portfolio_include flag
        update_query = text("""
            UPDATE policies
            SET portfolio_include = :include
            WHERE id = :policy_id
            AND tenant_id = :tenant_id
        """)

        await db.execute(update_query, {
            "include": request.include,
            "policy_id": actual_policy_id,
            "tenant_id": tenant_id
        })
        await db.commit()

        action = "included in" if request.include else "excluded from"
        logger.info(f"Policy {policy_id} {action} portfolio")

        return {
            "success": True,
            "message": f"Policy {action} portfolio successfully"
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid policy ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Toggle portfolio include failed: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 既存エンドポイント（後方互換性のため残す） ====================

@router.get("/summary")
async def get_portfolio_summary(
    window: str = Query("28d", regex="^(14d|28d|56d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> PortfolioSummary:
    """
    Get portfolio summary（推奨ポートフォリオの概要）

    Returns:
        PortfolioSummary: 推奨ポートフォリオ全体の集計値
    """
    import uuid as uuid_lib

    try:
        tenant_id = uuid_lib.UUID("00000000-0000-0000-0000-000000000001")

        # Parse window
        window_days = int(window.replace("d", ""))
        cutoff_date = datetime.utcnow() - timedelta(days=window_days)

        # Get completed analyses with diagnostics
        query = text("""
            SELECT
                id,
                delta_yen,
                dataset_id,
                treatment_col,
                outcome_col,
                created_at,
                diagnostics_snapshot
            FROM analysis_runs
            WHERE tenant_id = :tenant_id
            AND status = 'completed'
            AND delta_yen IS NOT NULL
            AND created_at >= :cutoff_date
            ORDER BY created_at DESC
        """)
        result = await db.execute(query, {
            "tenant_id": tenant_id,
            "cutoff_date": cutoff_date
        })
        analyses = result.fetchall()

        if not analyses:
            # Empty state - no analyses
            return PortfolioSummary(
                window=window,
                expectedDeltaYen=0.0,
                totalCostYen=0.0,
                meanCas=0.0,
                portfolioRisk=0.0,
                roi=0.0,
                selectedPolicyIds=[]
            )

        # Build policy candidates
        policies = []
        for row in analyses:
            analysis_id = str(row[0])
            delta_yen = _safe_float(row[1])
            diagnostics_snapshot = row[6] or {}  # JSONB field

            # Extract CAS and risk from diagnostics_snapshot
            cas = _safe_float(diagnostics_snapshot.get("cas_score"), 0.75)
            risk = _calculate_risk_score(delta_yen, cas)

            policies.append({
                "id": analysis_id,
                "delta_yen": delta_yen,
                "cas": cas,
                "risk": risk,
                "cost": abs(delta_yen) * 0.2  # Estimated cost
            })

        # Select Pareto-efficient policies with constraints
        # Constraints: CAS >= 0.75, Risk <= 0.3
        eligible = [p for p in policies if p["cas"] >= 0.75 and p["risk"] <= 0.3]

        if not eligible:
            # Relax constraints if no eligible policies
            eligible = policies

        # Build Pareto frontier
        points = [(p["delta_yen"], p["risk"]) for p in eligible]
        pareto_indices = [i for i in range(len(eligible)) if _is_pareto_efficient(i, points)]

        if not pareto_indices:
            pareto_indices = [0]  # Fallback

        # Select top 3-5 Pareto-efficient policies
        pareto_policies = [eligible[i] for i in pareto_indices]
        pareto_policies.sort(key=lambda x: x["delta_yen"], reverse=True)
        selected = pareto_policies[:5]  # Top 5

        # Calculate portfolio metrics
        total_delta_yen = sum(p["delta_yen"] for p in selected)
        total_cost = sum(p["cost"] for p in selected)
        mean_cas = sum(p["cas"] * p["delta_yen"] for p in selected) / total_delta_yen if total_delta_yen > 0 else 0.0

        # Portfolio risk (weighted average)
        portfolio_risk = sum(p["risk"] * abs(p["delta_yen"]) for p in selected) / sum(abs(p["delta_yen"]) for p in selected) if selected else 0.0

        # ROI
        roi = total_delta_yen / total_cost if total_cost > 0 else 0.0

        selected_ids = [p["id"] for p in selected]

        logger.info(f"Portfolio summary: window={window}, selected={len(selected_ids)}, delta_yen={total_delta_yen:.2f}")

        return PortfolioSummary(
            window=window,
            expectedDeltaYen=total_delta_yen,
            totalCostYen=total_cost,
            meanCas=mean_cas,
            portfolioRisk=portfolio_risk,
            roi=roi,
            selectedPolicyIds=selected_ids
        )

    except Exception as e:
        logger.error(f"Get portfolio summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policies")
async def get_portfolio_policies(
    window: str = Query("28d", regex="^(14d|28d|56d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[PortfolioPolicy]:
    """
    Get portfolio policies list（施策一覧）

    Returns:
        List[PortfolioPolicy]: 全候補施策のリスト（verdict付き）
    """
    import uuid as uuid_lib

    try:
        tenant_id = uuid_lib.UUID("00000000-0000-0000-0000-000000000001")

        # Get summary first to determine selected policies
        summary = await get_portfolio_summary(window=window, db=db, current_user=current_user)
        selected_ids = set(summary.selectedPolicyIds)

        # Parse window
        window_days = int(window.replace("d", ""))
        cutoff_date = datetime.utcnow() - timedelta(days=window_days)

        # Get all completed analyses with diagnostics
        query = text("""
            SELECT
                a.id,
                a.delta_yen,
                a.dataset_id,
                a.treatment_col,
                a.outcome_col,
                d.name as dataset_name,
                a.diagnostics_snapshot
            FROM analysis_runs a
            LEFT JOIN datasets d ON a.dataset_id = d.id AND a.tenant_id = d.tenant_id
            WHERE a.tenant_id = :tenant_id
            AND a.status = 'completed'
            AND a.delta_yen IS NOT NULL
            AND a.created_at >= :cutoff_date
            ORDER BY a.delta_yen DESC
        """)
        result = await db.execute(query, {
            "tenant_id": tenant_id,
            "cutoff_date": cutoff_date
        })
        analyses = result.fetchall()

        if not analyses:
            return []

        # Build policy list
        policies = []
        for idx, row in enumerate(analyses):
            analysis_id = str(row[0])
            delta_yen = _safe_float(row[1])
            dataset_name = row[5] or f"Dataset {str(row[2])[:8]}"
            diagnostics_snapshot = row[6] or {}  # JSONB field

            # Extract CAS and risk from diagnostics_snapshot
            cas = _safe_float(diagnostics_snapshot.get("cas_score"), 0.75)
            risk = _calculate_risk_score(delta_yen, cas)
            cost = abs(delta_yen) * 0.2
            roi = delta_yen / cost if cost > 0 else 0.0

            # Determine verdict
            if analysis_id in selected_ids:
                verdict = "include"
            elif cas < 0.6 or risk > 0.4:
                verdict = "exclude"
            else:
                verdict = "test"

            policy = PortfolioPolicy(
                id=analysis_id,
                name=f"Policy {chr(65 + idx % 26)}{idx // 26 if idx >= 26 else ''}",
                datasetName=dataset_name,
                channel="Multi-channel",
                segment=f"Analysis {analysis_id[:8]}",
                deltaYen=delta_yen,
                roi=roi,
                risk=risk,
                cas=cas,
                verdict=verdict
            )
            policies.append(policy)

        logger.info(f"Portfolio policies: {len(policies)} policies for window={window}")
        return policies

    except Exception as e:
        logger.error(f"Get portfolio policies failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/frontier")
async def get_pareto_frontier(
    window: str = Query("28d", regex="^(14d|28d|56d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[ParetoPoint]:
    """
    Get Pareto frontier points（パレートフロンティア散布図データ）

    Returns:
        List[ParetoPoint]: フロンティア上の点のリスト
    """
    import uuid as uuid_lib

    try:
        tenant_id = uuid_lib.UUID("00000000-0000-0000-0000-000000000001")

        # Get summary to determine recommended portfolio
        summary = await get_portfolio_summary(window=window, db=db, current_user=current_user)
        selected_ids = set(summary.selectedPolicyIds)

        # Get policies
        policies = await get_portfolio_policies(window=window, db=db, current_user=current_user)

        if not policies:
            return []

        # Build portfolio points (for simplicity, each policy = 1 portfolio)
        # In real implementation, should consider combinations
        points = []
        for policy in policies:
            is_recommended = policy.id in selected_ids
            point = ParetoPoint(
                portfolioId=policy.id,
                risk=policy.risk,
                deltaYen=policy.deltaYen,
                meanCas=policy.cas,
                isRecommended=is_recommended
            )
            points.append(point)

        # Sort by delta_yen descending
        points.sort(key=lambda x: x.deltaYen, reverse=True)

        logger.info(f"Pareto frontier: {len(points)} points for window={window}")
        return points

    except Exception as e:
        logger.error(f"Get frontier failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
