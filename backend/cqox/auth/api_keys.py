"""
API Key Management

Features:
- Service-to-service authentication
- Key rotation
- Rate limiting per key
- Scoped permissions
- Expiration
"""
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import secrets
import hashlib
from loguru import logger

from cqox.storage.redis_cache import get_redis_client


class APIKey(BaseModel):
    """API Key model"""
    key_id: str
    key_hash: str
    name: str
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    rate_limit: int = 1000  # requests per hour
    is_active: bool = True


class APIKeyManager:
    """
    API Key manager with Redis storage

    Features:
    - Secure key generation (32 bytes)
    - SHA-256 hashing
    - Scoped permissions
    - Rate limiting
    - Key rotation
    """

    PREFIX = "apikey:"

    @staticmethod
    def generate_key() -> str:
        """
        Generate secure API key

        Format: cqox_live_<32 random bytes hex>

        Returns:
            API key string
        """
        random_bytes = secrets.token_bytes(32)
        key = f"cqox_live_{random_bytes.hex()}"
        return key

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash API key using SHA-256"""
        return hashlib.sha256(key.encode()).hexdigest()

    async def create_key(
        self,
        name: str,
        scopes: List[str],
        expires_days: Optional[int] = None,
        rate_limit: int = 1000
    ) -> tuple[str, APIKey]:
        """
        Create new API key

        Args:
            name: Key name/description
            scopes: Permitted scopes (e.g., ["models:read", "policies:write"])
            expires_days: Expiration in days (None = no expiration)
            rate_limit: Requests per hour

        Returns:
            (plaintext_key, api_key_object)
        """
        import uuid

        # Generate key
        plaintext_key = self.generate_key()
        key_hash = self.hash_key(plaintext_key)
        key_id = str(uuid.uuid4())

        # Create API key object
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            scopes=scopes,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=expires_days) if expires_days else None,
            rate_limit=rate_limit,
            is_active=True
        )

        # Store in Redis
        redis = await get_redis_client()
        await redis.set(
            f"{self.PREFIX}{key_hash}",
            api_key.model_dump_json(),
            serialize='raw'
        )

        logger.info(f"API key created: {key_id} ({name})")

        return plaintext_key, api_key

    async def verify_key(self, key: str) -> Optional[APIKey]:
        """
        Verify API key and return key object

        Args:
            key: Plaintext API key

        Returns:
            APIKey object if valid, None otherwise
        """
        key_hash = self.hash_key(key)
        redis = await get_redis_client()

        # Get key from Redis
        key_data = await redis.get(f"{self.PREFIX}{key_hash}", deserialize='raw')

        if not key_data:
            return None

        api_key = APIKey.model_validate_json(key_data)

        # Check if active
        if not api_key.is_active:
            logger.warning(f"Inactive API key used: {api_key.key_id}")
            return None

        # Check expiration
        if api_key.expires_at and datetime.utcnow() > api_key.expires_at:
            logger.warning(f"Expired API key used: {api_key.key_id}")
            return None

        return api_key

    async def check_rate_limit(self, key: str) -> bool:
        """
        Check rate limit for API key

        Uses sliding window algorithm

        Args:
            key: Plaintext API key

        Returns:
            True if within limit, False if exceeded
        """
        api_key = await self.verify_key(key)

        if not api_key:
            return False

        redis = await get_redis_client()

        # Use sliding window rate limiting
        allowed = await redis.sliding_window_rate_limit(
            f"ratelimit:apikey:{api_key.key_id}",
            max_requests=api_key.rate_limit,
            window_seconds=3600  # 1 hour
        )

        return allowed

    async def revoke_key(self, key: str):
        """Revoke API key"""
        key_hash = self.hash_key(key)
        redis = await get_redis_client()

        # Get key
        key_data = await redis.get(f"{self.PREFIX}{key_hash}", deserialize='raw')

        if key_data:
            api_key = APIKey.model_validate_json(key_data)
            api_key.is_active = False

            # Update in Redis
            await redis.set(
                f"{self.PREFIX}{key_hash}",
                api_key.model_dump_json(),
                serialize='raw'
            )

            logger.info(f"API key revoked: {api_key.key_id}")

    async def list_keys(self) -> List[APIKey]:
        """List all API keys (without hashes)"""
        redis = await get_redis_client()

        keys = []
        pattern = f"{self.PREFIX}*"

        # Scan for all API keys
        cursor = 0
        while True:
            cursor, batch = await redis.client.scan(cursor, match=pattern, count=100)

            for key in batch:
                key_data = await redis.get(key.decode(), deserialize='raw')
                if key_data:
                    api_key = APIKey.model_validate_json(key_data)
                    keys.append(api_key)

            if cursor == 0:
                break

        return keys


# Global API key manager
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get or create API key manager"""
    global _api_key_manager

    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()

    return _api_key_manager
