"""V2 Module B API - Experiment Orchestrator & Bandit"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any, Literal, Any
from uuid import uuid4
from pydantic import BaseModel
import uuid as uuid_lib

from cqox.auth.dependencies import get_current_user
from cqox.database.connection import get_db
from cqox.engine.bandits.thompson import BernoulliThompsonBandit

router = APIRouter()
DEFAULT_TENANT_ID = uuid_lib.UUID("00000000-0000-0000-0000-000000000001")

class ExperimentCreate(BaseModel):
    experiment_name: str
    target_metric: str
    arms: List[str]


class OrchestratorExperiment(BaseModel):
    id: str
    experiment_name: str
    target_metric: str
    status: str
    created_at: str | None = None


class AllocationResponse(BaseModel):
    experiment_id: str
    allocations: Dict[str, float]


class OutcomeItem(BaseModel):
    arm_id: str
    reward: float


class OutcomeUpdateRequest(BaseModel):
    outcomes: List[OutcomeItem]
    reward_type: Literal["binary", "continuous"] = "binary"


BANDIT_TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS experiments (
        id UUID PRIMARY KEY,
        tenant_id UUID NOT NULL,
        experiment_name VARCHAR(255) NOT NULL,
        target_metric VARCHAR(255),
        status VARCHAR(50) NOT NULL DEFAULT 'running',
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_experiments_tenant_id ON experiments(tenant_id)",
    """
    CREATE TABLE IF NOT EXISTS experiment_allocations (
        id UUID PRIMARY KEY,
        experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
        arm_id VARCHAR(255) NOT NULL,
        alpha FLOAT DEFAULT 1.0,
        beta FLOAT DEFAULT 1.0,
        allocation_rate FLOAT DEFAULT 0.0,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_experiment_allocations_experiment_id ON experiment_allocations(experiment_id)"
]


async def _ensure_bandit_tables(db: AsyncSession) -> None:
    for stmt in BANDIT_TABLE_STATEMENTS:
        await db.execute(text(stmt))
    await db.commit()


def _resolve_tenant_uuid(current_user: Any) -> uuid_lib.UUID:
    if isinstance(current_user, dict):
        tenant_candidate = current_user.get("tenant_id")
    else:
        tenant_candidate = getattr(current_user, "tenant_id", None)

    if not tenant_candidate:
        return DEFAULT_TENANT_ID

    try:
        return uuid_lib.UUID(str(tenant_candidate))
    except Exception:
        return DEFAULT_TENANT_ID

@router.post("", response_model=OrchestratorExperiment)
async def create_experiment(
    experiment: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    await _ensure_bandit_tables(db)
    exp_id = str(uuid4())
    tenant_uuid = _resolve_tenant_uuid(current_user)
    await db.execute(
        text("INSERT INTO experiments (id, tenant_id, experiment_name, target_metric, status) VALUES (:id, :tenant_id, :name, :metric, 'running')"),
        {
            "id": uuid_lib.UUID(exp_id),
            "tenant_id": tenant_uuid,
            "name": experiment.experiment_name,
            "metric": experiment.target_metric
        }
    )
    insert_allocation = text("""
        INSERT INTO experiment_allocations (id, experiment_id, arm_id, allocation_rate)
        VALUES (:id, :experiment_id, :arm_id, :allocation_rate)
    """)
    for arm in experiment.arms:
        await db.execute(
            insert_allocation,
            {
                "id": uuid_lib.uuid4(),
                "experiment_id": uuid_lib.UUID(exp_id),
                "arm_id": arm,
                "allocation_rate": 1.0 / len(experiment.arms)
            }
        )
    await db.commit()
    return OrchestratorExperiment(
        id=exp_id,
        experiment_name=experiment.experiment_name,
        target_metric=experiment.target_metric,
        status="running"
    )


@router.get("", response_model=List[OrchestratorExperiment])
async def list_experiments(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    await _ensure_bandit_tables(db)
    tenant_uuid = _resolve_tenant_uuid(current_user)
    result = await db.execute(
        text("SELECT id, experiment_name, target_metric, status, created_at FROM experiments WHERE tenant_id = :tenant_id ORDER BY created_at DESC"),
        {"tenant_id": tenant_uuid}
    )
    rows = result.fetchall()
    return [
        OrchestratorExperiment(
            id=str(row[0]),
            experiment_name=row[1],
            target_metric=row[2],
            status=row[3],
            created_at=row[4].isoformat() if row[4] else None
        )
        for row in rows
    ]

@router.get("/{experiment_id}/allocation", response_model=AllocationResponse)
async def get_allocation(
    experiment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    await _ensure_bandit_tables(db)
    result = await db.execute(
        text("SELECT arm_id, alpha, beta FROM experiment_allocations WHERE experiment_id = :experiment_id"),
        {"experiment_id": uuid_lib.UUID(experiment_id)}
    )
    arms_data = result.fetchall()
    if not arms_data:
        raise HTTPException(404, "Not found")
    arm_ids = [row[0] for row in arms_data]
    bandit = BernoulliThompsonBandit(arm_ids)
    for row in arms_data:
        arm_id, alpha, beta = row
        bandit.state[arm_id].alpha = float(alpha)
        bandit.state[arm_id].beta = float(beta)
    allocations = bandit.sample_allocation()
    return AllocationResponse(experiment_id=experiment_id, allocations=allocations)


@router.post("/{experiment_id}/update", response_model=AllocationResponse)
async def update_experiment_allocation(
    experiment_id: str,
    request: OutcomeUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    await _ensure_bandit_tables(db)
    result = await db.execute(
        text("SELECT arm_id, alpha, beta FROM experiment_allocations WHERE experiment_id = :experiment_id"),
        {"experiment_id": uuid_lib.UUID(experiment_id)}
    )
    arms_data = result.fetchall()
    if not arms_data:
        raise HTTPException(404, "Not found")

    arm_ids = [row[0] for row in arms_data]
    bandit = BernoulliThompsonBandit(arm_ids)

    for row in arms_data:
        arm_id, alpha, beta = row
        bandit.state[arm_id].alpha = float(alpha)
        bandit.state[arm_id].beta = float(beta)

    outcomes = [(item.arm_id, int(item.reward > 0)) for item in request.outcomes]
    bandit.update(outcomes)
    allocations = bandit.sample_allocation()

    update_stmt = text("""
        UPDATE experiment_allocations
        SET alpha = :alpha,
            beta = :beta,
            allocation_rate = :allocation
        WHERE experiment_id = :experiment_id AND arm_id = :arm_id
    """)
    for arm_id, state in bandit.state.items():
        allocation_rate = allocations.get(arm_id, 0.0)
        await db.execute(
            update_stmt,
            {
                "alpha": state.alpha,
                "beta": state.beta,
                "allocation": allocation_rate,
                "experiment_id": uuid_lib.UUID(experiment_id),
                "arm_id": arm_id
            }
        )

    await db.commit()
    return AllocationResponse(experiment_id=experiment_id, allocations=allocations)
