"""
Decision Console endpoints
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

router = APIRouter()


@router.get("/summary")
async def get_console_summary():
    """Get Decision Console summary"""
    try:
        # TODO: Calculate actual summary
        # For now, return mock summary

        summary = {
            "recommended_policies": [
                {
                    "policy_id": "push_high_uplift_v1",
                    "name": "High-uplift push campaign",
                    "incremental_profit": 2500000.0,
                    "roi": 3.8,
                    "risk_score": 0.12,
                    "cas_score": 0.88
                },
                {
                    "policy_id": "email_retention_v2",
                    "name": "Email retention campaign",
                    "incremental_profit": 1800000.0,
                    "roi": 3.2,
                    "risk_score": 0.15,
                    "cas_score": 0.85
                }
            ],
            "total_incremental_profit": 15000000.0,
            "total_campaigns": 12,
            "avg_roi": 3.2
        }

        return summary
    except Exception as e:
        logger.error(f"Get console summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
