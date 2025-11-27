"""
Policy Lab API - v2
Offline policy learning, optimization, and evaluation
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from datetime import datetime
import uuid
import logging
import pandas as pd
import numpy as np

from cqox.models.v2 import (
    PolicyConfig,
    OfflinePolicyRun,
    FrontierPoint,
    CreatePolicyRequest,
    OfflinePolicyLearnRequest,
    PolicyType,
    ObjectiveType,
    RiskMetric,
    OPEMethod
)
from cqox.ml.offline_policy_learning import (
    OffPolicyEvaluator,
    PolicyOptimizer,
    ThresholdPolicy,
    LinearScorePolicy
)
from cqox.auth.dependencies import get_current_user, get_tenant_id
from cqox.database.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policies", tags=["policies"])

# Default tenant ID
DEFAULT_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("", response_model=PolicyConfig, status_code=201)
async def create_policy(
    request: CreatePolicyRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new policy configuration

    Creates a policy configuration for treatment assignment. The policy can be:
    - threshold: Treat if feature > threshold
    - linear: Treat if linear combination > threshold
    - custom: Custom policy logic

    The policy is saved in draft status and can be optimized using offline learning.
    """
    try:
        policy_id = str(uuid.uuid4())
        tenant_uuid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
        now = datetime.utcnow()

        # Store in policies table (v1 table, but with v2 fields in config JSONB)
        await db.execute(
            text("""
                INSERT INTO policies (id, name, description, policy_type, objective, status, config, tenant_id, created_at, updated_at)
                VALUES (:id, :name, :description, :policy_type, :objective, :status, :config, :tenant_id, :created_at, :updated_at)
            """),
            {
                "id": uuid.UUID(policy_id),
                "name": request.name,
                "description": request.description,
                "policy_type": request.policy_type.value if hasattr(request.policy_type, 'value') else str(request.policy_type),
                "objective": request.objective.value if hasattr(request.objective, 'value') else str(request.objective) if request.objective else None,
                "status": "draft",
                "config": json.dumps({
                    "treatment_variable": request.treatment_variable,
                    "outcome_variable": request.outcome_variable,
                    "features": request.features,
                    "threshold": request.threshold,
                    "budget_constraint": request.budget_constraint,
                    "coverage_constraint": request.coverage_constraint,
                    "dataset_id": request.dataset_id,
                    "model_id": request.model_id,
                    "created_by": current_user.get("user_id")
                }),
                "tenant_id": tenant_uuid,
                "created_at": now,
                "updated_at": now
            }
        )
        await db.commit()

        # Create PolicyConfig response object
        policy = PolicyConfig(
            id=policy_id,
            tenant_id=tenant_id,
            name=request.name,
            description=request.description,
            policy_type=request.policy_type,
            treatment_variable=request.treatment_variable,
            outcome_variable=request.outcome_variable,
            features=request.features,
            threshold=request.threshold,
            budget_constraint=request.budget_constraint,
            coverage_constraint=request.coverage_constraint,
            dataset_id=request.dataset_id,
            model_id=request.model_id,
            created_at=now,
            updated_at=now,
            created_by=current_user.get("user_id"),
            status="draft"
        )

        logger.info(f"Created policy {policy_id} for tenant {tenant_id}")

        return policy

    except Exception as e:
        logger.error(f"Error creating policy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{policy_id}", response_model=PolicyConfig)
async def get_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get policy configuration by ID"""
    try:
        tenant_uuid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
        
        result = await db.execute(
            text("""
                SELECT id, name, description, policy_type, objective, status, config, tenant_id, created_at, updated_at
                FROM policies
                WHERE id = :policy_id AND tenant_id = :tenant_id
            """),
            {
                "policy_id": uuid.UUID(policy_id),
                "tenant_id": tenant_uuid
            }
        )
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Policy not found")

        config = json.loads(row[6]) if row[6] else {}
        
        policy = PolicyConfig(
            id=str(row[0]),
            tenant_id=str(row[7]),
            name=row[1],
            description=row[2],
            policy_type=PolicyType(row[3]) if row[3] else PolicyType.THRESHOLD,
            treatment_variable=config.get("treatment_variable"),
            outcome_variable=config.get("outcome_variable"),
            features=config.get("features", []),
            threshold=config.get("threshold"),
            budget_constraint=config.get("budget_constraint"),
            coverage_constraint=config.get("coverage_constraint"),
            dataset_id=config.get("dataset_id"),
            model_id=config.get("model_id"),
            created_at=row[8],
            updated_at=row[9],
            created_by=config.get("created_by"),
            status=row[5] or "draft"
        )

        return policy
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting policy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[PolicyConfig])
async def list_policies(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    dataset_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List all policies for the current tenant

    Supports filtering by status and dataset_id.
    """
    try:
        tenant_uuid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
        
        query = """
            SELECT id, name, description, policy_type, objective, status, config, tenant_id, created_at, updated_at
            FROM policies
            WHERE tenant_id = :tenant_id
        """
        params = {"tenant_id": tenant_uuid}
        
        if status:
            query += " AND status = :status"
            params["status"] = status

        if dataset_id:
            query += " AND config->>'dataset_id' = :dataset_id"
            params["dataset_id"] = dataset_id
        
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        
        result = await db.execute(text(query), params)
        rows = result.fetchall()
        
        policies = []
        for row in rows:
            config = json.loads(row[6]) if row[6] else {}
            policies.append(PolicyConfig(
                id=str(row[0]),
                tenant_id=str(row[7]),
                name=row[1],
                description=row[2],
                policy_type=PolicyType(row[3]) if row[3] else PolicyType.THRESHOLD,
                treatment_variable=config.get("treatment_variable"),
                outcome_variable=config.get("outcome_variable"),
                features=config.get("features", []),
                threshold=config.get("threshold"),
                budget_constraint=config.get("budget_constraint"),
                coverage_constraint=config.get("coverage_constraint"),
                dataset_id=config.get("dataset_id"),
                model_id=config.get("model_id"),
                created_at=row[8],
                updated_at=row[9],
                created_by=config.get("created_by"),
                status=row[5] or "draft"
            ))
        
        return policies
        
    except Exception as e:
        logger.error(f"Error listing policies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{policy_id}/offline-learn", response_model=OfflinePolicyRun, status_code=202)
async def run_offline_policy_learning(
    policy_id: str,
    request: OfflinePolicyLearnRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """
    Run offline policy learning to optimize policy parameters

    This endpoint starts an async job to:
    1. Load historical data from the policy's dataset
    2. Train/load propensity and outcome models
    3. Evaluate candidate policies using Off-Policy Evaluation (OPE)
    4. Compute Pareto frontier of (expected_value, risk)
    5. Select best policy based on risk aversion

    The job runs in the background and returns immediately with a run ID.
    Use GET /policies/runs/{run_id} to check status and results.

    OPE Methods:
    - DR: Doubly Robust (recommended, unbiased if either model is correct)
    - IPW: Inverse Propensity Weighting (requires good propensity model)
    - DM: Direct Method (requires good outcome model)
    """
    try:
        tenant_uuid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
        
        # Check policy exists
        policy_result = await db.execute(
            text("SELECT id, config FROM policies WHERE id = :policy_id AND tenant_id = :tenant_id"),
            {"policy_id": uuid.UUID(policy_id), "tenant_id": tenant_uuid}
        )
        policy_row = policy_result.fetchone()
        
        if not policy_row:
            raise HTTPException(status_code=404, detail="Policy not found")

        policy_config = json.loads(policy_row[1]) if policy_row[1] else {}
        dataset_id = policy_config.get("dataset_id")
        
        run_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Insert into database
        await db.execute(
            text("""
                INSERT INTO offline_policy_runs (
                    id, tenant_id, policy_config_id, objective, risk_metric, ope_method,
                    risk_aversion, dataset_id, propensity_model_id, outcome_model_id,
                    n_candidates, n_bootstrap, status, created_at
                )
                VALUES (
                    :id, :tenant_id, :policy_config_id, :objective, :risk_metric, :ope_method,
                    :risk_aversion, :dataset_id, :propensity_model_id, :outcome_model_id,
                    :n_candidates, :n_bootstrap, :status, :created_at
                )
            """),
            {
                "id": uuid.UUID(run_id),
                "tenant_id": tenant_uuid,
                "policy_config_id": uuid.UUID(policy_id),
                "objective": request.objective.value if hasattr(request.objective, 'value') else str(request.objective),
                "risk_metric": request.risk_metric.value if hasattr(request.risk_metric, 'value') else str(request.risk_metric),
                "ope_method": request.ope_method.value if hasattr(request.ope_method, 'value') else str(request.ope_method),
                "risk_aversion": request.risk_aversion,
                "dataset_id": uuid.UUID(dataset_id) if dataset_id else None,
                "propensity_model_id": uuid.UUID(request.propensity_model_id) if request.propensity_model_id else None,
                "outcome_model_id": uuid.UUID(request.outcome_model_id) if request.outcome_model_id else None,
                "n_candidates": request.n_candidates,
                "n_bootstrap": request.n_bootstrap,
                "status": "pending",
                "created_at": now
            }
        )
        await db.commit()

        run = OfflinePolicyRun(
            id=run_id,
            tenant_id=tenant_id,
            policy_config_id=policy_id,
            objective=request.objective,
            risk_metric=request.risk_metric,
            ope_method=request.ope_method,
            risk_aversion=request.risk_aversion,
            dataset_id=dataset_id,
            propensity_model_id=request.propensity_model_id,
            outcome_model_id=request.outcome_model_id,
            n_candidates=request.n_candidates,
            n_bootstrap=request.n_bootstrap,
            status="pending",
            created_at=now
        )

        # Queue background task (use Celery in production, BackgroundTasks for demo)
        background_tasks.add_task(
            execute_offline_learning_task,
            run_id=run_id,
            policy_id=policy_id
        )

        logger.info(f"Started offline learning run {run_id} for policy {policy_id}")

        return run

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting offline learning: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}", response_model=OfflinePolicyRun)
async def get_policy_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """
    Get status and results of an offline learning run

    Returns the run object with:
    - status: pending, running, completed, failed
    - frontier: Pareto frontier points (if completed)
    - best_policy: Recommended policy configuration
    - evaluation metrics: estimated value, risk, confidence intervals
    """
    try:
        tenant_uuid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
        
        result = await db.execute(
            text("""
                SELECT id, tenant_id, policy_config_id, objective, risk_metric, ope_method,
                       risk_aversion, dataset_id, propensity_model_id, outcome_model_id,
                       n_candidates, n_bootstrap, status, frontier, best_policy,
                       evaluation_metrics, error_message, created_at, started_at, completed_at
                FROM offline_policy_runs
                WHERE id = :run_id AND tenant_id = :tenant_id
            """),
            {
                "run_id": uuid.UUID(run_id),
                "tenant_id": tenant_uuid
            }
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Run not found")

        # Parse JSONB fields
        frontier = json.loads(row[13]) if row[13] else None
        best_policy = json.loads(row[14]) if row[14] else None
        evaluation_metrics = json.loads(row[15]) if row[15] else None
        
        run = OfflinePolicyRun(
            id=str(row[0]),
            tenant_id=str(row[1]),
            policy_config_id=str(row[2]),
            objective=ObjectiveType(row[3]) if row[3] else None,
            risk_metric=RiskMetric(row[4]) if row[4] else None,
            ope_method=OPEMethod(row[5]) if row[5] else None,
            risk_aversion=float(row[6]) if row[6] else 0.5,
            dataset_id=str(row[7]) if row[7] else None,
            propensity_model_id=str(row[8]) if row[8] else None,
            outcome_model_id=str(row[9]) if row[9] else None,
            n_candidates=int(row[10]) if row[10] else 100,
            n_bootstrap=int(row[11]) if row[11] else 100,
            status=row[12] or "pending",
            frontier=frontier,
            best_policy=best_policy,
            evaluation_metrics=evaluation_metrics,
            error_message=row[16],
            created_at=row[17],
            started_at=row[18],
            completed_at=row[19]
        )

    return run
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting policy run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Delete a policy configuration"""
    try:
        tenant_uuid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
        
        # Check if policy exists
        policy_result = await db.execute(
            text("SELECT id FROM policies WHERE id = :policy_id AND tenant_id = :tenant_id"),
            {"policy_id": uuid.UUID(policy_id), "tenant_id": tenant_uuid}
        )
        if not policy_result.fetchone():
        raise HTTPException(status_code=404, detail="Policy not found")

    # Check if policy is in use
        active_runs_result = await db.execute(
            text("""
                SELECT COUNT(*) FROM offline_policy_runs
                WHERE policy_config_id = :policy_id
                AND status IN ('pending', 'running')
            """),
            {"policy_id": uuid.UUID(policy_id)}
        )
        active_count = active_runs_result.scalar()
        
        if active_count > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete policy with active learning runs"
        )

        # Delete policy
        await db.execute(
            text("DELETE FROM policies WHERE id = :policy_id AND tenant_id = :tenant_id"),
            {"policy_id": uuid.UUID(policy_id), "tenant_id": tenant_uuid}
        )
        await db.commit()

    logger.info(f"Deleted policy {policy_id}")

    return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting policy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Background task wrapper
async def execute_offline_learning_task(run_id: str, policy_id: str):
    """Wrapper for background task"""
    from cqox.database.connection import async_session_factory
    async with async_session_factory() as session:
        await execute_offline_learning(run_id, policy_id, session)


# Background task for offline learning
async def execute_offline_learning(run_id: str, policy_id: str, db: AsyncSession):
    """
    Execute offline policy learning in background

    This is a simplified demo implementation.
    In production, this should be a Celery task with:
    - Proper database transactions
    - Model loading from S3/model registry
    - Dataset loading from data warehouse
    - Progress tracking
    - Error handling and retries
    """
    from cqox.database.connection import async_session_factory
    
    async with async_session_factory() as session:
    try:
            # Update status to running
            await session.execute(
                text("""
                    UPDATE offline_policy_runs
                    SET status = 'running', started_at = NOW()
                    WHERE id = :run_id
                """),
                {"run_id": uuid.UUID(run_id)}
            )
            await session.commit()

        logger.info(f"Executing offline learning for run {run_id}")

            # Get policy and run details
            policy_result = await session.execute(
                text("SELECT config FROM policies WHERE id = :policy_id"),
                {"policy_id": uuid.UUID(policy_id)}
            )
            policy_row = policy_result.fetchone()
            if not policy_row:
                raise ValueError(f"Policy {policy_id} not found")
            
            policy_config = json.loads(policy_row[0]) if policy_row[0] else {}
            features = policy_config.get("features", [])
            
            run_result = await session.execute(
                text("SELECT ope_method, risk_metric, risk_aversion, n_candidates FROM offline_policy_runs WHERE id = :run_id"),
                {"run_id": uuid.UUID(run_id)}
            )
            run_row = run_result.fetchone()
            if not run_row:
                raise ValueError(f"Run {run_id} not found")
            
            ope_method = run_row[0]
            risk_metric = run_row[1]
            risk_aversion = float(run_row[2])
            n_candidates = int(run_row[3])

        # === DEMO: Generate synthetic data ===
        # In production, load from dataset_id
        np.random.seed(42)
        n_samples = 1000

        # Generate features
            X = np.random.randn(n_samples, len(features) if features else 3)

        # Generate treatment (observed)
        # Propensity: e(x) = sigmoid(0.5 * x0 + 0.3)
        propensity = 1 / (1 + np.exp(-(0.5 * X[:, 0] + 0.3)))
        treatment = np.random.binomial(1, propensity)

        # Generate outcome
        # Y = 1.0 + 2.0 * x0 + 3.0 * treatment + noise
        outcome = 1.0 + 2.0 * X[:, 0] + 3.0 * treatment + np.random.randn(n_samples)

        # Create dataframe
        dataset = pd.DataFrame({
            'treatment': treatment,
            'outcome': outcome,
            'propensity': propensity
        })

            for i, feat in enumerate(features if features else ['x0', 'x1', 'x2']):
            dataset[feat] = X[:, i]

        # === Create evaluator ===
        evaluator = OffPolicyEvaluator(
            propensity_model=None,  # Use pre-computed propensity
                outcome_model=None
        )

        optimizer = PolicyOptimizer(evaluator)

        # === Run grid search over threshold policies ===
            feature = features[0] if features else 'x0'

            results = optimizer.grid_search_threshold(
                dataset=dataset,
                feature=feature,
                treatment_col='treatment',
                outcome_col='outcome',
                n_thresholds=n_candidates,
                method=ope_method,
                risk_metric=risk_metric,
                risk_aversion=risk_aversion
            )

            # Compute Pareto frontier
            frontier_results = optimizer.compute_pareto_frontier(results)

            # Convert to dict for JSON storage
            frontier_dict = [
                {
                    'expected_value': r['expected_value'],
                    'risk': r['risk'],
                    'policy_params': r['policy_params'],
                    'metrics': {
                        'std': r['std'],
                        'utility': r['utility'],
                        'ci_lower': r['ci_lower'],
                        'ci_upper': r['ci_upper']
                    }
                }
                for r in frontier_results
            ]

            # Select best policy
            best_result = optimizer.select_best_policy(frontier_results, risk_aversion)

            if best_result:
                best_policy_dict = {
                    **policy_config,
                    'threshold': best_result.get('threshold'),
                    'status': 'optimized'
                }

                evaluation_metrics = {
                    'estimated_value': best_result['expected_value'],
                    'estimated_risk': best_result['risk'],
                    'confidence_interval': [best_result['ci_lower'], best_result['ci_upper']],
                        'std': best_result['std'],
                        'utility': best_result['utility']
                    }

                # Update run with results
                await session.execute(
                    text("""
                        UPDATE offline_policy_runs
                        SET status = 'completed',
                            frontier = :frontier,
                            best_policy = :best_policy,
                            evaluation_metrics = :evaluation_metrics,
                            completed_at = NOW()
                        WHERE id = :run_id
                    """),
                    {
                        "run_id": uuid.UUID(run_id),
                        "frontier": json.dumps(frontier_dict),
                        "best_policy": json.dumps(best_policy_dict),
                        "evaluation_metrics": json.dumps(evaluation_metrics)
                    }
                )
                await session.commit()

                logger.info(f"Offline learning completed for run {run_id}")
                logger.info(f"Best policy: threshold={best_result.get('threshold', 0):.2f}, "
                          f"value={best_result['expected_value']:.2f}, "
                          f"risk={best_result['risk']:.2f}")

            else:
                await session.execute(
                    text("""
                        UPDATE offline_policy_runs
                        SET status = 'failed',
                            error_message = :error_message,
                            completed_at = NOW()
                        WHERE id = :run_id
                    """),
                    {
                        "run_id": uuid.UUID(run_id),
                        "error_message": "No feasible policy found"
                    }
                )
                await session.commit()
                logger.error(f"No feasible policy found for run {run_id}")

    except Exception as e:
        logger.error(f"Error in offline learning run {run_id}: {e}", exc_info=True)

            await session.execute(
                text("""
                    UPDATE offline_policy_runs
                    SET status = 'failed',
                        error_message = :error_message,
                        completed_at = NOW()
                    WHERE id = :run_id
                """),
                {
                    "run_id": uuid.UUID(run_id),
                    "error_message": str(e)
                }
            )
            await session.commit()
