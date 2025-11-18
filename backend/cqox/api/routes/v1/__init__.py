"""
v1 API Routes

DecisionCard（Δ¥ + Go/Canary/Hold判定）関連のAPI
"""
from fastapi import APIRouter
from . import results, console, datasets, policies, analysis, upload

# v1 Router統合
v1_router = APIRouter()

# サブルーター登録
v1_router.include_router(datasets.router)
v1_router.include_router(policies.router)
v1_router.include_router(analysis.router)
v1_router.include_router(results.router)
v1_router.include_router(console.router)
v1_router.include_router(upload.router)

__all__ = ["v1_router", "results", "console", "datasets", "policies", "analysis", "upload"]
