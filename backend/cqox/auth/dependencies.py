"""
Authentication Dependencies
FastAPI dependency functions for authentication and authorization
"""

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging

from cqox.auth.jwt_manager import get_jwt_manager, TokenData

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current user from JWT token

    Returns:
        Dict with user_id, email, roles, tenant_id

    Raises:
        HTTPException: If not authenticated or token invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    jwt_manager = get_jwt_manager()

    try:
        token_data = jwt_manager.verify_token(credentials.credentials)

        # Check if token is revoked
        is_revoked = await jwt_manager.is_token_revoked(credentials.credentials)
        if is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )

        # Extract user data
        user = {
            "user_id": token_data.sub,
            "email": token_data.email,
            "roles": token_data.roles,
            "tenant_id": getattr(token_data, 'tenant_id', 'default_tenant')
        }

        return user

    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current user (optional, returns None if not authenticated)

    Returns:
        User dict or None
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def get_tenant_id(
    current_user: Dict[str, Any] = Depends(get_current_user),
    x_tenant_id: Optional[str] = Header(None)
) -> str:
    """
    Get tenant ID from user context or header

    Priority:
    1. X-Tenant-ID header (for cross-tenant admin operations)
    2. User's default tenant_id from token

    Returns:
        Tenant ID string

    Raises:
        HTTPException: If tenant_id cannot be determined
    """
    # Check header first (for admin cross-tenant operations)
    if x_tenant_id:
        # Verify user has permission to access this tenant
        # In production, check if user has cross-tenant permission
        if "admin" in current_user.get("roles", []):
            return x_tenant_id
        else:
            # Non-admin users cannot override tenant
            logger.warning(f"User {current_user['user_id']} attempted to access tenant {x_tenant_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-tenant access denied"
            )

    # Use user's tenant
    tenant_id = current_user.get("tenant_id")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID not found in user context"
        )

    return tenant_id


async def require_role(required_role: str):
    """
    Dependency factory to require specific role

    Usage:
        @router.get("/admin")
        async def admin_only(
            user: dict = Depends(get_current_user),
            _: None = Depends(require_role("admin"))
        ):
            ...
    """
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if required_role not in current_user.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )

    return role_checker
