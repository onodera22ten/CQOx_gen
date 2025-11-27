"""V2 API Router"""
from fastapi import APIRouter
from . import multi_arm, experiments, growth, governance, column_suggestions

v2_router = APIRouter()
v2_router.include_router(multi_arm.router, prefix="/multi-arm", tags=["v2-multi-arm"])
v2_router.include_router(experiments.router, prefix="/experiments", tags=["v2-experiments"])
v2_router.include_router(growth.router, prefix="/growth", tags=["v2-growth"])
v2_router.include_router(governance.router, prefix="/governance", tags=["v2-governance"])
v2_router.include_router(column_suggestions.router, tags=["v2-datasets"])

__all__ = ["v2_router"]
