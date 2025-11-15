"""
Admin API Routes

User management, role assignment, audit logs, and system configuration.

**Requires admin role for all endpoints.**
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid

from cqox.auth.jwt_manager import get_jwt_manager, TokenData
from cqox.auth.rbac import RBACManager, Role, Permission
from cqox.storage.postgres_client import get_postgres_client
from cqox.compliance.gdpr_handler import get_gdpr_handler, DataCategory
from cqox.validation.input_validator import PaginationParams


router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================================
# Models
# ============================================================================

class UserCreate(BaseModel):
    """Create user request"""
    email: EmailStr
    name: str
    password: str
    roles: List[str] = ["viewer"]


class UserUpdate(BaseModel):
    """Update user request"""
    name: Optional[str] = None
    roles: Optional[List[str]] = None
    active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response"""
    id: str
    email: str
    name: str
    roles: List[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    anonymized: bool


class AuditLogResponse(BaseModel):
    """Audit log response"""
    id: str
    user_id: str
    accessed_by: str
    data_category: str
    action: str
    timestamp: datetime
    ip_address: Optional[str]
    reason: Optional[str]


class SystemStatsResponse(BaseModel):
    """System statistics response"""
    total_users: int
    active_users: int
    total_model_runs: int
    total_policies: int
    total_api_requests_today: int
    storage_used_gb: float


# ============================================================================
# Dependencies
# ============================================================================

async def require_admin(
    credentials=Depends(HTTPBearer(auto_error=True))
) -> TokenData:
    """Require admin role"""
    jwt_manager = get_jwt_manager()

    try:
        token_data = jwt_manager.verify_token(credentials.credentials)

        if not RBACManager.has_permission(token_data.roles, Permission.USERS_WRITE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required"
            )

        return token_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


# ============================================================================
# User Management Endpoints
# ============================================================================

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    pagination: PaginationParams = Depends(),
    role: Optional[str] = Query(None, description="Filter by role"),
    active_only: bool = Query(True, description="Show only active users"),
    admin: TokenData = Depends(require_admin)
):
    """
    List all users

    **Permissions**: Requires admin role
    """
    db = await get_postgres_client()

    # Build query
    where_clauses = []
    params = []
    param_count = 1

    if active_only:
        where_clauses.append("deleted_at IS NULL")

    if role:
        where_clauses.append(f"${param_count} = ANY(roles)")
        params.append(role)
        param_count += 1

    where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"

    query = f"""
        SELECT id, email, name, roles, created_at, updated_at, deleted_at, anonymized
        FROM users
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([pagination.limit, pagination.offset])

    users = await db.fetch(query, *params)

    return [UserResponse(**dict(user)) for user in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    admin: TokenData = Depends(require_admin)
):
    """
    Get user by ID

    **Permissions**: Requires admin role
    """
    db = await get_postgres_client()

    user = await db.fetchrow(
        """
        SELECT id, email, name, roles, created_at, updated_at, deleted_at, anonymized
        FROM users
        WHERE id = $1
        """,
        user_id
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(**dict(user))


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    admin: TokenData = Depends(require_admin)
):
    """
    Create new user

    **Permissions**: Requires admin role
    """
    db = await get_postgres_client()
    jwt_manager = get_jwt_manager()

    # Check if user already exists
    existing = await db.fetchrow(
        "SELECT id FROM users WHERE email = $1",
        user_data.email
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )

    # Hash password
    password_hash = jwt_manager.hash_password(user_data.password)

    # Create user
    user_id = str(uuid.uuid4())
    now = datetime.utcnow()

    await db.execute(
        """
        INSERT INTO users (id, email, name, password_hash, roles, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        user_id,
        user_data.email,
        user_data.name,
        password_hash,
        user_data.roles,
        now,
        now
    )

    return UserResponse(
        id=user_id,
        email=user_data.email,
        name=user_data.name,
        roles=user_data.roles,
        created_at=now,
        updated_at=now,
        deleted_at=None,
        anonymized=False
    )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    admin: TokenData = Depends(require_admin)
):
    """
    Update user

    **Permissions**: Requires admin role
    """
    db = await get_postgres_client()

    # Check if user exists
    existing = await db.fetchrow(
        "SELECT * FROM users WHERE id = $1",
        user_id
    )

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Build update query
    updates = []
    params = []
    param_count = 1

    if user_data.name is not None:
        updates.append(f"name = ${param_count}")
        params.append(user_data.name)
        param_count += 1

    if user_data.roles is not None:
        updates.append(f"roles = ${param_count}")
        params.append(user_data.roles)
        param_count += 1

    if user_data.active is not None:
        if user_data.active:
            updates.append("deleted_at = NULL")
        else:
            updates.append(f"deleted_at = ${param_count}")
            params.append(datetime.utcnow())
            param_count += 1

    updates.append(f"updated_at = ${param_count}")
    params.append(datetime.utcnow())
    param_count += 1

    # Add user_id to params
    params.append(user_id)

    query = f"""
        UPDATE users
        SET {", ".join(updates)}
        WHERE id = ${param_count}
        RETURNING id, email, name, roles, created_at, updated_at, deleted_at, anonymized
    """

    updated_user = await db.fetchrow(query, *params)

    return UserResponse(**dict(updated_user))


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    permanent: bool = Query(False, description="Permanently delete (GDPR erasure)"),
    admin: TokenData = Depends(require_admin)
):
    """
    Delete user (soft delete by default)

    **Permissions**: Requires admin role

    - **Soft delete** (default): Mark as deleted, keep data for compliance
    - **Permanent delete** (GDPR): Anonymize and erase personal data
    """
    db = await get_postgres_client()
    gdpr_handler = get_gdpr_handler()

    # Check if user exists
    existing = await db.fetchrow(
        "SELECT * FROM users WHERE id = $1",
        user_id
    )

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if permanent:
        # GDPR erasure
        await gdpr_handler.erase_user_data(
            user_id=user_id,
            requester_id=admin.sub,
            reason="Admin-initiated deletion"
        )
    else:
        # Soft delete
        await db.execute(
            """
            UPDATE users
            SET deleted_at = $1, updated_at = $1
            WHERE id = $2
            """,
            datetime.utcnow(),
            user_id
        )


# ============================================================================
# Audit Log Endpoints
# ============================================================================

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    pagination: PaginationParams = Depends(),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    data_category: Optional[str] = Query(None, description="Filter by data category"),
    admin: TokenData = Depends(require_admin)
):
    """
    List audit logs

    **Permissions**: Requires admin role
    """
    db = await get_postgres_client()

    # Build query
    where_clauses = []
    params = []
    param_count = 1

    if user_id:
        where_clauses.append(f"user_id = ${param_count}")
        params.append(user_id)
        param_count += 1

    if action:
        where_clauses.append(f"action = ${param_count}")
        params.append(action)
        param_count += 1

    if data_category:
        where_clauses.append(f"data_category = ${param_count}")
        params.append(data_category)
        param_count += 1

    where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"

    query = f"""
        SELECT id, user_id, accessed_by, data_category, action, timestamp, ip_address, reason
        FROM data_access_logs
        WHERE {where_sql}
        ORDER BY timestamp DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([pagination.limit, pagination.offset])

    logs = await db.fetch(query, *params)

    return [AuditLogResponse(**dict(log)) for log in logs]


# ============================================================================
# System Statistics
# ============================================================================

@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    admin: TokenData = Depends(require_admin)
):
    """
    Get system statistics

    **Permissions**: Requires admin role
    """
    db = await get_postgres_client()

    # Total users
    total_users = await db.fetchval(
        "SELECT COUNT(*) FROM users"
    )

    # Active users (not deleted)
    active_users = await db.fetchval(
        "SELECT COUNT(*) FROM users WHERE deleted_at IS NULL"
    )

    # Total model runs
    total_model_runs = await db.fetchval(
        "SELECT COUNT(*) FROM model_runs"
    ) or 0

    # Total policies
    total_policies = await db.fetchval(
        "SELECT COUNT(*) FROM policies"
    ) or 0

    # API requests today (from metrics table if available)
    total_api_requests_today = 0  # TODO: Query from TimescaleDB metrics

    # Storage used (placeholder)
    storage_used_gb = 0.0  # TODO: Calculate actual storage

    return SystemStatsResponse(
        total_users=total_users,
        active_users=active_users,
        total_model_runs=total_model_runs,
        total_policies=total_policies,
        total_api_requests_today=total_api_requests_today,
        storage_used_gb=storage_used_gb
    )
