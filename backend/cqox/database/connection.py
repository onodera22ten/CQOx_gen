"""
Database Connection Management
Provides database session dependencies for FastAPI
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import logging
import os

logger = logging.getLogger(__name__)

# Import settings for large-scale data configuration
try:
    from cqox.config.settings import settings
    DB_POOL_SIZE = settings.db_pool_size
    DB_MAX_OVERFLOW = settings.db_max_overflow
    DB_POOL_TIMEOUT = settings.db_pool_timeout
    DB_POOL_RECYCLE = settings.db_pool_recycle
except ImportError:
    # Fallback defaults
    DB_POOL_SIZE = 50
    DB_MAX_OVERFLOW = 150
    DB_POOL_TIMEOUT = 30
    DB_POOL_RECYCLE = 3600
    logger.warning("Using default database pool settings")

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://cqox:cqox_dev_password@localhost:5432/cqox_dev"
)

# Ensure we're using asyncpg driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine with large-scale data support
# Architecture.md: 50-200 connections for production workloads
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # Check connection health before using
    pool_size=DB_POOL_SIZE,  # Base pool (default: 50)
    max_overflow=DB_MAX_OVERFLOW,  # Additional connections (default: 150)
    pool_timeout=DB_POOL_TIMEOUT,  # Timeout waiting for connection (seconds)
    pool_recycle=DB_POOL_RECYCLE,  # Recycle connections after N seconds
    connect_args={
        "server_settings": {
            "application_name": "cqox_api",
            "jit": "off"  # Disable JIT for predictable query performance
        },
        "command_timeout": 60,  # Query timeout (seconds)
        "timeout": 10  # Connection timeout (seconds)
    }
)

# Create session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions

    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...

    Yields:
        AsyncSession: Database session
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database (create tables)
    Call this at application startup
    """
    from cqox.database.models import Base as ModelsBase

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(ModelsBase.metadata.create_all)
        logger.info("Database tables created")


async def close_db():
    """
    Close database connections
    Call this at application shutdown
    """
    await engine.dispose()
    logger.info("Database connections closed")
