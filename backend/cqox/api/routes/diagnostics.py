"""
Diagnostics endpoints
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

router = APIRouter()


@router.get("/{model_run_id}")
async def get_diagnostics(model_run_id: str):
    """Get diagnostics for a model run"""
    try:
        # TODO: Load actual diagnostics
        # For now, return mock diagnostics

        diagnostics = {
            "model_run_id": model_run_id,
            "diagnostics": [
                {
                    "type": "covariate_balance",
                    "passed": True,
                    "max_smd": 0.08,
                    "threshold": 0.1
                },
                {
                    "type": "overlap",
                    "passed": True,
                    "violation_rate": 0.02,
                    "threshold": 0.05
                },
                {
                    "type": "sensitivity",
                    "gamma": 1.5,
                    "threshold": 1.3
                }
            ],
            "cas_score": 0.85
        }

        return diagnostics
    except Exception as e:
        logger.error(f"Get diagnostics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
