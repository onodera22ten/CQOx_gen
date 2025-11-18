"""
PostgreSQL Client

Async PostgreSQL client using asyncpg
"""
from typing import Optional, Any, List
import asyncpg
from loguru import logger
import os


class PostgreSQLClient:
    """
    Async PostgreSQL client with connection pooling

    Features:
    - Connection pooling
    - Automatic reconnection
    - Query execution
    """

    def __init__(
        self,
        dsn: Optional[str] = None,
        min_size: int = 10,
        max_size: int = 20
    ):
        raw_dsn = dsn or os.getenv(
            "DATABASE_URL",
            "postgresql://cqox:cqox@postgres:5432/cqox"
        )
        # asyncpg doesn't understand postgresql+asyncpg:// scheme
        # Convert to pure postgresql://
        self.dsn = raw_dsn.replace("postgresql+asyncpg://", "postgresql://")
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Initialize connection pool"""
        if self.pool:
            return

        try:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=60
            )
            logger.info(f"PostgreSQL connection pool created (size: {self.min_size}-{self.max_size})")

        except Exception as e:
            logger.error(f"Failed to create PostgreSQL pool: {e}")
            raise

    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL connection pool closed")

    async def execute(self, query: str, *args) -> str:
        """Execute a query (INSERT, UPDATE, DELETE)"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch single row"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch single value"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def executemany(self, query: str, args_list: List[tuple]):
        """Execute query with multiple parameter sets"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            await conn.executemany(query, args_list)


# Global PostgreSQL client
_postgres_client: Optional[PostgreSQLClient] = None


async def get_postgres_client() -> PostgreSQLClient:
    """Get or create PostgreSQL client"""
    global _postgres_client

    if _postgres_client is None:
        _postgres_client = PostgreSQLClient()
        await _postgres_client.connect()

    return _postgres_client
