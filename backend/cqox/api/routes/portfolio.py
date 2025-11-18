"""
Portfolio and ROI endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from cqox.auth.dependencies import get_current_user
from cqox.database.connection import get_db

router = APIRouter()


@router.get("/summary")
async def get_portfolio_summary(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get portfolio summary（実データから集計）"""
    from sqlalchemy import text
    import uuid as uuid_lib
    
    try:
        tenant_id = uuid_lib.UUID("00000000-0000-0000-0000-000000000001")
        
        # Policies count
        policy_query = text("""
            SELECT 
                COUNT(*) as total_policies,
                COUNT(*) FILTER (WHERE status = 'active') as active_policies
            FROM policies
            WHERE tenant_id = :tenant_id
        """)
        policy_result = await db.execute(policy_query, {"tenant_id": tenant_id})
        policy_row = policy_result.fetchone()
        
        # Analysis runs summary
        analysis_query = text("""
            SELECT 
                COUNT(*) as total_analyses,
                COUNT(*) FILTER (WHERE status = 'completed') as completed_analyses,
                COALESCE(SUM(delta_yen), 0) as total_profit,
                COALESCE(AVG(delta_yen), 0) as avg_profit
            FROM analysis_runs
            WHERE tenant_id = :tenant_id AND status = 'completed'
        """)
        analysis_result = await db.execute(analysis_query, {"tenant_id": tenant_id})
        analysis_row = analysis_result.fetchone()
        
        total_policies = policy_row[0] if policy_row else 0
        active_policies = policy_row[1] if policy_row else 0
        total_profit = float(analysis_row[2]) if analysis_row else 0.0
        avg_profit = float(analysis_row[3]) if analysis_row else 0.0
        
        # Calculate ROI (simplified: profit / number of analyses)
        completed_analyses = analysis_row[1] if analysis_row else 0
        total_roi = (total_profit / completed_analyses) if completed_analyses > 0 else 0.0
        
        summary = {
            "total_policies": total_policies,
            "active_policies": active_policies,
            "total_incremental_profit": total_profit,
            "total_roi": total_roi,
            "avg_cas_score": 0.0,  # TODO: Calculate from diagnostics
            "by_channel": {
                "all": {
                    "profit": total_profit,
                    "roi": total_roi
                }
            }
        }
        
        logger.info(f"Portfolio summary: {total_policies} policies, {total_profit:.2f} total profit")
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
