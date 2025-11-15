"""
Policy management endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import yaml
from pathlib import Path
from loguru import logger

from cqox.config import settings
from cqox.data.schema import Policy, PolicyStatus

router = APIRouter()


@router.get("/")
async def list_policies():
    """List all policies"""
    try:
        policies_dir = settings.policies_dir
        policy_files = list(policies_dir.glob("**/*.yaml"))

        policies = []
        for policy_file in policy_files:
            with open(policy_file, 'r') as f:
                policy_data = yaml.safe_load(f)
                policies.append(policy_data)

        return {"policies": policies, "count": len(policies)}
    except Exception as e:
        logger.error(f"List policies failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{policy_id}")
async def get_policy(policy_id: str):
    """Get policy details"""
    try:
        policy_file = settings.policies_dir / f"{policy_id}.yaml"

        if not policy_file.exists():
            raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

        with open(policy_file, 'r') as f:
            policy_data = yaml.safe_load(f)

        return policy_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get policy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_policy(policy: Policy):
    """Create a new policy"""
    try:
        policy_file = settings.policies_dir / f"{policy.id}.yaml"

        if policy_file.exists():
            raise HTTPException(status_code=400, detail=f"Policy {policy.id} already exists")

        # Save policy
        policy_file.parent.mkdir(parents=True, exist_ok=True)
        with open(policy_file, 'w') as f:
            yaml.dump(policy.dict(), f, default_flow_style=False)

        logger.info(f"Policy created: {policy.id}")
        return {"success": True, "policy_id": policy.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create policy failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{policy_id}/evaluate")
async def evaluate_policy(policy_id: str):
    """
    Run offline evaluation for a policy

    This would trigger an async job in production
    """
    try:
        # Load policy
        policy_file = settings.policies_dir / f"{policy_id}.yaml"
        if not policy_file.exists():
            raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

        with open(policy_file, 'r') as f:
            policy_data = yaml.safe_load(f)

        # TODO: Trigger async evaluation job
        # For now, return mock result

        evaluation_result = {
            "policy_id": policy_id,
            "status": "completed",
            "incremental_profit": 1250000.0,
            "incremental_revenue": 2000000.0,
            "roi": 2.5,
            "risk_score": 0.15,
            "cas_score": 0.85
        }

        logger.info(f"Policy evaluated: {policy_id}")
        return evaluation_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evaluate policy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{policy_id}/export")
async def export_policy_targets(policy_id: str):
    """
    Export target list for a policy

    Returns CSV/Parquet of users who should receive the treatment
    """
    try:
        # Load policy
        policy_file = settings.policies_dir / f"{policy_id}.yaml"
        if not policy_file.exists():
            raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

        # TODO: Generate target list based on policy rules
        # For now, return mock path

        export_path = settings.exports_dir / f"{policy_id}_targets.csv"

        logger.info(f"Policy targets exported: {policy_id}")
        return {
            "success": True,
            "export_path": str(export_path),
            "target_count": 5000
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export targets failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
