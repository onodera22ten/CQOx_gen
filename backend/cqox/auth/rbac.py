"""
Role-Based Access Control (RBAC)

Roles:
- admin: Full access
- analyst: Read/write for analysis
- viewer: Read-only access

Permissions:
- models:read, models:write, models:delete
- policies:read, policies:write, policies:delete
- diagnostics:read
- users:read, users:write
"""
from enum import Enum
from typing import List, Set
from functools import wraps
from fastapi import HTTPException, status
from pydantic import BaseModel


class Role(str, Enum):
    """User roles"""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Granular permissions"""
    # Models
    MODELS_READ = "models:read"
    MODELS_WRITE = "models:write"
    MODELS_DELETE = "models:delete"

    # Policies
    POLICIES_READ = "policies:read"
    POLICIES_WRITE = "policies:write"
    POLICIES_DELETE = "policies:delete"

    # Diagnostics
    DIAGNOSTICS_READ = "diagnostics:read"
    DIAGNOSTICS_WRITE = "diagnostics:write"

    # Users
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"

    # Data
    DATA_UPLOAD = "data:upload"
    DATA_EXPORT = "data:export"


# Role-Permission mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # Full access
        Permission.MODELS_READ,
        Permission.MODELS_WRITE,
        Permission.MODELS_DELETE,
        Permission.POLICIES_READ,
        Permission.POLICIES_WRITE,
        Permission.POLICIES_DELETE,
        Permission.DIAGNOSTICS_READ,
        Permission.DIAGNOSTICS_WRITE,
        Permission.USERS_READ,
        Permission.USERS_WRITE,
        Permission.USERS_DELETE,
        Permission.DATA_UPLOAD,
        Permission.DATA_EXPORT,
    },
    Role.ANALYST: {
        # Read/write for analysis, no delete
        Permission.MODELS_READ,
        Permission.MODELS_WRITE,
        Permission.POLICIES_READ,
        Permission.POLICIES_WRITE,
        Permission.DIAGNOSTICS_READ,
        Permission.DIAGNOSTICS_WRITE,
        Permission.DATA_UPLOAD,
        Permission.DATA_EXPORT,
    },
    Role.VIEWER: {
        # Read-only
        Permission.MODELS_READ,
        Permission.POLICIES_READ,
        Permission.DIAGNOSTICS_READ,
    }
}


class RBACManager:
    """Role-Based Access Control manager"""

    @staticmethod
    def has_permission(roles: List[str], required_permission: Permission) -> bool:
        """
        Check if user has required permission

        Args:
            roles: User's roles
            required_permission: Required permission

        Returns:
            True if user has permission
        """
        for role_str in roles:
            try:
                role = Role(role_str)
                permissions = ROLE_PERMISSIONS.get(role, set())
                if required_permission in permissions:
                    return True
            except ValueError:
                continue

        return False

    @staticmethod
    def has_role(roles: List[str], required_role: Role) -> bool:
        """Check if user has required role"""
        return required_role.value in roles

    @staticmethod
    def get_permissions(roles: List[str]) -> Set[Permission]:
        """Get all permissions for user's roles"""
        all_permissions = set()

        for role_str in roles:
            try:
                role = Role(role_str)
                permissions = ROLE_PERMISSIONS.get(role, set())
                all_permissions.update(permissions)
            except ValueError:
                continue

        return all_permissions


# Dependency for FastAPI
def require_permission(permission: Permission):
    """
    Decorator/dependency to require specific permission

    Usage:
        @router.get("/models")
        @require_permission(Permission.MODELS_READ)
        async def get_models():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from request
            # This would be injected via FastAPI dependency
            current_user = kwargs.get('current_user')

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )

            # Check permission
            if not RBACManager.has_permission(current_user.roles, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value} required"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_role(role: Role):
    """
    Decorator/dependency to require specific role

    Usage:
        @router.delete("/users/{user_id}")
        @require_role(Role.ADMIN)
        async def delete_user(user_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )

            if not RBACManager.has_role(current_user.roles, role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {role.value}"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
