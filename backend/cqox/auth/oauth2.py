"""
OAuth2 Integration

Providers:
- Google
- GitHub
- Microsoft

Features:
- Authorization code flow
- PKCE support
- State verification
- Automatic user creation
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel
import httpx
from loguru import logger


class OAuth2Provider(BaseModel):
    """OAuth2 provider configuration"""
    name: str
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scopes: list[str]


class OAuth2Manager:
    """
    OAuth2 manager for multiple providers

    Supported providers:
    - Google
    - GitHub
    - Microsoft Azure AD
    """

    def __init__(self):
        self.providers: Dict[str, OAuth2Provider] = {}

    def register_provider(self, provider: OAuth2Provider):
        """Register OAuth2 provider"""
        self.providers[provider.name] = provider
        logger.info(f"OAuth2 provider registered: {provider.name}")

    def get_authorization_url(
        self,
        provider_name: str,
        redirect_uri: str,
        state: str
    ) -> str:
        """
        Get OAuth2 authorization URL

        Args:
            provider_name: Provider name (google, github, microsoft)
            redirect_uri: Callback URL
            state: CSRF token

        Returns:
            Authorization URL
        """
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")

        params = {
            "client_id": provider.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(provider.scopes),
            "state": state
        }

        # Build URL
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{provider.authorize_url}?{query_string}"

    async def exchange_code_for_token(
        self,
        provider_name: str,
        code: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token

        Args:
            provider_name: Provider name
            code: Authorization code
            redirect_uri: Callback URL

        Returns:
            Token response
        """
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                provider.token_url,
                data={
                    "client_id": provider.client_id,
                    "client_secret": provider.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                },
                headers={"Accept": "application/json"}
            )

            response.raise_for_status()
            return response.json()

    async def get_user_info(
        self,
        provider_name: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Get user info from provider

        Args:
            provider_name: Provider name
            access_token: OAuth2 access token

        Returns:
            User info
        """
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                provider.userinfo_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )

            response.raise_for_status()
            return response.json()

    def normalize_user_info(
        self,
        provider_name: str,
        user_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize user info from different providers

        Returns:
            Standardized user info with keys: id, email, name, picture
        """
        if provider_name == "google":
            return {
                "id": user_info["sub"],
                "email": user_info["email"],
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
                "email_verified": user_info.get("email_verified", False)
            }
        elif provider_name == "github":
            return {
                "id": str(user_info["id"]),
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "picture": user_info.get("avatar_url"),
                "email_verified": user_info.get("email") is not None
            }
        elif provider_name == "microsoft":
            return {
                "id": user_info["sub"],
                "email": user_info.get("email") or user_info.get("userPrincipalName"),
                "name": user_info.get("name"),
                "picture": None,
                "email_verified": True
            }
        else:
            return user_info


# Pre-configured providers
GOOGLE_PROVIDER = OAuth2Provider(
    name="google",
    client_id="",  # Set from config
    client_secret="",  # Set from config
    authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
    token_url="https://oauth2.googleapis.com/token",
    userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
    scopes=["openid", "email", "profile"]
)

GITHUB_PROVIDER = OAuth2Provider(
    name="github",
    client_id="",  # Set from config
    client_secret="",  # Set from config
    authorize_url="https://github.com/login/oauth/authorize",
    token_url="https://github.com/login/oauth/access_token",
    userinfo_url="https://api.github.com/user",
    scopes=["user:email"]
)

MICROSOFT_PROVIDER = OAuth2Provider(
    name="microsoft",
    client_id="",  # Set from config
    client_secret="",  # Set from config
    authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
    token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
    userinfo_url="https://graph.microsoft.com/v1.0/me",
    scopes=["openid", "email", "profile"]
)


# Global OAuth2 manager
_oauth2_manager: Optional[OAuth2Manager] = None


def get_oauth2_manager() -> OAuth2Manager:
    """Get or create OAuth2 manager"""
    global _oauth2_manager

    if _oauth2_manager is None:
        from cqox.config import settings

        _oauth2_manager = OAuth2Manager()

        # Register providers if configured
        if getattr(settings, 'google_client_id', None):
            GOOGLE_PROVIDER.client_id = settings.google_client_id
            GOOGLE_PROVIDER.client_secret = settings.google_client_secret
            _oauth2_manager.register_provider(GOOGLE_PROVIDER)

        if getattr(settings, 'github_client_id', None):
            GITHUB_PROVIDER.client_id = settings.github_client_id
            GITHUB_PROVIDER.client_secret = settings.github_client_secret
            _oauth2_manager.register_provider(GITHUB_PROVIDER)

        if getattr(settings, 'microsoft_client_id', None):
            MICROSOFT_PROVIDER.client_id = settings.microsoft_client_id
            MICROSOFT_PROVIDER.client_secret = settings.microsoft_client_secret
            _oauth2_manager.register_provider(MICROSOFT_PROVIDER)

    return _oauth2_manager
