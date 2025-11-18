"""
Multi-Tenancy with Row-Level Security and Quotas
Tenant isolation, rate limiting, and usage metering
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import json

from fastapi import HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cqox.storage.redis_cache import get_redis_client
from cqox.storage.postgres_client import get_postgres_client

logger = logging.getLogger(__name__)


class Plan(str, Enum):
    """Subscription plans"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class TenantQuotas:
    """Tenant resource quotas"""
    # Storage
    max_storage_gb: int
    max_datasets: int

    # Compute
    max_concurrent_jobs: int
    max_jobs_per_day: int
    max_models: int

    # API
    max_api_calls_per_minute: int
    max_api_calls_per_day: int

    # Features
    max_policies: int
    max_experiments: int
    offline_policy_learning: bool
    recourse_generation: bool
    experiment_design: bool

    @classmethod
    def from_plan(cls, plan: Plan) -> 'TenantQuotas':
        """Get quotas for a plan"""
        quotas_by_plan = {
            Plan.FREE: cls(
                max_storage_gb=1,
                max_datasets=3,
                max_concurrent_jobs=1,
                max_jobs_per_day=10,
                max_models=5,
                max_api_calls_per_minute=10,
                max_api_calls_per_day=1000,
                max_policies=3,
                max_experiments=2,
                offline_policy_learning=False,
                recourse_generation=False,
                experiment_design=False,
            ),
            Plan.PRO: cls(
                max_storage_gb=50,
                max_datasets=50,
                max_concurrent_jobs=5,
                max_jobs_per_day=100,
                max_models=100,
                max_api_calls_per_minute=100,
                max_api_calls_per_day=100000,
                max_policies=50,
                max_experiments=20,
                offline_policy_learning=True,
                recourse_generation=True,
                experiment_design=True,
            ),
            Plan.ENTERPRISE: cls(
                max_storage_gb=1000,
                max_datasets=1000,
                max_concurrent_jobs=50,
                max_jobs_per_day=10000,
                max_models=10000,
                max_api_calls_per_minute=1000,
                max_api_calls_per_day=10000000,
                max_policies=1000,
                max_experiments=1000,
                offline_policy_learning=True,
                recourse_generation=True,
                experiment_design=True,
            ),
        }

        return quotas_by_plan[plan]


class TenantContext:
    """
    Tenant context manager for database queries

    Sets PostgreSQL session variable for Row-Level Security
    """

    def __init__(self, tenant_id: str, db_session: AsyncSession):
        self.tenant_id = tenant_id
        self.db_session = db_session

    async def __aenter__(self):
        """Set tenant context in database session"""
        # Set PostgreSQL session variable for RLS
        await self.db_session.execute(
            text("SET LOCAL app.current_tenant_id = :tenant_id"),
            {"tenant_id": self.tenant_id}
        )

        logger.debug(f"Set tenant context: {self.tenant_id}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Reset tenant context"""
        # PostgreSQL LOCAL variables are automatically reset at transaction end
        pass


class RateLimiter:
    """
    Redis-based sliding window rate limiter

    Features:
    - Sliding window for accurate rate limiting
    - Per-tenant and per-user limits
    - Burst allowance
    - Multiple time windows (minute, hour, day)
    """

    def __init__(self):
        self.redis = None

    async def check_rate_limit(self,
                              key: str,
                              limit: int,
                              window_seconds: int = 60,
                              burst_multiplier: float = 1.5) -> Dict[str, Any]:
        """
        Check if request is within rate limit

        Args:
            key: Rate limit key (e.g., "tenant:123:api" or "user:456:api")
            limit: Max requests in window
            window_seconds: Time window in seconds
            burst_multiplier: Allow burst up to limit * multiplier

        Returns:
            Dict with:
                - allowed: bool
                - current: int (current count)
                - limit: int
                - remaining: int
                - reset_at: datetime

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        if not self.redis:
            self.redis = await get_redis_client()

        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        # Sliding window key
        rate_key = f"ratelimit:{key}:{window_seconds}s"

        # Use sorted set with timestamp scores
        # Remove old entries
        await self.redis.zremrangebyscore(
            rate_key,
            '-inf',
            window_start.timestamp()
        )

        # Count current requests in window
        current_count = await self.redis.zcard(rate_key)

        # Calculate limits
        base_limit = limit
        burst_limit = int(limit * burst_multiplier)

        # Check limit
        if current_count >= burst_limit:
            # Rate limit exceeded
            reset_at = now + timedelta(seconds=window_seconds)

            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded: {current_count}/{limit} requests in {window_seconds}s",
                    "limit": limit,
                    "current": current_count,
                    "reset_at": reset_at.isoformat(),
                    "retry_after": window_seconds
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_at.timestamp())),
                    "Retry-After": str(window_seconds)
                }
            )

        # Add current request
        request_id = f"{now.timestamp()}:{id(now)}"
        await self.redis.zadd(rate_key, {request_id: now.timestamp()})

        # Set expiration
        await self.redis.expire(rate_key, window_seconds * 2)

        # Calculate remaining
        remaining = max(0, limit - current_count - 1)

        # Reset time
        reset_at = now + timedelta(seconds=window_seconds)

        return {
            "allowed": True,
            "current": current_count + 1,
            "limit": limit,
            "remaining": remaining,
            "reset_at": reset_at
        }

    async def check_multi_window(self,
                                 key: str,
                                 limits: Dict[str, int]) -> Dict[str, Any]:
        """
        Check rate limits across multiple time windows

        Args:
            key: Base rate limit key
            limits: Dict of window -> limit
                    e.g., {"minute": 100, "hour": 1000, "day": 10000}

        Returns:
            Rate limit info from most restrictive window
        """
        results = []

        window_seconds = {
            "minute": 60,
            "hour": 3600,
            "day": 86400,
        }

        for window_name, limit in limits.items():
            seconds = window_seconds[window_name]
            result = await self.check_rate_limit(
                f"{key}:{window_name}",
                limit,
                seconds
            )
            results.append(result)

        # Return most restrictive
        return min(results, key=lambda r: r['remaining'])


class QuotaManager:
    """
    Manage tenant resource quotas and usage metering

    Tracks:
    - Storage usage (GB)
    - Number of datasets, models, policies
    - API calls
    - Job executions
    """

    def __init__(self, tenant_id: str, quotas: TenantQuotas):
        self.tenant_id = tenant_id
        self.quotas = quotas
        self.redis = None

    async def check_quota(self, resource: str, requested: int = 1) -> bool:
        """
        Check if quota allows requested resources

        Args:
            resource: Resource type (e.g., "datasets", "models", "storage_gb")
            requested: Amount requested

        Returns:
            True if within quota

        Raises:
            HTTPException: 403 if quota exceeded
        """
        if not self.redis:
            self.redis = await get_redis_client()

        # Get current usage
        current_usage = await self.get_usage(resource)

        # Get quota limit
        quota_limit = getattr(self.quotas, f"max_{resource}", None)

        if quota_limit is None:
            # No quota defined for this resource
            return True

        # Check if request would exceed quota
        if current_usage + requested > quota_limit:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "quota_exceeded",
                    "message": f"Quota exceeded for {resource}",
                    "resource": resource,
                    "current": current_usage,
                    "requested": requested,
                    "limit": quota_limit,
                    "plan": "Upgrade to increase limits"
                }
            )

        return True

    async def get_usage(self, resource: str) -> int:
        """Get current usage for a resource"""
        if not self.redis:
            self.redis = await get_redis_client()

        usage_key = f"usage:{self.tenant_id}:{resource}"

        usage = await self.redis.get(usage_key)

        if usage is None:
            # Initialize from database
            usage = await self._fetch_usage_from_db(resource)
            await self.redis.set(usage_key, usage, ex=300)  # 5 min cache

        return int(usage or 0)

    async def increment_usage(self, resource: str, amount: int = 1):
        """Increment usage counter"""
        if not self.redis:
            self.redis = await get_redis_client()

        usage_key = f"usage:{self.tenant_id}:{resource}"

        await self.redis.incrby(usage_key, amount)

        # Also log to metering table for billing
        await self._log_metering_event(resource, amount)

    async def decrement_usage(self, resource: str, amount: int = 1):
        """Decrement usage counter (e.g., when deleting a dataset)"""
        if not self.redis:
            self.redis = await get_redis_client()

        usage_key = f"usage:{self.tenant_id}:{resource}"

        await self.redis.decrby(usage_key, amount)

        await self._log_metering_event(resource, -amount)

    async def _fetch_usage_from_db(self, resource: str) -> int:
        """Fetch current usage from database"""
        # In production, query actual counts from database

        # Example:
        # if resource == "datasets":
        #     count = await db.execute(
        #         "SELECT COUNT(*) FROM datasets WHERE tenant_id = :tenant_id",
        #         {"tenant_id": self.tenant_id}
        #     )
        #     return count

        return 0

    async def _log_metering_event(self, resource: str, amount: int):
        """Log metering event for billing"""
        # In production, insert into metering table

        event = {
            "tenant_id": self.tenant_id,
            "resource": resource,
            "amount": amount,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Store in metering table
        # INSERT INTO metering_events (tenant_id, resource, amount, timestamp)
        # VALUES (:tenant_id, :resource, :amount, :timestamp)

        logger.debug(f"Metering event: {event}")


# Middleware integration

async def tenant_rate_limit_middleware(request: Request, tenant_id: str):
    """
    Apply rate limiting for tenant

    Usage in FastAPI:
        @app.get("/api/resource")
        async def get_resource(
            tenant_id: str = Depends(get_tenant_id),
            _: None = Depends(tenant_rate_limit_middleware)
        ):
            ...
    """
    # Get tenant plan and quotas
    # In production, fetch from database
    plan = Plan.PRO  # Example
    quotas = TenantQuotas.from_plan(plan)

    # Apply rate limiting
    rate_limiter = RateLimiter()

    limits = {
        "minute": quotas.max_api_calls_per_minute,
    }

    result = await rate_limiter.check_multi_window(
        f"tenant:{tenant_id}:api",
        limits
    )

    # Add rate limit headers to response
    request.state.rate_limit = result


async def quota_check_middleware(request: Request, tenant_id: str, resource: str):
    """
    Check quota before resource creation

    Usage:
        @app.post("/api/datasets")
        async def create_dataset(
            tenant_id: str = Depends(get_tenant_id),
            _: None = Depends(lambda: quota_check_middleware(request, tenant_id, "datasets"))
        ):
            ...
    """
    # Get tenant quotas
    plan = Plan.PRO  # In production, fetch from DB
    quotas = TenantQuotas.from_plan(plan)

    # Check quota
    quota_manager = QuotaManager(tenant_id, quotas)
    await quota_manager.check_quota(resource)
