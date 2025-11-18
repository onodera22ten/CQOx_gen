"""
Pytest Configuration and Fixtures
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from cqox.api.main import app
from cqox.database.models import Base


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://cqox:cqox_dev_password@localhost:5434/cqox_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """Create test database"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_client() -> AsyncClient:
    """Create async HTTP client for testing"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers():
    """Generate auth headers for testing"""
    # Mock JWT token (in production, use real tokens)
    return {
        "Authorization": "Bearer test_token_123",
        "X-Tenant-ID": "test_tenant"
    }


@pytest.fixture
async def sample_dataset_id(async_client: AsyncClient, auth_headers):
    """Create a sample dataset for testing"""
    payload = {
        "name": "Sample Dataset",
        "description": "Dataset for testing"
    }
    response = await async_client.post("/api/v1/datasets/upload", json=payload, headers=auth_headers)
    return response.json()["dataset_id"]


@pytest.fixture
async def sample_policy_id(async_client: AsyncClient, auth_headers, sample_dataset_id):
    """Create a sample policy for testing"""
    payload = {
        "name": "Sample Policy",
        "dataset_id": sample_dataset_id,
        "target_rule": "age > 18"
    }
    response = await async_client.post("/api/v1/policies", json=payload, headers=auth_headers)
    return response.json()["id"]
