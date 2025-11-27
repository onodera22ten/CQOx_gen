"""V2 Module D API - Risk & Governance"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import pandas as pd
import uuid as uuid_lib

from cqox.auth.dependencies import get_current_user
from cqox.database.connection import get_db
from cqox.database.models import DEFAULT_TENANT_ID, GovernanceRule, GovernanceViolation
from cqox.engine.governance.fairness import (
    FairnessChecker,
    DataQualityChecker,
    ComplianceChecker,
    Violation as EngineViolation
)

router = APIRouter()

DEFAULT_GOVERNANCE_RULES = [
    {
        "name": "Fairness Uplift Disparity",
        "description": "Absolute uplift disparity must remain within ±¥1,000 across protected attributes.",
        "rule_type": "fairness",
        "severity": "high",
        "action": "review",
        "threshold_value": 1000.0,
        "config": {"metric": "absolute_uplift_disparity"}
    },
    {
        "name": "Data Quality Gate",
        "description": "Minimum 100 samples per batch and no >5% extreme outliers.",
        "rule_type": "data_quality",
        "severity": "medium",
        "action": "warn",
        "threshold_value": 100.0,
        "config": {"min_samples": 100}
    },
    {
        "name": "Compliance Frequency Cap",
        "description": "Per-user exposure counts must stay below configured caps.",
        "rule_type": "compliance",
        "severity": "critical",
        "action": "block",
        "threshold_value": 10.0,
        "config": {"max_frequency": 10}
    }
]


class FairnessCheckRequest(BaseModel):
    data: List[Dict[str, Any]]  # [{"delta_yen": 100, "gender": "male"}, ...]
    sensitive_attributes: Dict[str, List[str]]  # {"gender": ["male", "female"], ...}
    threshold: float = 1000.0


class DataQualityRequest(BaseModel):
    data: List[Dict[str, Any]]
    min_samples: int = 100


class ComplianceRequest(BaseModel):
    user_exposures: Dict[str, int]
    max_frequency: int = 10


class GovernanceRuleModel(BaseModel):
    id: str
    name: str
    description: Optional[str]
    rule_type: str
    severity: str
    action: str
    threshold_value: Optional[float]
    config: Optional[Dict[str, Any]]
    is_active: bool


class GovernanceRuleResponse(BaseModel):
    rules: List[GovernanceRuleModel]


class ViolationResponse(BaseModel):
    violations: List[Dict[str, Any]]


GOVERNANCE_TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS governance_rules (
        id UUID PRIMARY KEY,
        tenant_id UUID NOT NULL,
        name VARCHAR(255) NOT NULL,
        rule_name VARCHAR(255),
        description TEXT,
        rule_type VARCHAR(50) NOT NULL,
        severity VARCHAR(32) DEFAULT 'medium',
        action VARCHAR(32) DEFAULT 'warn',
        threshold_value FLOAT,
        config JSONB,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_governance_rules_tenant ON governance_rules(tenant_id)",
    """
    CREATE TABLE IF NOT EXISTS governance_violations (
        id UUID PRIMARY KEY,
        tenant_id UUID NOT NULL,
        rule_id UUID REFERENCES governance_rules(id),
        violation_type VARCHAR(50) NOT NULL,
        severity VARCHAR(32) NOT NULL,
        details JSONB,
        status VARCHAR(32) DEFAULT 'open',
        detected_at TIMESTAMPTZ DEFAULT NOW(),
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_governance_violations_tenant ON governance_violations(tenant_id)",
    "CREATE INDEX IF NOT EXISTS idx_governance_violations_rule ON governance_violations(rule_id)"
]


async def _ensure_governance_tables(db: AsyncSession) -> None:
    for stmt in GOVERNANCE_TABLE_STATEMENTS:
        await db.execute(text(stmt))
    await db.execute(text("ALTER TABLE governance_rules ADD COLUMN IF NOT EXISTS name VARCHAR(255)"))
    await db.execute(text("ALTER TABLE governance_rules ADD COLUMN IF NOT EXISTS rule_name VARCHAR(255)"))
    await db.execute(text("ALTER TABLE governance_rules ADD COLUMN IF NOT EXISTS description TEXT"))
    await db.execute(text("ALTER TABLE governance_rules ADD COLUMN IF NOT EXISTS rule_type VARCHAR(50)"))
    await db.execute(text("ALTER TABLE governance_rules ADD COLUMN IF NOT EXISTS severity VARCHAR(32) DEFAULT 'medium'"))
    await db.execute(text("ALTER TABLE governance_rules ADD COLUMN IF NOT EXISTS action VARCHAR(32) DEFAULT 'warn'"))
    await db.execute(text("ALTER TABLE governance_rules ADD COLUMN IF NOT EXISTS threshold_value FLOAT"))
    await db.execute(text("ALTER TABLE governance_rules ADD COLUMN IF NOT EXISTS config JSON"))
    await db.execute(text("ALTER TABLE governance_rules ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
    await db.execute(text("ALTER TABLE governance_rules ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()"))
    await db.execute(text("ALTER TABLE governance_rules ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()"))

    await db.execute(text("ALTER TABLE governance_violations ADD COLUMN IF NOT EXISTS violation_type VARCHAR(50)"))
    await db.execute(text("ALTER TABLE governance_violations ADD COLUMN IF NOT EXISTS severity VARCHAR(32)"))
    await db.execute(text("ALTER TABLE governance_violations ADD COLUMN IF NOT EXISTS details JSON"))
    await db.execute(text("ALTER TABLE governance_violations ADD COLUMN IF NOT EXISTS status VARCHAR(32) DEFAULT 'open'"))
    await db.execute(text("ALTER TABLE governance_violations ADD COLUMN IF NOT EXISTS detected_at TIMESTAMPTZ DEFAULT NOW()"))
    await db.execute(text("ALTER TABLE governance_violations ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()"))
    await db.commit()


def _resolve_tenant_id(current_user: Any) -> uuid_lib.UUID:
    """Normalize tenant ID from TokenData/dict into UUID."""
    candidate = None
    if isinstance(current_user, dict):
        candidate = current_user.get("tenant_id")
    else:
        candidate = getattr(current_user, "tenant_id", None)

    if not candidate:
        return DEFAULT_TENANT_ID

    try:
        return uuid_lib.UUID(str(candidate))
    except (ValueError, TypeError):
        return DEFAULT_TENANT_ID


def _serialize_violation(violation: EngineViolation) -> Dict[str, Any]:
    severity = getattr(violation.severity, "value", violation.severity)
    return {
        "rule_id": violation.rule_id,
        "type": violation.violation_type,
        "severity": severity,
        "details": violation.details,
        "affected_groups": violation.affected_groups
    }


def _serialize_violation_record(record: GovernanceViolation) -> Dict[str, Any]:
    return {
        "id": str(record.id),
        "rule_id": str(record.rule_id) if record.rule_id else None,
        "type": record.violation_type,
        "severity": record.severity,
        "details": record.details,
        "created_at": record.created_at.isoformat() if record.created_at else None
    }


async def _ensure_default_rules(db: AsyncSession, tenant_id: uuid_lib.UUID) -> List[GovernanceRule]:
    """Seed default rules if tenant has none."""
    await _ensure_governance_tables(db)
    result = await db.execute(
        select(GovernanceRule).where(
            GovernanceRule.tenant_id == tenant_id
        )
    )
    rules = result.scalars().all()
    if rules:
        return rules

    for rule in DEFAULT_GOVERNANCE_RULES:
        payload = {**rule}
        payload.setdefault("rule_name", rule["name"])
        db.add(GovernanceRule(tenant_id=tenant_id, **payload))

    await db.flush()

    result = await db.execute(
        select(GovernanceRule).where(GovernanceRule.tenant_id == tenant_id)
    )
    return result.scalars().all()


async def _log_violations(
    db: AsyncSession,
    tenant_id: uuid_lib.UUID,
    violations: List[EngineViolation],
    rule_type: str
) -> None:
    """Persist violations to governance_violations."""
    if not violations:
        return

    result = await db.execute(
        select(GovernanceRule).where(
            GovernanceRule.tenant_id == tenant_id,
            GovernanceRule.rule_type == rule_type,
            GovernanceRule.is_active.is_(True)
        )
    )
    rule = result.scalars().first()

    for violation in violations:
        severity = getattr(violation.severity, "value", violation.severity)
        db.add(
            GovernanceViolation(
                tenant_id=tenant_id,
                rule_id=rule.id if rule else None,
                violation_type=violation.violation_type,
                severity=severity,
                details=violation.details
            )
        )

    await db.flush()


@router.post("/check/fairness", response_model=ViolationResponse)
async def check_fairness(
    request: FairnessCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Check fairness violations"""
    await _ensure_governance_tables(db)
    df = pd.DataFrame(request.data)

    checker = FairnessChecker(threshold=request.threshold)
    violations = checker.check_multiple_attributes(df, request.sensitive_attributes)

    tenant_id = _resolve_tenant_id(current_user)
    await _log_violations(db, tenant_id, violations, "fairness")

    return ViolationResponse(
        violations=[_serialize_violation(v) for v in violations]
    )


@router.post("/check/data-quality", response_model=ViolationResponse)
async def check_data_quality(
    request: DataQualityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Check data quality"""
    await _ensure_governance_tables(db)
    df = pd.DataFrame(request.data)

    checker = DataQualityChecker()

    violations: List[EngineViolation] = []

    sample_violation = checker.check_sample_size(df, request.min_samples)
    if sample_violation:
        violations.append(sample_violation)

    numeric_columns = df.select_dtypes(include=["float64", "int64", "number"]).columns
    for col in numeric_columns:
        outlier_violation = checker.check_outliers(df, col)
        if outlier_violation:
            violations.append(outlier_violation)

    tenant_id = _resolve_tenant_id(current_user)
    await _log_violations(db, tenant_id, violations, "data_quality")

    return ViolationResponse(
        violations=[_serialize_violation(v) for v in violations]
    )


@router.post("/check/compliance", response_model=ViolationResponse)
async def check_compliance(
    request: ComplianceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Check compliance (frequency cap)"""
    await _ensure_governance_tables(db)
    checker = ComplianceChecker()

    violations = checker.check_frequency_cap(request.user_exposures, request.max_frequency)

    tenant_id = _resolve_tenant_id(current_user)
    await _log_violations(db, tenant_id, violations, "compliance")

    return ViolationResponse(
        violations=[_serialize_violation(v) for v in violations]
    )


@router.get("/rules", response_model=GovernanceRuleResponse)
async def list_rules(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List governance rules for current tenant (auto-seeded)."""
    await _ensure_governance_tables(db)
    tenant_id = _resolve_tenant_id(current_user)
    rules = await _ensure_default_rules(db, tenant_id)

    return GovernanceRuleResponse(
        rules=[
            GovernanceRuleModel(
                id=str(rule.id),
                name=rule.name,
                description=rule.description,
                rule_type=rule.rule_type,
                severity=rule.severity,
                action=rule.action,
                threshold_value=rule.threshold_value,
                config=rule.config,
                is_active=rule.is_active
            )
            for rule in rules
        ]
    )


@router.get("/violations")
async def list_violations(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all governance violations"""
    await _ensure_governance_tables(db)
    tenant_id = _resolve_tenant_id(current_user)
    result = await db.execute(
        select(GovernanceViolation)
        .where(GovernanceViolation.tenant_id == tenant_id)
        .order_by(GovernanceViolation.created_at.desc())
        .limit(100)
    )
    violations = result.scalars().all()

    return {
        "violations": [_serialize_violation_record(v) for v in violations]
    }
