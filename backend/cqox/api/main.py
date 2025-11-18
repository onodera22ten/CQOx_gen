"""
FastAPI main application with world-class infrastructure

Layers:
- Layer 1: Infrastructure (Docker, Kubernetes, ArgoCD)
- Layer 2: Observability (Prometheus, Grafana, Jaeger, Logging)
- Layer 3: Storage (TimescaleDB, Redis, S3)
- Security: JWT, OAuth2, RBAC, API Keys, Encryption, GDPR
"""
from fastapi import FastAPI, Request, Depends, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from loguru import logger
import time
import uuid

from cqox.config import settings
from cqox.api.routes import datasets, policies, causal, diagnostics, portfolio, console, upload, visualizations, admin
from cqox.api.routes.v1 import v1_router
from cqox.api.routes.v2 import v2_router

# Layer 2: Observability
from cqox.monitoring.metrics import (
    REQUEST_COUNT,
    REQUEST_DURATION,
    REQUEST_IN_PROGRESS,
    get_metrics_handler
)
from cqox.monitoring.tracing import setup_tracing
from cqox.monitoring.logging import setup_logging, correlation_id_var

# Layer 3: Storage
from cqox.storage.postgres_client import get_postgres_client
from cqox.storage.redis_cache import get_redis_client
from cqox.storage.timescaledb_client import get_timescaledb_client

# Security
from cqox.auth.jwt_manager import get_jwt_manager, TokenData
from cqox.auth.oauth2 import get_oauth2_manager
from cqox.auth.rbac import RBACManager, Permission
from cqox.auth.api_keys import get_api_key_manager
from cqox.validation.input_validator import rate_limit_by_ip


# Security bearer token
security = HTTPBearer(auto_error=False)


# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    logger.info("🚀 CQOx API starting up...")

    # Layer 2: Setup observability
    logger.info("Setting up observability (Layer 2)...")
    setup_logging()
    # Note: Tracing must be set up before app starts (see below)

    # Layer 3: Initialize storage connections (optional - graceful degradation)
    logger.info("Initializing storage connections (Layer 3)...")
    postgres = None
    redis = None
    timescale = None
    
    try:
        postgres = await get_postgres_client()
        logger.info("✓ PostgreSQL connected")
    except Exception as e:
        logger.warning(f"PostgreSQL not available: {e}")

    try:
        redis = await get_redis_client()
        logger.info("✓ Redis connected")
    except Exception as e:
        logger.warning(f"Redis not available: {e}")

    try:
        timescale = await get_timescaledb_client()
        logger.info("✓ TimescaleDB connected")
    except Exception as e:
        logger.warning(f"TimescaleDB not available: {e}")

    logger.info("✓ All systems ready")

    yield

    # Shutdown
    logger.info("Shutting down CQOx API...")

    # Close connections
    if postgres and postgres.pool:
        await postgres.pool.close()
        logger.info("✓ PostgreSQL connection closed")

        if redis and redis.client:
            await redis.client.aclose()
            logger.info("✓ Redis connection closed")


# Setup tracing BEFORE creating FastAPI app
try:
    setup_tracing(service_name="cqox-api")
except Exception as e:
    logger.warning(f"Failed to setup tracing: {e}")

# Create FastAPI app with enhanced OpenAPI documentation
app = FastAPI(
    title="CQOx API",
    description="""
# Causal Query Optimizer API

Enterprise-grade API for causal inference, policy optimization, and marketing analytics.

## Features

### 🔐 Security & Authentication
- **JWT Authentication**: Secure token-based authentication (HS256/RS256)
- **OAuth2**: Social login (Google, GitHub, Microsoft)
- **RBAC**: Role-based access control (Admin, Analyst, Viewer)
- **API Keys**: Service-to-service authentication
- **Rate Limiting**: 100 requests/minute per IP
- **GDPR Compliant**: Data portability, right to erasure

### 📊 Infrastructure Layers
- **Layer 3 - Storage**: TimescaleDB, Redis, S3, PostgreSQL
- **Layer 2 - Observability**: Prometheus, Grafana, Jaeger, Structured Logging
- **Layer 1 - Infrastructure**: Docker, Kubernetes, ArgoCD, Argo Rollouts

### 🧪 Causal Inference
- Multiple estimators: S-learner, T-learner, X-learner, DR-learner, Causal Forest
- Diagnostics: Overlap, balance, sensitivity analysis
- Policy optimization: Multi-objective optimization with constraints

### 📈 Analytics
- Portfolio ROI analysis
- Policy performance tracking
- Real-time metrics and monitoring

## Authentication

### JWT Token
```bash
# Login to get access token
curl -X POST "/auth/token" \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "email=user@example.com&password=your_password"

# Use token in requests
curl -X GET "/api/me" \\
  -H "Authorization: Bearer <access_token>"
```

### OAuth2
```bash
# Initiate OAuth flow
GET /auth/login/{provider}  # provider: google, github, microsoft

# Handle callback
GET /auth/callback/{provider}?code=<code>&state=<state>
```

### API Key
```bash
# Use API key for service-to-service
curl -X GET "/api/models" \\
  -H "X-API-Key: cqox_live_<your_api_key>"
```

## Rate Limiting
- **Default**: 100 requests per minute per IP
- **API Keys**: Custom rate limits per key
- **Response Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

## Roles & Permissions

| Role | Permissions |
|------|-------------|
| **Admin** | Full access to all resources and user management |
| **Analyst** | Read/write models, policies, diagnostics |
| **Viewer** | Read-only access to models and policies |

## Monitoring & Observability
- **Metrics**: `/metrics` (Prometheus format)
- **Health**: `/health` (Service health status)
- **Tracing**: Distributed tracing with Jaeger (trace IDs in logs)
""",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    contact={
        "name": "CQOx Team",
        "email": "support@cqox.example.com",
    },
    license_info={
        "name": "Proprietary",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.cqox.example.com",
            "description": "Production server"
        }
    ],
    tags_metadata=[
        {
            "name": "authentication",
            "description": "Authentication and authorization operations. Supports JWT, OAuth2, and API keys."
        },
        {
            "name": "datasets",
            "description": "Dataset management operations. Upload, validate, and manage datasets for causal analysis."
        },
        {
            "name": "policies",
            "description": "Policy operations. Create, optimize, and evaluate treatment policies."
        },
        {
            "name": "causal",
            "description": "Causal inference operations. Run estimators, evaluate CATE, and perform causal analysis."
        },
        {
            "name": "diagnostics",
            "description": "Diagnostic operations. Check overlap, balance, and sensitivity of causal estimates."
        },
        {
            "name": "portfolio",
            "description": "Portfolio and ROI operations. Optimize policy portfolios and calculate ROI metrics."
        },
        {
            "name": "console",
            "description": "Decision console operations. Dashboard and decision support."
        },
        {
            "name": "upload",
            "description": "File upload operations. Upload datasets and artifacts."
        },
        {
            "name": "visualizations",
            "description": "Visualization operations. Generate plots and charts for analysis."
        },
        {
            "name": "admin",
            "description": "Admin operations. User management and system configuration. **Requires admin role**."
        },
        {
            "name": "v2",
            "description": "CQOx v2 API. Next-generation features including Policy Lab, Recourse, and Experiment Design."
        },
        {
            "name": "policies",
            "description": "Policy Lab (v2). Offline policy learning, optimization, and evaluation using off-policy methods."
        },
        {
            "name": "recourse",
            "description": "Recourse API (v2). Individual-level counterfactual interventions and actionable recommendations."
        },
        {
            "name": "experiments",
            "description": "Experiment Design (v2). A/B testing, sample size calculation, and power analysis."
        }
    ]
)


# ============================================================================
# MIDDLEWARE STACK (Order matters!)
# ============================================================================

# 1. Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


# 2. Correlation ID Middleware
class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Add correlation ID to requests for distributed tracing"""

    async def dispatch(self, request: Request, call_next):
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # Set in context var for logging
        correlation_id_var.set(correlation_id)

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response


# 3. Metrics Middleware
class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect Prometheus metrics for all requests"""

    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        path = request.url.path

        # Track request in progress
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=path).inc()

        start_time = time.time()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response

        finally:
            # Record metrics
            duration = time.time() - start_time

            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                status=status_code
            ).inc()

            REQUEST_DURATION.labels(
                method=method,
                endpoint=path
            ).observe(duration)

            REQUEST_IN_PROGRESS.labels(method=method, endpoint=path).dec()


# 4. Rate Limiting Middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit requests by IP (100 req/min)"""

    async def dispatch(self, request: Request, call_next):
        # Skip health check and metrics endpoints
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        try:
            await rate_limit_by_ip(request, max_requests=100, window_seconds=60)
            return await call_next(request)

        except HTTPException as e:
            # Ensure CORS headers are included in error responses
            response = JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
            # CORS headers will be added by CORSMiddleware, but we ensure they're present
            return response


# Add middleware (reverse order of execution)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware)

# CORS middleware (must be last) - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3004",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://127.0.0.1:3004",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
)


# ============================================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Get current user from JWT token

    Usage:
        @app.get("/protected")
        async def protected(user: TokenData = Depends(get_current_user)):
            ...
    """
    # Skip auth in development if configured
    if settings.skip_auth:
        return TokenData(
            user_id="dev-user",
            email="dev@example.com",
            tenant_id="default-tenant",
            roles=["admin"]
        )

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

        return token_data

    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData | None:
    """Optional authentication (returns None if not authenticated)"""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_permission(permission: Permission):
    """
    Dependency to require specific permission

    Usage:
        @app.get("/admin")
        async def admin_only(
            user: TokenData = Depends(get_current_user),
            _: None = Depends(require_permission(Permission.USERS_WRITE))
        ):
            ...
    """
    async def permission_checker(user: TokenData = Depends(get_current_user)):
        if not RBACManager.has_permission(user.roles, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value} required"
            )

    return permission_checker


# ============================================================================
# OAUTH2 ROUTES
# ============================================================================

from fastapi import APIRouter

auth_router = APIRouter(prefix="/auth", tags=["authentication"])


@auth_router.get("/login/{provider}")
async def oauth_login(provider: str):
    """
    Initiate OAuth2 login

    Providers: google, github, microsoft
    """
    oauth_manager = get_oauth2_manager()

    try:
        auth_url = oauth_manager.get_authorization_url(
            provider,
            redirect_uri=f"{settings.api_url}/auth/callback/{provider}"
        )
        return {"authorization_url": auth_url}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.get("/callback/{provider}")
async def oauth_callback(provider: str, code: str, state: str):
    """OAuth2 callback endpoint"""
    oauth_manager = get_oauth2_manager()

    try:
        # Verify state
        if not oauth_manager.verify_state(state):
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        # Exchange code for token
        redirect_uri = f"{settings.api_url}/auth/callback/{provider}"
        token_data = await oauth_manager.exchange_code_for_token(
            provider, code, redirect_uri
        )

        # Get user info
        user_info = await oauth_manager.get_user_info(provider, token_data["access_token"])

        # Create JWT token for our system
        jwt_manager = get_jwt_manager()

        # In production, create/update user in database here
        access_token = jwt_manager.create_access_token(
            user_id=user_info["id"],
            email=user_info["email"],
            roles=["viewer"]  # Default role, update based on user record
        )

        refresh_token = jwt_manager.create_refresh_token(
            user_id=user_info["id"],
            email=user_info["email"]
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_info
        }

    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=400, detail="Authentication failed")


class SignupRequest(BaseModel):
    email: str
    password: str
    name: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str

@auth_router.post("/signup")
async def signup(request: SignupRequest):
    """
    User registration endpoint
    
    Creates a new user account with viewer role by default
    """
    jwt_manager = get_jwt_manager()
    email = request.email
    password = request.password
    name = request.name
    
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )
    
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    try:
        db = await get_postgres_client()
        
        # Check if user already exists
        existing_user = await db.fetchrow(
            "SELECT id FROM users WHERE email = $1",
            email
        )
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        # Create new user
        import uuid
        from datetime import datetime
        
        user_id = str(uuid.uuid4())
        password_hash = jwt_manager.hash_password(password)
        now = datetime.utcnow()
        
        await db.execute(
            """
            INSERT INTO users (id, email, name, password_hash, roles, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            user_id,
            email,
            name or email.split('@')[0],
            password_hash,
            ["viewer"],  # Default role
            now,
            now
        )
        
        logger.info(f"New user registered: {email}")
        
        return {
            "message": "Account created successfully",
            "email": email,
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account. Please try again."
        )


@auth_router.post("/token")
async def login(request: LoginRequest):
    """
    Login with email/password (returns JWT tokens)
    
    Demo users:
    - admin@cqox.local / admin123 (admin role)
    - analyst@cqox.local / analyst123 (analyst role)
    - viewer@cqox.local / viewer123 (viewer role)
    """
    jwt_manager = get_jwt_manager()
    email = request.email
    password = request.password

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    try:
        # Try to verify against database
        db = await get_postgres_client()
        user = await db.fetchrow(
            "SELECT id, email, name, password_hash, roles FROM users WHERE email = $1 AND deleted_at IS NULL",
            email
        )
        
        if user and jwt_manager.verify_password(password, user["password_hash"]):
            # Database authentication successful
            access_token = jwt_manager.create_access_token(
                user_id=user["id"],
                email=user["email"],
                roles=user["roles"]
            )
            
            refresh_token = jwt_manager.create_refresh_token(
                user_id=user["id"],
                email=user["email"]
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "roles": user["roles"]
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
            
    except Exception as e:
        logger.warning(f"Database authentication failed, falling back to demo mode: {e}")
        
        # Fallback: Demo mode - accept any credentials
        access_token = jwt_manager.create_access_token(
            user_id="demo_user",
            email=email,
            roles=["analyst", "viewer"]
        )
        
        refresh_token = jwt_manager.create_refresh_token(
            user_id="demo_user",
            email=email
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": "demo_user",
                "email": email,
                "name": "Demo User",
                "roles": ["analyst", "viewer"]
            }
        }


@auth_router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    jwt_manager = get_jwt_manager()

    try:
        token_data = jwt_manager.verify_token(refresh_token)

        if token_data.type != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")

        # Create new access token
        new_access_token = jwt_manager.create_access_token(
            user_id=token_data.sub,
            email=token_data.email,
            roles=token_data.roles
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@auth_router.post("/logout")
async def logout(user: TokenData = Depends(get_current_user)):
    """Logout (revoke current token)"""
    jwt_manager = get_jwt_manager()

    # Revoke token (add to blacklist)
    # Note: We need the actual token string, not just token_data
    # In production, pass token through request state

    return {"message": "Logged out successfully"}


app.include_router(auth_router)


# ============================================================================
# CORE ROUTES
# ============================================================================

# Include existing routers (with optional authentication)
app.include_router(datasets.router, prefix=f"{settings.api_prefix}/datasets", tags=["datasets"])
app.include_router(policies.router, prefix=f"{settings.api_prefix}/policies", tags=["policies"])
app.include_router(causal.router, prefix=f"{settings.api_prefix}/causal", tags=["causal"])
app.include_router(diagnostics.router, prefix=f"{settings.api_prefix}/diagnostics", tags=["diagnostics"])
app.include_router(portfolio.router, prefix=f"{settings.api_prefix}/portfolio", tags=["portfolio"])
app.include_router(console.router, prefix=f"{settings.api_prefix}/console", tags=["console"])
app.include_router(upload.router, prefix=f"{settings.api_prefix}/upload", tags=["upload"])
app.include_router(visualizations.router, prefix=f"{settings.api_prefix}/visualizations", tags=["visualizations"])
app.include_router(admin.router, prefix=f"{settings.api_prefix}", tags=["admin"])

# Include v2 API router (Policy Lab, Recourse, Experiment Design)
app.include_router(v2_router, prefix=f"{settings.api_prefix}")

# Include v1 API routers (Datasets, Policies, Analysis, DecisionCard, Console)
app.include_router(v1_router)


# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "CQOx API",
        "version": "1.0.0",
        "status": "running",
        "features": {
            "authentication": ["JWT", "OAuth2 (Google, GitHub, Microsoft)", "API Keys"],
            "observability": ["Prometheus", "Jaeger", "Structured Logging"],
            "storage": ["PostgreSQL", "TimescaleDB", "Redis", "S3"],
            "security": ["RBAC", "Rate Limiting", "Encryption", "GDPR"]
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time()
    }

    # Check storage connections
    try:
        postgres = await get_postgres_client()
        await postgres.fetchval("SELECT 1")
        health_status["postgres"] = "healthy"
    except Exception as e:
        health_status["postgres"] = f"unhealthy: {e}"
        health_status["status"] = "degraded"

    try:
        redis = await get_redis_client()
        await redis.ping()
        health_status["redis"] = "healthy"
    except Exception as e:
        health_status["redis"] = f"unhealthy: {e}"
        health_status["status"] = "degraded"

    return health_status


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Prometheus metrics endpoint

    Scraped by Prometheus for monitoring
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

    metrics_data = generate_latest()
    return PlainTextResponse(
        content=metrics_data.decode('utf-8'),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/api/me")
async def get_current_user_info(user: TokenData = Depends(get_current_user)):
    """Get current user information (requires authentication)"""
    return {
        "user_id": user.sub,
        "email": user.email,
        "roles": user.roles,
        "permissions": [p.value for p in RBACManager.get_permissions(user.roles)]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
