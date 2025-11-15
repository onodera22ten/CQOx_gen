"""
TimescaleDB client for time-series metrics storage

High-performance time-series database optimized for:
- Model training metrics (100K+ rows/sec)
- Diagnostic results over time
- Policy performance tracking
- Real-time dashboards
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncpg
from loguru import logger
from pydantic import BaseModel


class MetricPoint(BaseModel):
    """Time-series metric point"""
    timestamp: datetime
    metric_name: str
    metric_value: float
    tags: Dict[str, str] = {}
    model_run_id: Optional[str] = None
    policy_id: Optional[str] = None


class TimescaleDBClient:
    """
    TimescaleDB client with automatic hypertable creation and compression

    Features:
    - Automatic hypertable partitioning (1-day chunks)
    - Compression after 7 days (10x space reduction)
    - Continuous aggregates for fast queries
    - Connection pooling
    """

    def __init__(self, connection_string: str, pool_size: int = 20):
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Initialize connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=5,
                max_size=self.pool_size,
                command_timeout=60,
                max_queries=50000,
                max_inactive_connection_lifetime=300
            )

            await self._create_hypertables()
            await self._create_continuous_aggregates()
            await self._setup_compression()

            logger.info("TimescaleDB connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to connect to TimescaleDB: {e}")
            raise

    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("TimescaleDB connection pool closed")

    async def _create_hypertables(self):
        """Create hypertables for time-series data"""
        async with self.pool.acquire() as conn:
            # Enable TimescaleDB extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

            # Model training metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS model_metrics (
                    timestamp TIMESTAMPTZ NOT NULL,
                    model_run_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value DOUBLE PRECISION NOT NULL,
                    estimator TEXT,
                    dataset_id TEXT,
                    tags JSONB
                );
            """)

            # Convert to hypertable (1-day chunks)
            await conn.execute("""
                SELECT create_hypertable(
                    'model_metrics',
                    'timestamp',
                    chunk_time_interval => INTERVAL '1 day',
                    if_not_exists => TRUE
                );
            """)

            # Policy evaluation metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS policy_metrics (
                    timestamp TIMESTAMPTZ NOT NULL,
                    policy_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value DOUBLE PRECISION NOT NULL,
                    policy_version INTEGER,
                    channel TEXT,
                    tags JSONB
                );
            """)

            await conn.execute("""
                SELECT create_hypertable(
                    'policy_metrics',
                    'timestamp',
                    chunk_time_interval => INTERVAL '1 day',
                    if_not_exists => TRUE
                );
            """)

            # Diagnostic results table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS diagnostic_metrics (
                    timestamp TIMESTAMPTZ NOT NULL,
                    model_run_id TEXT NOT NULL,
                    diagnostic_type TEXT NOT NULL,
                    score DOUBLE PRECISION NOT NULL,
                    passed BOOLEAN,
                    tags JSONB
                );
            """)

            await conn.execute("""
                SELECT create_hypertable(
                    'diagnostic_metrics',
                    'timestamp',
                    chunk_time_interval => INTERVAL '1 day',
                    if_not_exists => TRUE
                );
            """)

            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_metrics_run_id
                ON model_metrics (model_run_id, timestamp DESC);
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_policy_metrics_policy_id
                ON policy_metrics (policy_id, timestamp DESC);
            """)

            logger.info("TimescaleDB hypertables created")

    async def _setup_compression(self):
        """Enable compression for old data (7 days+)"""
        async with self.pool.acquire() as conn:
            # Compress model_metrics after 7 days
            await conn.execute("""
                ALTER TABLE model_metrics SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'model_run_id, estimator'
                );
            """)

            await conn.execute("""
                SELECT add_compression_policy('model_metrics', INTERVAL '7 days');
            """)

            # Compress policy_metrics after 7 days
            await conn.execute("""
                ALTER TABLE policy_metrics SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'policy_id, channel'
                );
            """)

            await conn.execute("""
                SELECT add_compression_policy('policy_metrics', INTERVAL '7 days');
            """)

            logger.info("TimescaleDB compression policies configured")

    async def _create_continuous_aggregates(self):
        """Create continuous aggregates for fast queries"""
        async with self.pool.acquire() as conn:
            # Hourly model metrics aggregate
            await conn.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS model_metrics_hourly
                WITH (timescaledb.continuous) AS
                SELECT
                    time_bucket('1 hour', timestamp) AS bucket,
                    model_run_id,
                    metric_name,
                    AVG(metric_value) as avg_value,
                    MIN(metric_value) as min_value,
                    MAX(metric_value) as max_value,
                    COUNT(*) as count
                FROM model_metrics
                GROUP BY bucket, model_run_id, metric_name
                WITH NO DATA;
            """)

            # Refresh policy (every hour)
            await conn.execute("""
                SELECT add_continuous_aggregate_policy('model_metrics_hourly',
                    start_offset => INTERVAL '3 hours',
                    end_offset => INTERVAL '1 hour',
                    schedule_interval => INTERVAL '1 hour');
            """)

            logger.info("TimescaleDB continuous aggregates created")

    async def insert_metric(self, metric: MetricPoint):
        """Insert single metric point"""
        async with self.pool.acquire() as conn:
            if metric.model_run_id:
                await conn.execute("""
                    INSERT INTO model_metrics
                    (timestamp, model_run_id, metric_name, metric_value, tags)
                    VALUES ($1, $2, $3, $4, $5)
                """, metric.timestamp, metric.model_run_id, metric.metric_name,
                    metric.metric_value, metric.tags)
            elif metric.policy_id:
                await conn.execute("""
                    INSERT INTO policy_metrics
                    (timestamp, policy_id, metric_name, metric_value, tags)
                    VALUES ($1, $2, $3, $4, $5)
                """, metric.timestamp, metric.policy_id, metric.metric_name,
                    metric.metric_value, metric.tags)

    async def insert_metrics_batch(self, metrics: List[MetricPoint]):
        """Bulk insert metrics (high performance)"""
        async with self.pool.acquire() as conn:
            model_metrics = [m for m in metrics if m.model_run_id]
            policy_metrics = [m for m in metrics if m.policy_id]

            if model_metrics:
                await conn.executemany("""
                    INSERT INTO model_metrics
                    (timestamp, model_run_id, metric_name, metric_value, tags)
                    VALUES ($1, $2, $3, $4, $5)
                """, [(m.timestamp, m.model_run_id, m.metric_name, m.metric_value, m.tags)
                      for m in model_metrics])

            if policy_metrics:
                await conn.executemany("""
                    INSERT INTO policy_metrics
                    (timestamp, policy_id, metric_name, metric_value, tags)
                    VALUES ($1, $2, $3, $4, $5)
                """, [(m.timestamp, m.policy_id, m.metric_name, m.metric_value, m.tags)
                      for m in policy_metrics])

            logger.info(f"Inserted {len(metrics)} metrics in batch")

    async def query_metrics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        model_run_id: Optional[str] = None,
        policy_id: Optional[str] = None,
        aggregation: str = "avg",
        interval: str = "1 hour"
    ) -> List[Dict[str, Any]]:
        """
        Query time-series metrics with aggregation

        Args:
            metric_name: Metric to query
            start_time: Start timestamp
            end_time: End timestamp
            model_run_id: Filter by model run
            policy_id: Filter by policy
            aggregation: avg, min, max, sum, count
            interval: Aggregation interval (e.g., '1 hour', '1 day')
        """
        async with self.pool.acquire() as conn:
            if model_run_id:
                query = f"""
                    SELECT
                        time_bucket($1, timestamp) as bucket,
                        {aggregation}(metric_value) as value
                    FROM model_metrics
                    WHERE metric_name = $2
                      AND model_run_id = $3
                      AND timestamp BETWEEN $4 AND $5
                    GROUP BY bucket
                    ORDER BY bucket DESC
                """
                rows = await conn.fetch(
                    query, interval, metric_name, model_run_id, start_time, end_time
                )
            elif policy_id:
                query = f"""
                    SELECT
                        time_bucket($1, timestamp) as bucket,
                        {aggregation}(metric_value) as value
                    FROM policy_metrics
                    WHERE metric_name = $2
                      AND policy_id = $3
                      AND timestamp BETWEEN $4 AND $5
                    GROUP BY bucket
                    ORDER BY bucket DESC
                """
                rows = await conn.fetch(
                    query, interval, metric_name, policy_id, start_time, end_time
                )
            else:
                return []

            return [dict(row) for row in rows]

    async def get_latest_metrics(
        self,
        model_run_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get latest metrics for a model run"""
        async with self.pool.acquire() as conn:
            if model_run_id:
                rows = await conn.fetch("""
                    SELECT timestamp, metric_name, metric_value, tags
                    FROM model_metrics
                    WHERE model_run_id = $1
                    ORDER BY timestamp DESC
                    LIMIT $2
                """, model_run_id, limit)
            else:
                rows = await conn.fetch("""
                    SELECT timestamp, model_run_id, metric_name, metric_value, tags
                    FROM model_metrics
                    ORDER BY timestamp DESC
                    LIMIT $1
                """, limit)

            return [dict(row) for row in rows]

    async def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    hypertable_name,
                    total_chunks,
                    number_compressed_chunks,
                    pg_size_pretty(before_compression_total_bytes) as uncompressed_size,
                    pg_size_pretty(after_compression_total_bytes) as compressed_size
                FROM timescaledb_information.compression_settings
                JOIN timescaledb_information.chunks ON TRUE
                WHERE hypertable_name IN ('model_metrics', 'policy_metrics')
            """)

            return [dict(row) for row in rows]


# Global client instance
_timescaledb_client: Optional[TimescaleDBClient] = None


async def get_timescaledb_client() -> TimescaleDBClient:
    """Get or create TimescaleDB client"""
    global _timescaledb_client

    if _timescaledb_client is None:
        from cqox.config import settings
        _timescaledb_client = TimescaleDBClient(settings.database_url)
        await _timescaledb_client.connect()

    return _timescaledb_client
