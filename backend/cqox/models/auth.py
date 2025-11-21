"""
Authentication Models - Pydantic schemas for API requests/responses

これらのモデルはAPIのリクエスト/レスポンスで使用されます。
データベースモデルは別途 db/models.py で定義します。
"""
from datetime import datetime
from typing import Optional, List, Union
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Base User Models
class UserBase(BaseModel):
    """Base user fields"""
    email: EmailStr = Field(..., description="User email address")


class UserCreate(UserBase):
    """User creation request"""
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    role: str = Field(default="viewer", description="User role: admin, analyst, viewer")


class UserUpdate(BaseModel):
    """User update request"""
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response (excludes password)"""
    id: Union[int, UUID]
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserResponse):
    """User as stored in database (includes password hash)"""
    password_hash: str


# Authentication Request/Response Models
class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Login response with access token"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="Authenticated user info")


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str = Field(..., description="Subject (user email)")
    user_id: Union[int, str] = Field(..., description="User ID (int or UUID string)")
    role: str = Field(..., description="User role")
    tenant_id: Optional[Union[str, UUID]] = Field(None, description="Tenant ID")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(..., description="Refresh token")


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    "LoginRequest",
    "LoginResponse",
    "TokenPayload",
    "RefreshTokenRequest",
    "PasswordChangeRequest",
]
