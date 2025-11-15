"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
import os

from cqox.api.main import app
from cqox.auth.jwt_manager import get_jwt_manager
from cqox.storage.postgres_client import get_postgres_client
from cqox.storage.redis_cache import get_redis_client


# Configure test environment
os.environ["DATABASE_URL"] = os.getenv(
    "DATABASE_URL", "postgresql://cqox:cqox@localhost:5432/cqox_test"
)
os.environ["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/1")
os.environ["JWT_SECRET_KEY"] = "test-secret-key"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def db_client():
    """Get database client"""
    client = await get_postgres_client()
    yield client

    # Cleanup after tests
    if client.pool:
        await client.pool.close()


@pytest.fixture
async def redis_client():
    """Get Redis client"""
    client = await get_redis_client()
    yield client

    # Cleanup after tests
    if client.client:
        await client.client.flushdb()  # Clear test database
        await client.client.close()


@pytest.fixture
def jwt_manager():
    """Get JWT manager"""
    return get_jwt_manager()


@pytest.fixture
def auth_headers(jwt_manager) -> dict:
    """Create authentication headers with viewer role"""
    token = jwt_manager.create_access_token(
        user_id="test-user-id",
        email="test@example.com",
        roles=["viewer"]
    )

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def analyst_headers(jwt_manager) -> dict:
    """Create authentication headers with analyst role"""
    token = jwt_manager.create_access_token(
        user_id="analyst-user-id",
        email="analyst@example.com",
        roles=["analyst"]
    )

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(jwt_manager) -> dict:
    """Create authentication headers with admin role"""
    token = jwt_manager.create_access_token(
        user_id="admin-user-id",
        email="admin@example.com",
        roles=["admin"]
    )

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
async def setup_test_database(db_client):
    """Setup test database before each test"""
    # Create tables if they don't exist
    await db_client.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255),
            password_hash VARCHAR(255),
            roles TEXT[] DEFAULT ARRAY['viewer'],
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            deleted_at TIMESTAMP,
            anonymized BOOLEAN DEFAULT FALSE
        )
    """)

    yield

    # Cleanup after test
    await db_client.execute("TRUNCATE users CASCADE")


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "roles": ["viewer"]
    }


@pytest.fixture
def sample_model_run_data():
    """Sample model run data for testing"""
    return {
        "estimator": "s_learner",
        "dataset_name": "test_dataset",
        "treatment_col": "treatment",
        "outcome_col": "outcome",
        "confounders": ["age", "gender"],
        "status": "pending"
    }
