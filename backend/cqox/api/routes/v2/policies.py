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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policies", tags=["policies"])


# In-memory storage for demo (replace with database in production)
policies_store: dict[str, PolicyConfig] = {}
runs_store: dict[str, OfflinePolicyRun] = {}


@router.post("", response_model=PolicyConfig, status_code=201)
async def create_policy(
    request: CreatePolicyRequest,
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
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=current_user.get("user_id"),
            status="draft"
        )

        policies_store[policy_id] = policy

        logger.info(f"Created policy {policy_id} for tenant {tenant_id}")

        return policy

    except Exception as e:
        logger.error(f"Error creating policy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{policy_id}", response_model=PolicyConfig)
async def get_policy(
    policy_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get policy configuration by ID"""
    if policy_id not in policies_store:
        raise HTTPException(status_code=404, detail="Policy not found")

    policy = policies_store[policy_id]

    # Check tenant isolation
    if policy.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Policy not found")

    return policy


@router.get("", response_model=List[PolicyConfig])
async def list_policies(
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
    # Filter by tenant
    tenant_policies = [p for p in policies_store.values() if p.tenant_id == tenant_id]

    # Apply filters
    if status:
        tenant_policies = [p for p in tenant_policies if p.status == status]

    if dataset_id:
        tenant_policies = [p for p in tenant_policies if p.dataset_id == dataset_id]

    # Sort by created_at descending
    tenant_policies.sort(key=lambda p: p.created_at or datetime.min, reverse=True)

    # Pagination
    paginated = tenant_policies[offset:offset + limit]

    return paginated


@router.post("/{policy_id}/offline-learn", response_model=OfflinePolicyRun, status_code=202)
async def run_offline_policy_learning(
    policy_id: str,
    request: OfflinePolicyLearnRequest,
    background_tasks: BackgroundTasks,
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
    if policy_id not in policies_store:
        raise HTTPException(status_code=404, detail="Policy not found")

    policy = policies_store[policy_id]

    if policy.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Policy not found")

    try:
        run_id = str(uuid.uuid4())

        run = OfflinePolicyRun(
            id=run_id,
            tenant_id=tenant_id,
            policy_config_id=policy_id,
            objective=request.objective,
            risk_metric=request.risk_metric,
            ope_method=request.ope_method,
            risk_aversion=request.risk_aversion,
            dataset_id=policy.dataset_id,
            propensity_model_id=request.propensity_model_id,
            outcome_model_id=request.outcome_model_id,
            n_candidates=request.n_candidates,
            n_bootstrap=request.n_bootstrap,
            status="pending",
            created_at=datetime.utcnow()
        )

        runs_store[run_id] = run

        # Queue background task
        background_tasks.add_task(
            execute_offline_learning,
            run_id=run_id,
            policy=policy,
            run=run
        )

        logger.info(f"Started offline learning run {run_id} for policy {policy_id}")

        return run

    except Exception as e:
        logger.error(f"Error starting offline learning: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}", response_model=OfflinePolicyRun)
async def get_policy_run(
    run_id: str,
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
    if run_id not in runs_store:
        raise HTTPException(status_code=404, detail="Run not found")

    run = runs_store[run_id]

    if run.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Run not found")

    return run


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Delete a policy configuration"""
    if policy_id not in policies_store:
        raise HTTPException(status_code=404, detail="Policy not found")

    policy = policies_store[policy_id]

    if policy.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Policy not found")

    # Check if policy is in use
    active_runs = [r for r in runs_store.values()
                  if r.policy_config_id == policy_id and r.status in ["pending", "running"]]

    if active_runs:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete policy with active learning runs"
        )

    del policies_store[policy_id]

    logger.info(f"Deleted policy {policy_id}")

    return None


# Background task for offline learning
async def execute_offline_learning(run_id: str, policy: PolicyConfig, run: OfflinePolicyRun):
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
    try:
        # Update status
        run.status = "running"
        runs_store[run_id] = run

        logger.info(f"Executing offline learning for run {run_id}")

        # === DEMO: Generate synthetic data ===
        # In production, load from dataset_id
        np.random.seed(42)
        n_samples = 1000

        # Generate features
        X = np.random.randn(n_samples, len(policy.features))

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

        for i, feat in enumerate(policy.features):
            dataset[feat] = X[:, i]

        # === Create evaluator ===
        # In production, load models from model registry
        evaluator = OffPolicyEvaluator(
            propensity_model=None,  # Use pre-computed propensity
            outcome_model=None  # Would load from model_id
        )

        optimizer = PolicyOptimizer(evaluator)

        # === Run grid search over threshold policies ===
        if policy.policy_type == PolicyType.THRESHOLD:
            # Grid search over first feature
            feature = policy.features[0]

            results = optimizer.grid_search_threshold(
                dataset=dataset,
                feature=feature,
                treatment_col='treatment',
                outcome_col='outcome',
                n_thresholds=run.n_candidates,
                method=run.ope_method.value,
                risk_metric=run.risk_metric.value,
                risk_aversion=run.risk_aversion
            )

            # Compute Pareto frontier
            frontier_results = optimizer.compute_pareto_frontier(results)

            # Convert to FrontierPoint objects
            frontier = [
                FrontierPoint(
                    expected_value=r['expected_value'],
                    risk=r['risk'],
                    policy_params=r['policy_params'],
                    metrics={
                        'std': r['std'],
                        'utility': r['utility'],
                        'ci_lower': r['ci_lower'],
                        'ci_upper': r['ci_upper']
                    }
                )
                for r in frontier_results
            ]

            # Select best policy
            best_result = optimizer.select_best_policy(frontier_results, run.risk_aversion)

            if best_result:
                best_policy = PolicyConfig(
                    **policy.dict(),
                    threshold=best_result['threshold'],
                    status="optimized"
                )

                selected_point = FrontierPoint(
                    expected_value=best_result['expected_value'],
                    risk=best_result['risk'],
                    policy_params=best_result['policy_params'],
                    metrics={
                        'std': best_result['std'],
                        'utility': best_result['utility']
                    }
                )

                # Update run with results
                run.frontier = frontier
                run.best_policy = best_policy
                run.selected_point = selected_point
                run.estimated_value = best_result['expected_value']
                run.estimated_risk = best_result['risk']
                run.confidence_interval = [best_result['ci_lower'], best_result['ci_upper']]
                run.status = "completed"
                run.completed_at = datetime.utcnow()

                logger.info(f"Offline learning completed for run {run_id}")
                logger.info(f"Best policy: threshold={best_result['threshold']:.2f}, "
                          f"value={best_result['expected_value']:.2f}, "
                          f"risk={best_result['risk']:.2f}")

            else:
                run.status = "failed"
                run.error_message = "No feasible policy found"
                logger.error(f"No feasible policy found for run {run_id}")

        else:
            # Other policy types not implemented in demo
            run.status = "failed"
            run.error_message = f"Policy type {policy.policy_type} not yet implemented"
            logger.error(f"Policy type {policy.policy_type} not implemented")

        # Save updated run
        runs_store[run_id] = run

    except Exception as e:
        logger.error(f"Error in offline learning run {run_id}: {e}", exc_info=True)

        run.status = "failed"
        run.error_message = str(e)
        run.completed_at = datetime.utcnow()
        runs_store[run_id] = run
