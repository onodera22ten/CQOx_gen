"""V2 Module A API - Multi-Arm Causal Design"""
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, bindparam
from typing import List, Dict, Any
from uuid import uuid4
from pydantic import BaseModel
import numpy as np
import pandas as pd
import uuid as uuid_lib

from cqox.auth.dependencies import get_current_user
from cqox.database.connection import get_db
from cqox.database.models import Dataset
from cqox.engine.estimators.multi_arm_dr import MultiArmDREstimator, DoseResponseEstimator

router = APIRouter()
DEFAULT_TENANT_ID = uuid_lib.UUID("00000000-0000-0000-0000-000000000001")


class ExperimentCreate(BaseModel):
    experiment_name: str
    treatment_type: str  # 'binary' | 'multi_armed' | 'dose_response'
    dataset_id: str
    treatment_column: str
    outcome_column: str
    arms: List[Dict[str, Any]]  # [{"arm_id": 0, "label": "Control"}, ...]


class TreatmentArmResponse(BaseModel):
    arm_id: int
    label: str
    description: str | None = None
    delta_yen: float | None = None
    cas: float | None = None
    risk: float | None = None


class ExperimentResponse(BaseModel):
    id: str
    experiment_name: str
    treatment_type: str
    dataset_id: str | None = None
    treatment_column: str | None = None
    outcome_column: str | None = None
    status: str
    created_at: str | None = None
    arms: List[TreatmentArmResponse]


class AutoPayloadResponse(BaseModel):
    dataset_id: str
    treatment_column: str
    outcome_column: str
    feature_columns: List[str]
    row_count: int
    X: List[List[float]]
    T: List[float]
    Y: List[float]


MULTI_ARM_TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS multi_arm_experiments (
        id UUID PRIMARY KEY,
        tenant_id UUID NOT NULL,
        experiment_name VARCHAR(255) NOT NULL,
        treatment_type VARCHAR(50) NOT NULL,
        dataset_id UUID,
        treatment_column VARCHAR(255) NOT NULL,
        outcome_column VARCHAR(255) NOT NULL,
        status VARCHAR(50) NOT NULL DEFAULT 'draft',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        created_by UUID,
        metadata JSONB
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_multi_arm_experiments_tenant_id ON multi_arm_experiments(tenant_id)",
    "CREATE INDEX IF NOT EXISTS ix_multi_arm_experiments_status ON multi_arm_experiments(status)",
    """
    CREATE TABLE IF NOT EXISTS treatment_arms (
        id UUID PRIMARY KEY,
        experiment_id UUID NOT NULL REFERENCES multi_arm_experiments(id) ON DELETE CASCADE,
        arm_id INTEGER NOT NULL,
        arm_label VARCHAR(100) NOT NULL,
        arm_description TEXT,
        delta_yen NUMERIC(15, 2),
        cas NUMERIC(5, 4),
        risk NUMERIC(5, 4),
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_treatment_arms_experiment_id ON treatment_arms(experiment_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_treatment_arms_experiment_arm ON treatment_arms(experiment_id, arm_id)",
    """
    CREATE TABLE IF NOT EXISTS dose_response_configs (
        id UUID PRIMARY KEY,
        experiment_id UUID NOT NULL REFERENCES multi_arm_experiments(id) ON DELETE CASCADE,
        min_dose NUMERIC(10, 2) NOT NULL,
        max_dose NUMERIC(10, 2) NOT NULL,
        dose_unit VARCHAR(50),
        polynomial_degree INTEGER NOT NULL DEFAULT 2,
        curve_data JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_dose_response_configs_experiment_id ON dose_response_configs(experiment_id)"
]


async def _ensure_multi_arm_tables(db: AsyncSession) -> None:
    for stmt in MULTI_ARM_TABLE_STATEMENTS:
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


def _resolve_dataset_path(dataset_path: str) -> str:
    if not dataset_path:
        raise FileNotFoundError("Dataset path is empty")

    candidates = [
        dataset_path,
        os.path.join("/app/data/uploads", os.path.basename(dataset_path)),
        os.path.join("/home/hirokionodera/CQOx_gen/backend/data/uploads", os.path.basename(dataset_path)),
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    raise FileNotFoundError(f"Dataset file not found for path {dataset_path}")


def _load_dataset_for_experiment(path: str, limit: int = 2000) -> pd.DataFrame:
    _, ext = os.path.splitext(path.lower())

    if ext in {".parquet", ".pq"}:
        df = pd.read_parquet(path)
    elif ext in {".csv", ".txt"}:
        df = pd.read_csv(path)
    elif ext in {".json"}:
        df = pd.read_json(path)
    elif ext in {".xls", ".xlsx"}:
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    if len(df) > limit:
        df = df.head(limit)

    return df


@router.post("/experiments", response_model=ExperimentResponse)
async def create_experiment(
    experiment: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create multi-arm experiment"""
    await _ensure_multi_arm_tables(db)
    exp_id = str(uuid4())
    tenant_uuid = _resolve_tenant_uuid(current_user)
    dataset_row = await db.execute(
        text("""
            SELECT id, tenant_id, file_path
            FROM datasets
            WHERE id = :dataset_id AND tenant_id = :tenant_id
        """),
        {"dataset_id": experiment.dataset_id, "tenant_id": tenant_uuid}
    )
    dataset = dataset_row.fetchone()
    if not dataset or not dataset.file_path:
        raise HTTPException(status_code=404, detail="Dataset not found for tenant")

    await db.execute(
        text("""
            INSERT INTO multi_arm_experiments
            (id, tenant_id, dataset_id, experiment_name, treatment_type, treatment_column, outcome_column, status)
            VALUES (:id, :tenant_id, :dataset_id, :experiment_name, :treatment_type, :treatment_column, :outcome_column, 'draft')
        """),
        {
            "id": uuid_lib.UUID(exp_id),
            "tenant_id": tenant_uuid,
            "dataset_id": uuid_lib.UUID(experiment.dataset_id),
            "experiment_name": experiment.experiment_name,
            "treatment_type": experiment.treatment_type,
            "treatment_column": experiment.treatment_column,
            "outcome_column": experiment.outcome_column
        }
    )

    insert_arm_stmt = text("""
        INSERT INTO treatment_arms (id, experiment_id, arm_id, arm_label, arm_description)
        VALUES (:id, :experiment_id, :arm_id, :arm_label, :arm_description)
    """)

    for arm in experiment.arms:
        await db.execute(
            insert_arm_stmt,
            {
                "id": uuid_lib.uuid4(),
                "experiment_id": uuid_lib.UUID(exp_id),
                "arm_id": arm['arm_id'],
                "arm_label": arm['label'],
                "arm_description": arm.get("description")
            }
        )

    await db.commit()

    return ExperimentResponse(
        id=exp_id,
        experiment_name=experiment.experiment_name,
        treatment_type=experiment.treatment_type,
        dataset_id=experiment.dataset_id,
        treatment_column=experiment.treatment_column,
        outcome_column=experiment.outcome_column,
        status='draft',
        created_at=None,
        arms=[
            TreatmentArmResponse(
                arm_id=arm['arm_id'],
                label=arm['label'],
                description=arm.get("description"),
                delta_yen=None,
                cas=None,
                risk=None
            )
            for arm in experiment.arms
        ]
    )


@router.get("/experiments", response_model=List[ExperimentResponse])
async def list_experiments(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """List all experiments"""
    await _ensure_multi_arm_tables(db)
    tenant_uuid = _resolve_tenant_uuid(current_user)
    result = await db.execute(
        text("""
            SELECT id, dataset_id, experiment_name, treatment_type, treatment_column, outcome_column, status, created_at
            FROM multi_arm_experiments
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
        """),
        {"tenant_id": tenant_uuid}
    )
    experiments = result.fetchall()

    if not experiments:
        return []

    experiment_ids = [row[0] for row in experiments]
    arm_stmt = text("""
        SELECT experiment_id, arm_id, arm_label, arm_description, delta_yen, cas, risk
        FROM treatment_arms
        WHERE experiment_id IN :experiment_ids
        ORDER BY arm_id
    """).bindparams(bindparam("experiment_ids", expanding=True))
    arm_rows = await db.execute(arm_stmt, {"experiment_ids": tuple(experiment_ids)})

    arms_map: Dict[uuid_lib.UUID, List[TreatmentArmResponse]] = {}
    for row in arm_rows:
        exp_id, arm_id, label, description, delta, cas, risk = row
        arms_map.setdefault(exp_id, []).append(
            TreatmentArmResponse(
                arm_id=arm_id,
                label=label,
                description=description,
                delta_yen=float(delta) if delta is not None else None,
                cas=float(cas) if cas is not None else None,
                risk=float(risk) if risk is not None else None
            )
        )

    response: List[ExperimentResponse] = []
    for exp in experiments:
        exp_id, dataset_id, name, treatment_type, treatment_col, outcome_col, status, created_at = exp
        response.append(
            ExperimentResponse(
                id=str(exp_id),
                dataset_id=str(dataset_id) if dataset_id else None,
                experiment_name=name,
                treatment_type=treatment_type,
                treatment_column=treatment_col,
                outcome_column=outcome_col,
                status=status,
                created_at=created_at.isoformat() if created_at else None,
                arms=arms_map.get(exp_id, [])
            )
        )

    return response


@router.post("/experiments/{experiment_id}/analyze")
async def analyze_experiment(
    experiment_id: str,
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Analyze multi-arm experiment with DR estimator"""
    await _ensure_multi_arm_tables(db)
    X = np.array(data.get('X', []))
    T = np.array(data.get('T', []))
    Y = np.array(data.get('Y', []))

    if len(X) == 0 or len(T) == 0 or len(Y) == 0:
        raise HTTPException(400, "Missing data")

    estimator = MultiArmDREstimator()
    estimator.fit(X, T, Y)

    ate_results = estimator.estimate_ate(X, T, Y)

    # Update treatment_arms with results
    for arm_id, ate in ate_results.items():
        await db.execute(
            text("UPDATE treatment_arms SET delta_yen = :delta WHERE experiment_id = :experiment_id AND arm_id = :arm_id"),
            {
                "delta": ate,
                "experiment_id": uuid_lib.UUID(experiment_id),
                "arm_id": arm_id
            }
        )

    await db.commit()

    return {"ate_by_arm": ate_results}


@router.get("/experiments/{experiment_id}/auto-payload", response_model=AutoPayloadResponse)
async def generate_analysis_payload(
    experiment_id: str,
    limit: int = 2000,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Generate analysis payload from dataset columns"""
    await _ensure_multi_arm_tables(db)
    tenant_uuid = _resolve_tenant_uuid(current_user)
    result = await db.execute(
        text("""
            SELECT id, dataset_id, treatment_column, outcome_column
            FROM multi_arm_experiments
            WHERE id = :experiment_id AND tenant_id = :tenant_id
        """),
        {"experiment_id": uuid_lib.UUID(experiment_id), "tenant_id": tenant_uuid}
    )
    experiment = result.fetchone()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    dataset_result = await db.execute(
        text("SELECT id, tenant_id, file_path FROM datasets WHERE id = :dataset_id AND tenant_id = :tenant_id"),
        {"dataset_id": experiment.dataset_id, "tenant_id": tenant_uuid}
    )
    dataset = dataset_result.fetchone()
    if not dataset or not dataset.file_path:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        file_path = _resolve_dataset_path(dataset.file_path)
        df = _load_dataset_for_experiment(file_path, limit=limit)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=f"Failed to load dataset: {exc}") from exc

    treatment_col = experiment.treatment_column
    outcome_col = experiment.outcome_column

    if treatment_col not in df.columns or outcome_col not in df.columns:
        raise HTTPException(status_code=400, detail="Dataset missing treatment or outcome column")

    work_df = df.copy()
    # Convert categorical treatment to numeric codes if needed
    if not pd.api.types.is_numeric_dtype(work_df[treatment_col]):
        work_df[treatment_col] = pd.Categorical(work_df[treatment_col]).codes
    if not pd.api.types.is_numeric_dtype(work_df[outcome_col]):
        work_df[outcome_col] = pd.to_numeric(work_df[outcome_col], errors="coerce")

    numeric_cols = work_df.select_dtypes(include=["number"]).columns.tolist()
    feature_cols = [col for col in numeric_cols if col not in {treatment_col, outcome_col}]
    if not feature_cols:
        feature_cols = [col for col in work_df.columns if col not in {treatment_col, outcome_col}]

    feature_cols = feature_cols[: min(len(feature_cols), 25)]
    if not feature_cols:
        raise HTTPException(status_code=400, detail="No numeric feature columns available in dataset")
    feature_df = work_df[feature_cols].fillna(0)

    return AutoPayloadResponse(
        dataset_id=str(dataset.id),
        treatment_column=treatment_col,
        outcome_column=outcome_col,
        feature_columns=feature_cols,
        row_count=len(work_df),
        X=feature_df.values.tolist(),
        T=work_df[treatment_col].fillna(0).tolist(),
        Y=work_df[outcome_col].fillna(0).tolist()
    )
