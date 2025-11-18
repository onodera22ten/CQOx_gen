"""
Causal inference endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from loguru import logger
import uuid

from cqox.tasks.causal_tasks import train_causal_models as train_task

router = APIRouter()

# Supported estimators (all 7)
SUPPORTED_ESTIMATORS = [
    "s_learner",
    "t_learner",
    "x_learner",
    "dr_learner",
    "causal_forest",
    "uplift_forest",
    "doubly_robust_forest"
]


class TrainRequest(BaseModel):
    """Request to train causal models"""
    dataset_path: str
    outcome: str
    treatment: str
    features: List[str]
    estimators: List[str] = ["s_learner", "t_learner", "dr_learner"]
    async_mode: bool = True  # Use Celery if True


class TrainSyncRequest(BaseModel):
    """Request for synchronous training"""
    dataset_path: str
    outcome: str
    treatment: str
    features: List[str]
    estimator: str = "s_learner"


@router.post("/train")
async def train_causal_models_endpoint(request: TrainRequest):
    """
    Train causal models (async via Celery)

    Supports all 7 estimators:
    - s_learner
    - t_learner
    - x_learner
    - dr_learner
    - causal_forest
    - uplift_forest
    - doubly_robust_forest
    """
    try:
        # Validate estimators
        invalid = [e for e in request.estimators if e not in SUPPORTED_ESTIMATORS]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported estimators: {invalid}. Supported: {SUPPORTED_ESTIMATORS}"
            )

        logger.info(f"Training causal models: {request.estimators}")

        if request.async_mode:
            # Trigger Celery task
            task = train_task.delay(
                dataset_path=request.dataset_path,
                outcome=request.outcome,
                treatment=request.treatment,
                features=request.features,
                estimators=request.estimators
            )

            return {
                "task_id": task.id,
                "status": "submitted",
                "estimators": request.estimators,
                "message": f"Training {len(request.estimators)} estimators asynchronously"
            }
        else:
            # Synchronous execution
            from cqox.data.loader import DataLoader
            from cqox.causal.estimators.s_learner import SLearner
            from cqox.causal.estimators.t_learner import TLearner
            from cqox.causal.estimators.x_learner import XLearner
            from cqox.causal.estimators.dr_learner import DRLearner
            from cqox.causal.estimators.causal_forest import CausalForest
            from cqox.causal.estimators.uplift_forest import UpliftForest
            from cqox.causal.estimators.doubly_robust_forest import DoublyRobustForest
            import numpy as np

            # Load data
            df = DataLoader.load_auto(request.dataset_path)
            X = df[request.features]
            T = df[request.treatment]
            y = df[request.outcome]

            results = {}

            # Map estimator names to classes
            estimator_map = {
                's_learner': SLearner,
                't_learner': TLearner,
                'x_learner': XLearner,
                'dr_learner': DRLearner,
                'causal_forest': CausalForest,
                'uplift_forest': UpliftForest,
                'doubly_robust_forest': DoublyRobustForest
            }

            # Train each estimator
            for estimator_name in request.estimators:
                logger.info(f"Training {estimator_name}")

                EstimatorClass = estimator_map[estimator_name]
                estimator = EstimatorClass()

                # Fit
                estimator.fit(X, T, y)

                # Estimate ATE and CATE
                ate = estimator.estimate_ate()
                cate = estimator.estimate_cate(X)

                results[estimator_name] = {
                    'ate': float(ate),
                    'cate_mean': float(np.mean(cate)),
                    'cate_std': float(np.std(cate)),
                    'cate_min': float(np.min(cate)),
                    'cate_max': float(np.max(cate))
                }

            return {
                "status": "completed",
                "results": results
            }

    except Exception as e:
        logger.error(f"Train models failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train/sync")
async def train_single_model_sync(request: TrainSyncRequest):
    """
    Train a single model synchronously (for quick testing)
    """
    try:
        if request.estimator not in SUPPORTED_ESTIMATORS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported estimator: {request.estimator}"
            )

        from cqox.data.loader import DataLoader
        from cqox.causal.estimators.s_learner import SLearner
        from cqox.causal.estimators.t_learner import TLearner
        from cqox.causal.estimators.x_learner import XLearner
        from cqox.causal.estimators.dr_learner import DRLearner
        from cqox.causal.estimators.causal_forest import CausalForest
        from cqox.causal.estimators.uplift_forest import UpliftForest
        from cqox.causal.estimators.doubly_robust_forest import DoublyRobustForest
        import numpy as np

        estimator_map = {
            's_learner': SLearner,
            't_learner': TLearner,
            'x_learner': XLearner,
            'dr_learner': DRLearner,
            'causal_forest': CausalForest,
            'uplift_forest': UpliftForest,
            'doubly_robust_forest': DoublyRobustForest
        }

        logger.info(f"Training {request.estimator} synchronously")

        # Load data
        df = DataLoader.load_auto(request.dataset_path)
        X = df[request.features]
        T = df[request.treatment]
        y = df[request.outcome]

        # Train
        EstimatorClass = estimator_map[request.estimator]
        estimator = EstimatorClass()
        estimator.fit(X, T, y)

        # Estimate
        ate = estimator.estimate_ate()
        cate = estimator.estimate_cate(X)

        return {
            "estimator": request.estimator,
            "status": "completed",
            "ate": float(ate),
            "cate_mean": float(np.mean(cate)),
            "cate_std": float(np.std(cate)),
            "cate_min": float(np.min(cate)),
            "cate_max": float(np.max(cate)),
            "cate_values": cate.tolist()
        }

    except Exception as e:
        logger.error(f"Train single model failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get Celery task status"""
    try:
        from cqox.tasks.celery_app import app as celery_app

        task = celery_app.AsyncResult(task_id)

        return {
            "task_id": task_id,
            "status": task.status,
            "result": task.result if task.ready() else None
        }

    except Exception as e:
        logger.error(f"Get task status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estimators")
async def list_estimators():
    """List all supported estimators"""
    return {
        "estimators": SUPPORTED_ESTIMATORS,
        "total": len(SUPPORTED_ESTIMATORS)
    }
