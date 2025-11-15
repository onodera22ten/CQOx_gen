"""
Experiment Design API - v2
A/B testing, sample size calculation, and power analysis
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import uuid
import logging
from datetime import datetime

from cqox.models.v2 import (
    ExperimentDesign,
    ExperimentDesignRequest,
    ExperimentResult,
    ExperimentArm
)
from cqox.ml.experiment_design import (
    SampleSizeCalculator,
    PowerAnalyzer,
    SequentialTesting,
    ExperimentAnalyzer
)
from cqox.auth.dependencies import get_current_user, get_tenant_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/experiments", tags=["experiments"])


# In-memory storage for demo
experiments_store: dict[str, ExperimentDesign] = {}


@router.post("/design", response_model=ExperimentDesign, status_code=201)
async def create_experiment_design(
    request: ExperimentDesignRequest,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """
    Create an A/B test experiment design with sample size calculation

    This endpoint designs an experiment by:
    1. Validating treatment arms (must sum to 100% allocation)
    2. Calculating required sample size based on:
       - Outcome type (continuous or binary)
       - Minimum detectable effect
       - Desired power and significance level
    3. Estimating runtime given current traffic

    **Sample Size Formulas**:

    For continuous outcomes (t-test):
    ```
    n = 2 * (z_α/2 + z_β)² * σ² / δ²
    ```

    For binary outcomes (proportion test):
    ```
    n = (z_α * √(p*(1-p)*(1+1/r)) + z_β * √(p1*(1-p1) + p2*(1-p2)/r))² / (p2-p1)²
    ```

    Where:
    - z_α = critical value for significance level α
    - z_β = critical value for power (1-β)
    - σ = standard deviation
    - δ = minimum detectable effect
    - p1, p2 = proportions in control and treatment
    - r = allocation ratio

    Args:
        request: Experiment design specification

    Returns:
        ExperimentDesign with calculated sample sizes
    """
    try:
        experiment_id = str(uuid.uuid4())

        # Validate arms
        total_allocation = sum(arm.allocation for arm in request.arms)
        if not (0.99 <= total_allocation <= 1.01):
            raise HTTPException(
                status_code=400,
                detail=f"Arm allocations must sum to 1.0, got {total_allocation}"
            )

        # Calculate sample size based on outcome type
        if request.outcome_type == "continuous":
            # Continuous outcome (t-test)
            if request.baseline_mean is None:
                raise HTTPException(
                    status_code=400,
                    detail="baseline_mean required for continuous outcomes"
                )

            # Estimate baseline_std from historical data or use heuristic
            if request.dataset_id:
                # In production, load from dataset and compute std
                baseline_std = request.baseline_mean * 0.5  # Heuristic: CV = 0.5
            else:
                # Use heuristic
                baseline_std = request.baseline_mean * 0.5

            sample_size_result = SampleSizeCalculator.continuous_outcome(
                baseline_mean=request.baseline_mean,
                baseline_std=baseline_std,
                minimum_detectable_effect=request.minimum_detectable_effect,
                alpha=request.alpha,
                power=request.power,
                two_sided=True,
                allocation_ratio=1.0
            )

        elif request.outcome_type == "binary":
            # Binary outcome (proportion test)
            if request.baseline_proportion is None:
                raise HTTPException(
                    status_code=400,
                    detail="baseline_proportion required for binary outcomes"
                )

            sample_size_result = SampleSizeCalculator.binary_outcome(
                baseline_proportion=request.baseline_proportion,
                minimum_detectable_effect=request.minimum_detectable_effect,
                alpha=request.alpha,
                power=request.power,
                two_sided=True,
                allocation_ratio=1.0
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported outcome_type: {request.outcome_type}"
            )

        # Adjust for number of arms (if > 2, need Bonferroni correction)
        n_arms = len(request.arms)
        if n_arms > 2:
            # Multi-arm: adjust sample size
            # Bonferroni correction: alpha_adj = alpha / (n_arms - 1)
            adjusted_alpha = request.alpha / (n_arms - 1)

            if request.outcome_type == "continuous":
                sample_size_result = SampleSizeCalculator.multi_arm(
                    n_arms=n_arms,
                    baseline_mean=request.baseline_mean,
                    baseline_std=baseline_std,
                    minimum_detectable_effect=request.minimum_detectable_effect,
                    alpha=request.alpha,
                    power=request.power,
                    correction='bonferroni'
                )
            else:
                # Re-calculate with adjusted alpha
                sample_size_result = SampleSizeCalculator.binary_outcome(
                    baseline_proportion=request.baseline_proportion,
                    minimum_detectable_effect=request.minimum_detectable_effect,
                    alpha=adjusted_alpha,
                    power=request.power,
                    two_sided=True,
                    allocation_ratio=1.0
                )

        # Estimate runtime
        # In production, fetch current_traffic_per_day from analytics
        current_traffic_per_day = 1000  # Demo value

        expected_runtime_days = ExperimentAnalyzer.estimate_runtime(
            required_sample_size=sample_size_result.total_sample_size,
            current_traffic_per_day=current_traffic_per_day,
            allocation_to_experiment=1.0
        )

        # Create experiment design
        experiment = ExperimentDesign(
            id=experiment_id,
            tenant_id=tenant_id,
            name=request.name,
            description=request.description,
            treatment_variable=request.treatment_variable,
            arms=request.arms,
            primary_outcome=request.primary_outcome,
            outcome_type=request.outcome_type,
            baseline_mean=request.baseline_mean,
            baseline_proportion=request.baseline_proportion,
            minimum_detectable_effect=request.minimum_detectable_effect,
            alpha=request.alpha,
            power=request.power,
            required_sample_size_per_arm=sample_size_result.required_sample_size_per_arm,
            total_sample_size=sample_size_result.total_sample_size,
            expected_runtime_days=expected_runtime_days,
            dataset_id=request.dataset_id,
            policy_config_id=request.policy_config_id,
            status="design",
            created_at=datetime.utcnow()
        )

        experiments_store[experiment_id] = experiment

        logger.info(f"Created experiment design {experiment_id} for tenant {tenant_id}")
        logger.info(f"Sample size: {sample_size_result.total_sample_size} "
                   f"({sample_size_result.required_sample_size_per_arm} per arm)")
        logger.info(f"Expected runtime: {expected_runtime_days:.1f} days")

        return experiment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating experiment design: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{experiment_id}", response_model=ExperimentDesign)
async def get_experiment(
    experiment_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get experiment design by ID"""
    if experiment_id not in experiments_store:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment = experiments_store[experiment_id]

    if experiment.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return experiment


@router.get("", response_model=List[ExperimentDesign])
async def list_experiments(
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List all experiments for the current tenant"""
    # Filter by tenant
    tenant_experiments = [e for e in experiments_store.values() if e.tenant_id == tenant_id]

    # Apply filters
    if status:
        tenant_experiments = [e for e in tenant_experiments if e.status == status]

    # Sort by created_at descending
    tenant_experiments.sort(key=lambda e: e.created_at or datetime.min, reverse=True)

    # Pagination
    paginated = tenant_experiments[offset:offset + limit]

    return paginated


@router.post("/{experiment_id}/start", response_model=ExperimentDesign)
async def start_experiment(
    experiment_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """
    Start running an experiment

    This transitions the experiment from "design" to "running" status.
    In production, this would:
    1. Deploy treatment assignment logic to production
    2. Start logging assignments and outcomes
    3. Initialize monitoring dashboards
    """
    if experiment_id not in experiments_store:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment = experiments_store[experiment_id]

    if experiment.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.status != "design":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start experiment in status '{experiment.status}'"
        )

    # Update status
    experiment.status = "running"
    experiment.started_at = datetime.utcnow()

    experiments_store[experiment_id] = experiment

    logger.info(f"Started experiment {experiment_id}")

    return experiment


@router.post("/{experiment_id}/stop", response_model=ExperimentDesign)
async def stop_experiment(
    experiment_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """
    Stop a running experiment

    This transitions the experiment to "stopped" status and freezes data collection.
    """
    if experiment_id not in experiments_store:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment = experiments_store[experiment_id]

    if experiment.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.status != "running":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot stop experiment in status '{experiment.status}'"
        )

    # Update status
    experiment.status = "stopped"
    experiment.completed_at = datetime.utcnow()

    experiments_store[experiment_id] = experiment

    logger.info(f"Stopped experiment {experiment_id}")

    return experiment


@router.get("/{experiment_id}/power-analysis", response_model=dict)
async def power_analysis(
    experiment_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """
    Compute power analysis for the experiment

    Returns power curve showing statistical power for different effect sizes.
    """
    if experiment_id not in experiments_store:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment = experiments_store[experiment_id]

    if experiment.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        # Generate power curve
        effect_sizes = [
            experiment.minimum_detectable_effect * factor
            for factor in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        ]

        # Convert effect sizes to Cohen's d
        if experiment.outcome_type == "continuous":
            baseline_std = experiment.baseline_mean * 0.5
            effect_sizes_d = [e / baseline_std for e in effect_sizes]
        else:
            # For binary, use Cohen's h approximation
            import numpy as np
            p1 = experiment.baseline_proportion
            effect_sizes_d = [
                2 * (np.arcsin(np.sqrt(p1 + e)) - np.arcsin(np.sqrt(p1)))
                for e in effect_sizes
            ]

        power_curve = PowerAnalyzer.power_curve(
            effect_sizes=effect_sizes_d,
            sample_size_per_arm=experiment.required_sample_size_per_arm,
            alpha=experiment.alpha
        )

        # Format results
        power_results = [
            {
                'effect_size': float(effect_sizes[i]),
                'effect_size_standardized': float(effect_sizes_d[i]),
                'power': float(power)
            }
            for i, (_, power) in enumerate(power_curve)
        ]

        return {
            'experiment_id': experiment_id,
            'sample_size_per_arm': experiment.required_sample_size_per_arm,
            'alpha': experiment.alpha,
            'power_curve': power_results
        }

    except Exception as e:
        logger.error(f"Error computing power analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{experiment_id}", status_code=204)
async def delete_experiment(
    experiment_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Delete an experiment design (only if not started)"""
    if experiment_id not in experiments_store:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment = experiments_store[experiment_id]

    if experiment.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.status in ["running", "completed"]:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete running or completed experiment"
        )

    del experiments_store[experiment_id]

    logger.info(f"Deleted experiment {experiment_id}")

    return None
