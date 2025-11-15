"""
Recourse API - v2
Individual-level counterfactual interventions
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
import uuid
import logging
import numpy as np
from datetime import datetime

from cqox.models.v2 import (
    RecoursePlan,
    RecourseRequest,
    BatchRecourseRequest,
    RecourseCandidate as RecourseResponse
)
from cqox.ml.recourse_engine import RecourseGenerator, RecourseCandidate
from cqox.auth.dependencies import get_current_user, get_tenant_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recourse", tags=["recourse"])


# Mock model for demo (in production, load from model registry)
class MockModel:
    """Mock outcome prediction model"""

    def predict(self, X):
        """Simple linear model for demo: y = 1.0 + 2.0*x0 + 1.5*x1 + 0.5*x2"""
        if len(X.shape) == 1:
            X = X.reshape(1, -1)

        predictions = 1.0 + 2.0 * X[:, 0]

        if X.shape[1] > 1:
            predictions += 1.5 * X[:, 1]

        if X.shape[1] > 2:
            predictions += 0.5 * X[:, 2]

        return predictions


@router.post("/{unit_id}", response_model=RecoursePlan, status_code=200)
async def get_individual_recourse(
    unit_id: str,
    request: RecourseRequest,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate counterfactual recourse plan for an individual

    Given an individual's current features and a target outcome,
    this endpoint generates actionable interventions to help them
    achieve the desired outcome.

    The recourse engine:
    1. Loads the outcome prediction model
    2. Identifies actionable features (e.g., can change spending, not age)
    3. Optimizes feature changes to reach target while minimizing cost
    4. Returns multiple diverse recourse options

    **Important**: This endpoint does NOT store individual-level data.
    The recourse plan is computed on-the-fly and returned immediately.
    No PII is persisted in the database (GDPR/privacy compliance).

    Args:
        unit_id: Individual identifier (for logging/auditing only)
        request: Recourse request with current features and target

    Returns:
        RecoursePlan with multiple intervention candidates
    """
    try:
        logger.info(f"Generating recourse for unit {unit_id}, target={request.target_outcome}")

        # === Load model ===
        # In production, load from model registry using request.policy_id
        model = MockModel()

        # === Validate features ===
        all_features = list(request.current_features.keys())

        # Check that actionable features are subset of all features
        for feat in request.actionable_features:
            if feat not in all_features:
                raise HTTPException(
                    status_code=400,
                    detail=f"Actionable feature '{feat}' not in current_features"
                )

        for feat in request.immutable_features:
            if feat not in all_features:
                raise HTTPException(
                    status_code=400,
                    detail=f"Immutable feature '{feat}' not in current_features"
                )

        # === Create recourse generator ===
        # In production, load feature ranges and costs from metadata
        feature_ranges = {
            feat: (0.0, 10.0) for feat in request.actionable_features
        }

        generator = RecourseGenerator(
            model=model,
            feature_ranges=feature_ranges,
            feature_costs=request.feature_costs,
            cost_type=request.cost_type
        )

        # === Predict current outcome ===
        current_predicted = generator.predict_outcome(request.current_features, all_features)

        logger.info(f"Current predicted outcome: {current_predicted:.2f}")

        # Check if target is already met
        if current_predicted >= request.target_outcome:
            logger.info(f"Target already met for unit {unit_id}")

            # Return empty recourse plan
            return RecoursePlan(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                unit_id=unit_id,
                policy_id=request.policy_id,
                current_features=request.current_features,
                current_predicted_outcome=float(current_predicted),
                target_outcome=request.target_outcome,
                candidates=[],
                actionable_features=request.actionable_features,
                immutable_features=request.immutable_features,
                cost_type=request.cost_type,
                feature_costs=request.feature_costs,
                model_id="mock_model",
                generated_at=datetime.utcnow()
            )

        # === Generate diverse recourse candidates ===
        candidates = generator.generate_diverse_recourse(
            current_features=request.current_features,
            target_outcome=request.target_outcome,
            actionable_features=request.actionable_features,
            immutable_features=request.immutable_features,
            all_features=all_features,
            n_candidates=request.n_candidates,
            diversity_weight=0.2
        )

        logger.info(f"Generated {len(candidates)} recourse candidates for unit {unit_id}")

        # Convert to response format
        candidate_responses = [
            RecourseResponse(
                intervention=c.intervention,
                predicted_outcome=c.predicted_outcome,
                cost=c.cost,
                feasibility=c.feasibility,
                actionability=c.actionability,
                diversity=c.diversity
            )
            for c in candidates
        ]

        # Create recourse plan
        plan = RecoursePlan(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            unit_id=unit_id,
            policy_id=request.policy_id,
            current_features=request.current_features,
            current_predicted_outcome=float(current_predicted),
            target_outcome=request.target_outcome,
            candidates=candidate_responses,
            actionable_features=request.actionable_features,
            immutable_features=request.immutable_features,
            cost_type=request.cost_type,
            feature_costs=request.feature_costs,
            model_id="mock_model",
            generated_at=datetime.utcnow()
        )

        return plan

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recourse for unit {unit_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=List[RecoursePlan], status_code=200)
async def batch_recourse(
    request: BatchRecourseRequest,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate recourse plans for multiple individuals (batch processing)

    This endpoint processes up to 1000 individuals in a single request.
    For larger batches, use async job processing.

    The individuals' data must be provided via dataset_id, which contains:
    - unit_id column
    - Feature columns matching actionable_features

    **Privacy note**: Individual-level recourse plans are NOT stored.
    They are computed and returned immediately.

    Args:
        request: Batch request with unit_ids and parameters

    Returns:
        List of RecoursePlan objects (one per unit_id)
    """
    try:
        if len(request.unit_ids) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Batch size exceeds limit of 1000. Use async job for larger batches."
            )

        logger.info(f"Processing batch recourse for {len(request.unit_ids)} units")

        # === Load dataset ===
        # In production, load from data warehouse/feature store
        # For demo, generate synthetic data
        import pandas as pd

        np.random.seed(42)
        dataset = pd.DataFrame({
            'unit_id': request.unit_ids,
            'feature_0': np.random.randn(len(request.unit_ids)),
            'feature_1': np.random.randn(len(request.unit_ids)),
            'feature_2': np.random.randn(len(request.unit_ids))
        })

        # === Load model ===
        model = MockModel()

        # === Create recourse generator ===
        feature_ranges = {
            feat: (0.0, 10.0) for feat in request.actionable_features
        }

        generator = RecourseGenerator(
            model=model,
            feature_ranges=feature_ranges,
            cost_type='L1'
        )

        # === Process each unit ===
        plans = []

        for unit_id in request.unit_ids:
            unit_data = dataset[dataset['unit_id'] == unit_id].iloc[0]

            # Extract current features
            current_features = {
                feat: float(unit_data[feat])
                for feat in request.actionable_features
                if feat in dataset.columns
            }

            if not current_features:
                logger.warning(f"No features found for unit {unit_id}, skipping")
                continue

            all_features = list(current_features.keys())

            # Predict current outcome
            current_predicted = generator.predict_outcome(current_features, all_features)

            # Generate recourse if needed
            if current_predicted < request.target_outcome:
                candidates = generator.generate_diverse_recourse(
                    current_features=current_features,
                    target_outcome=request.target_outcome,
                    actionable_features=request.actionable_features,
                    immutable_features=request.immutable_features,
                    all_features=all_features,
                    n_candidates=request.n_candidates
                )

                candidate_responses = [
                    RecourseResponse(
                        intervention=c.intervention,
                        predicted_outcome=c.predicted_outcome,
                        cost=c.cost,
                        feasibility=c.feasibility,
                        actionability=c.actionability,
                        diversity=c.diversity
                    )
                    for c in candidates
                ]
            else:
                candidate_responses = []

            # Create plan
            plan = RecoursePlan(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                unit_id=unit_id,
                policy_id=request.policy_id,
                current_features=current_features,
                current_predicted_outcome=float(current_predicted),
                target_outcome=request.target_outcome,
                candidates=candidate_responses,
                actionable_features=request.actionable_features,
                immutable_features=request.immutable_features,
                model_id="mock_model",
                generated_at=datetime.utcnow()
            )

            plans.append(plan)

        logger.info(f"Generated {len(plans)} recourse plans")

        return plans

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch recourse: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
