"""
Rate Limiting Middleware

APIのレート制限実装（Redis-based）
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Callable, Optional
import redis.asyncio as redis
import hashlib

from cqox.storage.redis_cache import get_redis_client
from loguru import logger


class RateLimiter:
    """
    Redis-based Rate Limiter
    
    **アルゴリズム**: Sliding Window Log
    
    **設定例**:
    - tier_free: 100 req/min
    - tier_basic: 1000 req/min
    - tier_premium: 10000 req/min
    - tier_enterprise: unlimited
    """
    
    def __init__(self,
                 requests_per_minute: int = 100,
                 burst_size: int = 20):
        """
        Args:
            requests_per_minute: 1分あたりのリクエスト数上限
            burst_size: バースト許容量（短時間の連続リクエスト）
        """
        self.rate = requests_per_minute
        self.burst = burst_size
        self.window = 60  # seconds
    
    async def check_rate_limit(self,
                               key: str,
                               requests: int = 1) -> tuple[bool, int, int]:
        """
        Rate limitをチェック
        
        Args:
            key: ユーザー/IPアドレス識別子
            requests: リクエスト数（デフォルト1）
        
        Returns:
            (allowed, remaining, reset_at): 
                - allowed: True if within limit
                - remaining: 残りリクエスト数
                - reset_at: リセット時刻（Unix timestamp）
        """
        try:
            redis_client = await get_redis_client()
            
            now = time.time()
            window_start = now - self.window
            
            # Sliding window key
            rate_key = f"rate_limit:{key}"
            
            # Remove old entries
            await redis_client.client.zremrangebyscore(rate_key, 0, window_start)
            
            # Count current requests in window
            current_requests = await redis_client.client.zcard(rate_key)
            
            # Check limit
            if current_requests >= self.rate:
                # Get oldest timestamp to calculate reset time
                oldest = await redis_client.client.zrange(rate_key, 0, 0, withscores=True)
                reset_at = int(oldest[0][1] + self.window) if oldest else int(now + self.window)
                return False, 0, reset_at
            
            # Add current request
            request_id = f"{now}:{hashlib.md5(str(time.time_ns()).encode()).hexdigest()[:8]}"
            await redis_client.client.zadd(rate_key, {request_id: now})
            
            # Set expiry
            await redis_client.client.expire(rate_key, self.window)
            
            remaining = self.rate - current_requests - 1
            reset_at = int(now + self.window)
            
            return True, remaining, reset_at
            
        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}. Allowing request.")
            # Fail open - allow request if Redis is down
            return True, self.rate, int(time.time() + self.window)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware for rate limiting
    
    **ヘッダー**:
    - X-RateLimit-Limit: 上限数
    - X-RateLimit-Remaining: 残り数
    - X-RateLimit-Reset: リセット時刻
    """
    
    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip health check and metrics endpoints
        if request.url.path in ["/health", "/metrics", "/api/docs", "/api/openapi.json"]:
            return await call_next(request)
        
        # Get identifier (prefer user_id, fallback to IP)
        identifier = self._get_identifier(request)
        
        # Check rate limit
        allowed, remaining, reset_at = await self.rate_limiter.check_rate_limit(identifier)
        
        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(self.rate_limiter.rate),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_at)
        }
        
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {self.rate_limiter.rate}/min",
                    "retry_after": reset_at - int(time.time())
                },
                headers={
                    **headers,
                    "Retry-After": str(reset_at - int(time.time()))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add headers to response
        for key, value in headers.items():
            response.headers[key] = value
        
        return response
    
    def _get_identifier(self, request: Request) -> str:
        """Get user/IP identifier for rate limiting"""
        # 1. Try to get user_id from auth
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get("sub") or request.state.user.get("user_id")
            if user_id:
                return f"user:{user_id}"
        
        # 2. Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Get real IP from X-Forwarded-For if behind proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        
        return f"ip:{client_ip}"


# Tier-based rate limiters
RATE_LIMITERS = {
    "free": RateLimiter(requests_per_minute=100, burst_size=20),
    "basic": RateLimiter(requests_per_minute=1000, burst_size=100),
    "premium": RateLimiter(requests_per_minute=10000, burst_size=500),
    "enterprise": RateLimiter(requests_per_minute=100000, burst_size=5000),
}


def get_rate_limiter_for_tier(tier: str) -> RateLimiter:
    """Get rate limiter based on subscription tier"""
    return RATE_LIMITERS.get(tier, RATE_LIMITERS["free"])

