"""
Portfolio and ROI endpoints
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

router = APIRouter()


@router.get("/summary")
async def get_portfolio_summary():
    """Get portfolio summary"""
    try:
        # TODO: Calculate actual portfolio metrics
        # For now, return mock summary

        summary = {
            "total_policies": 12,
            "active_policies": 8,
            "total_incremental_profit": 15000000.0,
            "total_roi": 3.2,
            "avg_cas_score": 0.82,
            "by_channel": {
                "push": {
                    "profit": 6000000.0,
                    "roi": 3.5
                },
                "email": {
                    "profit": 5000000.0,
                    "roi": 2.8
                },
                "web": {
                    "profit": 4000000.0,
                    "roi": 3.1
                }
            }
        }

        return summary
    except Exception as e:
        logger.error(f"Get portfolio summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/frontier")
async def get_pareto_frontier():
    """Get multi-objective Pareto frontier"""
    try:
        # TODO: Calculate actual frontier
        # For now, return mock data

        frontier = {
            "all_policies": {
                "x": [100000, 150000, 200000, 250000, 300000],
                "y": [0.1, 0.15, 0.2, 0.3, 0.5],
                "policy_ids": ["p1", "p2", "p3", "p4", "p5"]
            },
            "pareto_frontier": {
                "x": [100000, 200000, 300000],
                "y": [0.1, 0.2, 0.5],
                "policy_ids": ["p1", "p3", "p5"]
            },
            "obj1_name": "incremental_profit",
            "obj2_name": "risk_metric"
        }

        return frontier
    except Exception as e:
        logger.error(f"Get frontier failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
