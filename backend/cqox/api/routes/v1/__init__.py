"""
v1 API Routes

DecisionCard（Δ¥ + Go/Canary/Hold判定）関連のAPI

NOTE: Console router is now registered in main.py with Viz.pdf spec
- OLD: v1/console.py (修正.pdf spec) - kept for /decision-console/overview backward compatibility
- NEW: routes/console.py (Viz.pdf spec) - primary /console/summary endpoint
"""
from fastapi import APIRouter
from . import results, datasets, policies, analysis, upload
# NOTE: console router is excluded here to avoid conflict with Viz.pdf console router in main.py

# v1 Router統合
v1_router = APIRouter()

# サブルーター登録
v1_router.include_router(datasets.router)
v1_router.include_router(policies.router)
v1_router.include_router(analysis.router)
v1_router.include_router(results.router)
# NOTE: console.router removed - using Viz.pdf spec router from main.py instead
# v1_router.include_router(console.router)
# v1_router.include_router(console.decision_console_router)
v1_router.include_router(upload.router)

__all__ = ["v1_router", "results", "datasets", "policies", "analysis", "upload"]
