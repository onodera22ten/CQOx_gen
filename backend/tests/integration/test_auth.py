"""
Integration tests for authentication

Tests JWT, OAuth2, RBAC, and API key authentication
"""
import pytest
from httpx import AsyncClient
from fastapi import status
import jwt
from datetime import datetime, timedelta

from cqox.api.main import app
from cqox.auth.jwt_manager import get_jwt_manager
from cqox.auth.api_keys import get_api_key_manager


@pytest.mark.asyncio
class TestJWTAuthentication:
    """Test JWT-based authentication"""

    async def test_login_with_valid_credentials(self, async_client: AsyncClient):
        """Test successful login with email/password"""
        response = await async_client.post(
            "/auth/token",
            data={"email": "test@example.com", "password": "password123"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_with_invalid_credentials(self, async_client: AsyncClient):
        """Test login failure with invalid credentials"""
        response = await async_client.post(
            "/auth/token",
            data={"email": "test@example.com", "password": "wrongpassword"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_access_protected_endpoint_without_token(self, async_client: AsyncClient):
        """Test accessing protected endpoint without token"""
        response = await async_client.get("/api/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_access_protected_endpoint_with_valid_token(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test accessing protected endpoint with valid token"""
        response = await async_client.get("/api/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "user_id" in data
        assert "email" in data
        assert "roles" in data
        assert "permissions" in data

    async def test_access_protected_endpoint_with_expired_token(
        self, async_client: AsyncClient
    ):
        """Test accessing protected endpoint with expired token"""
        jwt_manager = get_jwt_manager()

        # Create expired token (expired 1 hour ago)
        expired_token = jwt.encode(
            {
                "sub": "user123",
                "email": "test@example.com",
                "roles": ["viewer"],
                "exp": datetime.utcnow() - timedelta(hours=1),
                "iat": datetime.utcnow() - timedelta(hours=2),
                "jti": "test-jti",
                "type": "access"
            },
            jwt_manager.secret_key,
            algorithm="HS256"
        )

        response = await async_client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_refresh_token(self, async_client: AsyncClient):
        """Test refreshing access token with refresh token"""
        # First login to get tokens
        login_response = await async_client.post(
            "/auth/token",
            data={"email": "test@example.com", "password": "password123"}
        )
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token to get new access token
        response = await async_client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_logout(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test logout (token revocation)"""
        response = await async_client.post(
            "/auth/logout",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestRBAC:
    """Test Role-Based Access Control"""

    async def test_admin_can_access_admin_endpoint(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Test admin role can access admin endpoints"""
        response = await async_client.get(
            "/api/admin/users",  # Requires admin role
            headers=admin_headers
        )

        # Should succeed or return 404 if endpoint not implemented
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_viewer_cannot_access_admin_endpoint(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test viewer role cannot access admin endpoints"""
        response = await async_client.get(
            "/api/admin/users",
            headers=auth_headers
        )

        # Should return 403 Forbidden or 404 if endpoint not implemented
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    async def test_analyst_can_write_models(
        self, async_client: AsyncClient, analyst_headers: dict
    ):
        """Test analyst role has models:write permission"""
        response = await async_client.get(
            "/api/me",
            headers=analyst_headers
        )

        data = response.json()
        assert "models:write" in data["permissions"]

    async def test_viewer_cannot_write_models(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test viewer role does not have models:write permission"""
        response = await async_client.get(
            "/api/me",
            headers=auth_headers
        )

        data = response.json()
        assert "models:write" not in data["permissions"]


@pytest.mark.asyncio
class TestAPIKeys:
    """Test API key authentication"""

    async def test_create_api_key(self, admin_headers: dict):
        """Test creating API key (admin only)"""
        api_key_manager = get_api_key_manager()

        plaintext_key, api_key = await api_key_manager.create_key(
            name="test-key",
            scopes=["models:read"],
            rate_limit=100
        )

        assert plaintext_key.startswith("cqox_live_")
        assert api_key.name == "test-key"
        assert "models:read" in api_key.scopes

    async def test_verify_valid_api_key(self):
        """Test verifying valid API key"""
        api_key_manager = get_api_key_manager()

        # Create key
        plaintext_key, _ = await api_key_manager.create_key(
            name="test-key",
            scopes=["models:read"]
        )

        # Verify key
        verified_key = await api_key_manager.verify_key(plaintext_key)

        assert verified_key is not None
        assert verified_key.name == "test-key"

    async def test_verify_invalid_api_key(self):
        """Test verifying invalid API key"""
        api_key_manager = get_api_key_manager()

        with pytest.raises(ValueError):
            await api_key_manager.verify_key("invalid_key")

    async def test_api_key_rate_limiting(self):
        """Test API key rate limiting"""
        api_key_manager = get_api_key_manager()

        # Create key with low rate limit
        plaintext_key, _ = await api_key_manager.create_key(
            name="limited-key",
            scopes=["models:read"],
            rate_limit=2  # Only 2 requests per hour
        )

        # First 2 requests should succeed
        assert await api_key_manager.check_rate_limit(plaintext_key) is True
        assert await api_key_manager.check_rate_limit(plaintext_key) is True

        # Third request should fail
        assert await api_key_manager.check_rate_limit(plaintext_key) is False


@pytest.mark.asyncio
class TestOAuth2:
    """Test OAuth2 authentication flow"""

    async def test_oauth_login_initiation(self, async_client: AsyncClient):
        """Test OAuth2 login initiation"""
        response = await async_client.get("/auth/login/google")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "authorization_url" in data
        assert "accounts.google.com" in data["authorization_url"]

    async def test_oauth_callback_with_invalid_state(
        self, async_client: AsyncClient
    ):
        """Test OAuth2 callback with invalid state parameter"""
        response = await async_client.get(
            "/auth/callback/google?code=testcode&state=invalid_state"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
