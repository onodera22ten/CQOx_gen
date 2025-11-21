"""
Authentication API Routes

Endpoints:
- POST /auth/login - User login
- POST /auth/logout - User logout
- GET /auth/me - Get current user info
- POST /auth/refresh - Refresh access token
- POST /auth/change-password - Change password
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from cqox.db.database import get_db
from cqox.models.auth import (
    LoginRequest,
    LoginResponse,
    UserResponse,
    PasswordChangeRequest,
    RefreshTokenRequest
)
from cqox.services.auth_service import AuthService
from cqox.api.dependencies.auth import get_current_active_user
from cqox.db.models import User

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    User login with email and password

    Returns JWT access token and user information
    """
    # Authenticate user
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = AuthService.create_access_token(
        data={
            "sub": user.email,
            "user_id": str(user.id),
            "role": user.role,
            "tenant_id": str(user.tenant_id) if hasattr(user, 'tenant_id') and user.tenant_id else None
        }
    )

    # Create refresh token
    refresh_token = AuthService.create_refresh_token(
        data={
            "sub": user.email,
            "user_id": str(user.id),
            "role": user.role,
            "tenant_id": str(user.tenant_id) if hasattr(user, 'tenant_id') and user.tenant_id else None
        }
    )

    # Convert user to response model
    user_response = UserResponse.model_validate(user)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_response
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    User logout

    Note: For stateless JWT, logout is handled client-side by removing the token.
    This endpoint is provided for consistency and future extensions (e.g., token blacklist).
    """
    return {
        "message": "Successfully logged out",
        "user_email": current_user.email
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information
    """
    return UserResponse.model_validate(current_user)


@router.post("/refresh")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    # Verify refresh token
    token_data = AuthService.verify_token(refresh_data.refresh_token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Get user
    user = AuthService.get_user_by_id(db, token_data.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new access token
    access_token = AuthService.create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user password
    """
    # Verify old password
    if not AuthService.verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )

    # Update password
    current_user.password_hash = AuthService.get_password_hash(password_data.new_password)
    db.commit()

    return {
        "message": "Password changed successfully"
    }


@router.get("/health")
async def auth_health():
    """Health check for auth service"""
    return {"status": "ok", "service": "auth"}
