"""
CQOx v2 API Routes
Policy Lab, Recourse, and Experiment Design
"""

from fastapi import APIRouter

# Create v2 router
v2_router = APIRouter(prefix="/v2", tags=["v2"])

# Import subrouters
from .policies import router as policies_router
from .recourse import router as recourse_router
from .experiments import router as experiments_router

# Include subrouters
v2_router.include_router(policies_router)
v2_router.include_router(recourse_router)
v2_router.include_router(experiments_router)

__all__ = ["v2_router"]
