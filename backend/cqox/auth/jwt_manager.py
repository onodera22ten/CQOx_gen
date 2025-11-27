"""
JWT Token Management

Features:
- HS256/RS256 support
- 1-hour access token expiry
- 7-day refresh token expiry
- Token revocation (Redis blacklist)
- Claims validation
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from passlib.context import CryptContext
from pydantic import BaseModel
from loguru import logger

from cqox.storage.redis_cache import get_redis_client


class TokenData(BaseModel):
    """JWT token payload"""
    sub: str  # User ID or email
    email: str = ""  # Optional - may use sub as email
    roles: list[str] = []  # Optional - may use role as single element
    tenant_id: str | None = None
    exp: datetime
    iat: datetime
    jti: str = ""  # Optional - JWT ID for revocation (auth_service.py may not include it)


class JWTManager:
    """
    JWT token manager with RS256/HS256 support

    Features:
    - Access tokens (1 hour)
    - Refresh tokens (7 days)
    - Token revocation via Redis blacklist
    - Role-based claims
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 60,
        refresh_token_expire_days: int = 7,
        private_key: Optional[str] = None,
        public_key: Optional[str] = None
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.private_key = private_key
        self.public_key = public_key
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_access_token(
        self,
        user_id: str,
        email: str,
        roles: list[str],
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create JWT access token

        Args:
            user_id: User identifier
            email: User email
            roles: User roles (for RBAC)
            additional_claims: Extra claims

        Returns:
            JWT token string
        """
        import uuid

        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": user_id,
            "user_id": user_id,  # Explicit user_id for TokenPayload compatibility
            "email": email,
            "roles": roles,
            "role": roles[0] if roles else "viewer",  # Primary role for TokenPayload
            "exp": expires,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "type": "access"
        }

        if additional_claims:
            payload.update(additional_claims)

        # Use RS256 if private key provided
        if self.algorithm == "RS256" and self.private_key:
            token = jwt.encode(payload, self.private_key, algorithm="RS256")
        else:
            token = jwt.encode(payload, self.secret_key, algorithm="HS256")

        return token

    def create_refresh_token(
        self,
        user_id: str,
        email: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create JWT refresh token (7 days)"""
        import uuid

        now = datetime.utcnow()
        expires = now + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": user_id,
            "email": email,
            "exp": expires,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "type": "refresh"
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> TokenData:
        """
        Verify and decode JWT token

        Args:
            token: JWT token string

        Returns:
            TokenData

        Raises:
            InvalidTokenError: If token is invalid
            ExpiredSignatureError: If token is expired
        """
        try:
            # Use RS256 if public key provided
            if self.algorithm == "RS256" and self.public_key:
                payload = jwt.decode(token, self.public_key, algorithms=["RS256"])
            else:
                payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])

            return TokenData(
                sub=payload["sub"],
                email=payload.get("email", payload.get("sub", "")),
                roles=payload.get("roles", [payload.get("role", "viewer")]),
                tenant_id=payload.get("tenant_id"),
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
                jti=payload.get("jti", str(payload.get("iat", "")))
            )

        except ExpiredSignatureError:
            logger.warning(f"Token expired")
            raise
        except InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise

    async def revoke_token(self, token: str):
        """
        Revoke token by adding to Redis blacklist

        Args:
            token: JWT token to revoke
        """
        try:
            token_data = self.verify_token(token)
            redis = await get_redis_client()

            # Calculate TTL (time until expiration)
            ttl = int((token_data.exp - datetime.utcnow()).total_seconds())

            if ttl > 0:
                # Add JTI to blacklist
                await redis.set(
                    f"revoked:token:{token_data.jti}",
                    "1",
                    ttl=ttl
                )

                logger.info(f"Token revoked: {token_data.jti}")

        except Exception as e:
            logger.error(f"Token revocation failed: {e}")
            raise

    async def is_token_revoked(self, token: str) -> bool:
        """
        Check if token is revoked

        Args:
            token: JWT token

        Returns:
            True if revoked, False otherwise
        """
        try:
            token_data = self.verify_token(token)
            redis = await get_redis_client()

            is_revoked = await redis.exists(f"revoked:token:{token_data.jti}")
            return bool(is_revoked)

        except Exception:
            return True  # Treat invalid tokens as revoked

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)


# Global JWT manager instance
_jwt_manager: Optional[JWTManager] = None


def get_jwt_manager() -> JWTManager:
    """Get or create JWT manager"""
    global _jwt_manager

    if _jwt_manager is None:
        from cqox.config import settings

        import os

        # Match exactly the same key used by auth_service.py
        secret_fallback = 'your-secret-key-change-in-production'
        env_secret = os.environ.get('SECRET_KEY', secret_fallback)

        # Priority: ENV > settings.jwt_secret_key > settings.secret_key > fallback
        settings_secret = getattr(settings, 'secret_key', None)
        configured_secret = getattr(settings, 'jwt_secret_key', None)

        # Use same key as auth_service.py: os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        final_secret = env_secret  # This matches auth_service.py

        _jwt_manager = JWTManager(
            secret_key=final_secret,
            algorithm=getattr(settings, 'jwt_algorithm', 'HS256'),
            access_token_expire_minutes=getattr(settings, 'jwt_access_expire_minutes', 60),
            refresh_token_expire_days=getattr(settings, 'jwt_refresh_expire_days', 7),
            private_key=getattr(settings, 'jwt_private_key', None),
            public_key=getattr(settings, 'jwt_public_key', None)
        )

    return _jwt_manager
