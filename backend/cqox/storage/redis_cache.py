"""
Redis cache client with advanced features

Features:
- Rate limiting (Token Bucket + Sliding Window)
- Distributed locking
- Cache warming
- Cache tagging
- Automatic serialization
"""
import redis.asyncio as aioredis
from typing import Optional, Any, List, Dict
from datetime import timedelta
import json
import pickle
import hashlib
import os
from loguru import logger
from pydantic import BaseModel


class CacheConfig(BaseModel):
    """Cache configuration"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 50
    decode_responses: bool = False


class RedisCache:
    """
    Advanced Redis cache client

    Features:
    - Automatic serialization (JSON/Pickle)
    - Connection pooling
    - Cache invalidation patterns
    - Distributed rate limiting
    - Circuit breaker integration
    """

    def __init__(self, config: CacheConfig):
        self.config = config
        self.client: Optional[aioredis.Redis] = None

    async def connect(self):
        """Initialize Redis connection pool"""
        # Prefer environment variable REDIS_URL
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            self.client = await aioredis.from_url(
                redis_url,
                max_connections=self.config.max_connections,
                decode_responses=self.config.decode_responses
            )
            logger.info(f"Redis connected from REDIS_URL: {redis_url}")
        else:
            self.client = await aioredis.from_url(
                f"redis://{self.config.host}:{self.config.port}/{self.config.db}",
                password=self.config.password,
                max_connections=self.config.max_connections,
                decode_responses=self.config.decode_responses
            )
            logger.info(f"Redis connected: {self.config.host}:{self.config.port}")

    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")

    async def get(self, key: str, deserialize: str = 'json') -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key
            deserialize: 'json', 'pickle', or 'raw'

        Returns:
            Cached value or None
        """
        value = await self.client.get(key)

        if value is None:
            return None

        if deserialize == 'json':
            return json.loads(value)
        elif deserialize == 'pickle':
            return pickle.loads(value)
        else:
            return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize: str = 'json'
    ):
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            serialize: 'json', 'pickle', or 'raw'
        """
        if serialize == 'json':
            data = json.dumps(value)
        elif serialize == 'pickle':
            data = pickle.dumps(value)
        else:
            data = value

        if ttl:
            await self.client.setex(key, ttl, data)
        else:
            await self.client.set(key, data)

    async def delete(self, *keys: str):
        """Delete one or more keys"""
        await self.client.delete(*keys)

    async def exists(self, *keys: str) -> int:
        """Check if keys exist"""
        return await self.client.exists(*keys)

    async def expire(self, key: str, ttl: int):
        """Set expiration on key"""
        await self.client.expire(key, ttl)

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment value"""
        return await self.client.incrby(key, amount)

    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement value"""
        return await self.client.decrby(key, amount)

    # Rate Limiting (Token Bucket)
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Token bucket rate limiting

        Args:
            key: Rate limit key (e.g., "rate:user:123")
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if allowed, False if rate limited
        """
        current = await self.client.get(key)

        if current is None:
            # First request
            await self.client.setex(key, window_seconds, 1)
            return True

        count = int(current)

        if count >= max_requests:
            return False

        await self.client.incr(key)
        return True

    # Sliding Window Rate Limiting (more accurate)
    async def sliding_window_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Sliding window rate limiting using sorted sets

        More accurate than token bucket for burst traffic

        Args:
            key: Rate limit key
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if allowed, False if rate limited
        """
        import time

        now = time.time()
        window_start = now - window_seconds

        pipe = self.client.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count requests in window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Set expiration
        pipe.expire(key, window_seconds)

        results = await pipe.execute()

        count = results[1]

        return count < max_requests

    # Distributed Lock
    async def acquire_lock(
        self,
        lock_key: str,
        timeout: int = 10,
        blocking_timeout: Optional[int] = None
    ) -> bool:
        """
        Acquire distributed lock

        Args:
            lock_key: Lock identifier
            timeout: Lock timeout in seconds
            blocking_timeout: Wait time for lock acquisition

        Returns:
            True if acquired, False otherwise
        """
        if blocking_timeout is None:
            # Non-blocking
            return await self.client.set(
                f"lock:{lock_key}",
                "1",
                ex=timeout,
                nx=True
            )
        else:
            # Blocking with timeout
            import time
            start = time.time()

            while time.time() - start < blocking_timeout:
                acquired = await self.client.set(
                    f"lock:{lock_key}",
                    "1",
                    ex=timeout,
                    nx=True
                )

                if acquired:
                    return True

                await asyncio.sleep(0.1)

            return False

    async def release_lock(self, lock_key: str):
        """Release distributed lock"""
        await self.client.delete(f"lock:{lock_key}")

    # Cache Tags
    async def add_tag(self, key: str, *tags: str):
        """Add tags to a cache key"""
        for tag in tags:
            await self.client.sadd(f"tag:{tag}", key)

    async def invalidate_by_tag(self, tag: str):
        """Invalidate all keys with a specific tag"""
        keys = await self.client.smembers(f"tag:{tag}")

        if keys:
            await self.client.delete(*keys)
            await self.client.delete(f"tag:{tag}")

    # Cache Warming
    async def warm_cache(self, key: str, loader_func, ttl: int = 3600):
        """
        Warm cache with data from loader function

        Args:
            key: Cache key
            loader_func: Async function to load data
            ttl: Cache TTL
        """
        data = await loader_func()
        await self.set(key, data, ttl=ttl)
        logger.info(f"Cache warmed: {key}")

    # Pattern Operations
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        keys = []
        async for key in self.client.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            await self.client.delete(*keys)
            logger.info(f"Deleted {len(keys)} keys matching pattern: {pattern}")

    # Health Check
    async def ping(self) -> bool:
        """Check Redis connection"""
        try:
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    # Statistics
    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis statistics"""
        info = await self.client.info()

        return {
            'version': info['redis_version'],
            'connected_clients': info['connected_clients'],
            'used_memory': info['used_memory_human'],
            'used_memory_peak': info['used_memory_peak_human'],
            'total_commands_processed': info['total_commands_processed'],
            'instantaneous_ops_per_sec': info['instantaneous_ops_per_sec'],
            'keyspace_hits': info['keyspace_hits'],
            'keyspace_misses': info['keyspace_misses'],
            'evicted_keys': info['evicted_keys']
        }


# Helper functions
def generate_cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_data = f"{args}:{kwargs}"
    return hashlib.md5(key_data.encode()).hexdigest()


# Global client instance
_redis_client: Optional[RedisCache] = None


async def get_redis_client() -> RedisCache:
    """Get or create Redis client"""
    global _redis_client

    if _redis_client is None:
        from cqox.config import settings

        config = CacheConfig(
            host=getattr(settings, 'redis_host', 'localhost'),
            port=getattr(settings, 'redis_port', 6379),
            db=getattr(settings, 'redis_db', 0),
            password=getattr(settings, 'redis_password', None)
        )

        _redis_client = RedisCache(config)
        await _redis_client.connect()

    return _redis_client
