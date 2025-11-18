"""
Distributed Job Execution with Idempotency
Celery tasks with Redis locks and exponential backoff
"""

from celery import Celery, Task
from celery.exceptions import Retry
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from enum import Enum
import uuid
import logging
import json
import hashlib

from cqox.config import settings
from cqox.storage.redis_cache import get_redis_client

logger = logging.getLogger(__name__)


# Job status FSM (Finite State Machine)
class JobStatus(str, Enum):
    """Job status states"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


# Valid state transitions
VALID_TRANSITIONS = {
    JobStatus.PENDING: [JobStatus.QUEUED, JobStatus.CANCELLED],
    JobStatus.QUEUED: [JobStatus.RUNNING, JobStatus.CANCELLED],
    JobStatus.RUNNING: [JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.RETRYING, JobStatus.CANCELLED],
    JobStatus.RETRYING: [JobStatus.RUNNING, JobStatus.FAILED, JobStatus.CANCELLED],
    JobStatus.SUCCEEDED: [],  # Terminal state
    JobStatus.FAILED: [],  # Terminal state
    JobStatus.CANCELLED: [],  # Terminal state
}


# Celery app configuration
celery_app = Celery(
    'cqox',
    broker=settings.celery_broker_url if hasattr(settings, 'celery_broker_url') else 'redis://localhost:6379/0',
    backend=settings.celery_result_backend if hasattr(settings, 'celery_result_backend') else 'redis://localhost:6379/0'
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Result backend
    result_expires=3600,  # 1 hour
    result_extended=True,

    # Retry settings
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,

    # Routing
    task_routes={
        'cqox.tasks.heavy.*': {'queue': 'heavy'},
        'cqox.tasks.light.*': {'queue': 'light'},
        'cqox.tasks.realtime.*': {'queue': 'realtime'},
    },

    # Queue priority
    task_queue_max_priority=10,
    task_default_priority=5,

    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time for heavy tasks
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)


class IdempotentTask(Task):
    """
    Base task class with idempotency support

    Features:
    - Idempotency key generation and checking
    - Redis distributed locks
    - Automatic state transitions
    - Exponential backoff retry with jitter
    - Dead Letter Queue (DLQ) for failed tasks
    """

    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True

    def __call__(self, *args, **kwargs):
        """Override to add idempotency checking"""
        # Extract idempotency key
        idempotency_key = kwargs.get('idempotency_key')

        if idempotency_key:
            # Check if this task has already been processed
            result = self._check_idempotency(idempotency_key)
            if result is not None:
                logger.info(f"Task {self.name} with key {idempotency_key} already processed")
                return result

        # Execute task
        try:
            result = super().__call__(*args, **kwargs)

            # Store result for idempotency
            if idempotency_key:
                self._store_idempotent_result(idempotency_key, result)

            return result

        except Exception as e:
            logger.error(f"Task {self.name} failed: {e}", exc_info=True)
            raise

    def _check_idempotency(self, key: str) -> Optional[Any]:
        """Check if task with this key has already been processed"""
        redis = get_redis_client()

        # Check Redis cache
        cache_key = f"idempotency:{key}"
        cached_result = redis.get(cache_key)

        if cached_result:
            try:
                return json.loads(cached_result)
            except json.JSONDecodeError:
                return cached_result

        return None

    def _store_idempotent_result(self, key: str, result: Any, ttl: int = 86400):
        """Store task result for idempotency (24 hour TTL)"""
        redis = get_redis_client()

        cache_key = f"idempotency:{key}"

        # Serialize result
        try:
            serialized = json.dumps(result)
        except (TypeError, ValueError):
            serialized = str(result)

        # Store with TTL
        redis.setex(cache_key, ttl, serialized)

    def generate_idempotency_key(self, *args, **kwargs) -> str:
        """
        Generate idempotency key from task name and arguments

        Format: {task_name}:{hash(args+kwargs)}
        """
        # Serialize arguments
        args_str = json.dumps(args, sort_keys=True)
        kwargs_str = json.dumps({k: v for k, v in kwargs.items() if k != 'idempotency_key'}, sort_keys=True)

        # Hash
        content = f"{self.name}:{args_str}:{kwargs_str}"
        hash_value = hashlib.sha256(content.encode()).hexdigest()[:16]

        return f"{self.name}:{hash_value}"


class DistributedLock:
    """
    Redis-based distributed lock

    Prevents multiple workers from executing the same critical section.

    Usage:
        async with DistributedLock(f"policy:{policy_id}"):
            # Critical section
            ...
    """

    def __init__(self,
                 key: str,
                 timeout: int = 300,  # 5 minutes
                 blocking: bool = True,
                 blocking_timeout: int = 60):
        """
        Args:
            key: Lock key
            timeout: Lock expiration time (seconds)
            blocking: Wait for lock if already held
            blocking_timeout: Max time to wait for lock (seconds)
        """
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.blocking = blocking
        self.blocking_timeout = blocking_timeout
        self.lock_value = str(uuid.uuid4())
        self.redis = None
        self._acquired = False

    async def __aenter__(self):
        """Acquire lock"""
        self.redis = await get_redis_client()

        if self.blocking:
            # Blocking acquire with timeout
            start_time = datetime.utcnow()

            while True:
                acquired = await self.redis.set(
                    self.key,
                    self.lock_value,
                    ex=self.timeout,
                    nx=True  # Only set if not exists
                )

                if acquired:
                    self._acquired = True
                    logger.debug(f"Acquired lock: {self.key}")
                    return self

                # Check timeout
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed >= self.blocking_timeout:
                    raise TimeoutError(f"Failed to acquire lock {self.key} within {self.blocking_timeout}s")

                # Wait and retry
                await asyncio.sleep(0.1)
        else:
            # Non-blocking acquire
            acquired = await self.redis.set(
                self.key,
                self.lock_value,
                ex=self.timeout,
                nx=True
            )

            if not acquired:
                raise RuntimeError(f"Lock {self.key} is already held")

            self._acquired = True
            logger.debug(f"Acquired lock: {self.key}")
            return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release lock"""
        if self._acquired and self.redis:
            # Verify we still own the lock before deleting
            current_value = await self.redis.get(self.key)

            if current_value == self.lock_value:
                await self.redis.delete(self.key)
                logger.debug(f"Released lock: {self.key}")
            else:
                logger.warning(f"Lock {self.key} was already released or expired")

            self._acquired = False


class JobStateManager:
    """
    Manage job state transitions with FSM validation
    """

    @staticmethod
    async def transition(job_id: str,
                        from_status: JobStatus,
                        to_status: JobStatus,
                        metadata: Optional[Dict] = None) -> bool:
        """
        Transition job to new status

        Args:
            job_id: Job ID
            from_status: Current status
            to_status: Target status
            metadata: Additional data to store

        Returns:
            True if transition succeeded

        Raises:
            ValueError: If transition is invalid
        """
        # Validate transition
        if to_status not in VALID_TRANSITIONS.get(from_status, []):
            raise ValueError(
                f"Invalid state transition: {from_status} -> {to_status}. "
                f"Valid transitions from {from_status}: {VALID_TRANSITIONS.get(from_status, [])}"
            )

        # Use Redis transaction for atomic update
        redis = await get_redis_client()

        # Store state in Redis
        state_key = f"job:{job_id}:state"

        state_data = {
            'status': to_status.value,
            'previous_status': from_status.value,
            'transitioned_at': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }

        await redis.set(state_key, json.dumps(state_data), ex=86400)  # 24 hour TTL

        # Also update database (in production)
        # await update_job_status_in_db(job_id, to_status, metadata)

        logger.info(f"Job {job_id} transitioned: {from_status} -> {to_status}")

        return True

    @staticmethod
    async def get_status(job_id: str) -> Optional[JobStatus]:
        """Get current job status"""
        redis = await get_redis_client()

        state_key = f"job:{job_id}:state"
        state_data = await redis.get(state_key)

        if state_data:
            try:
                data = json.loads(state_data)
                return JobStatus(data['status'])
            except (json.JSONDecodeError, KeyError, ValueError):
                return None

        return None


# Example task definitions

@celery_app.task(base=IdempotentTask, bind=True, queue='heavy', priority=3)
def train_policy_task(self,
                     policy_id: str,
                     dataset_id: str,
                     idempotency_key: Optional[str] = None):
    """
    Heavy task: Train policy with offline learning

    Features:
    - Idempotency via key
    - Distributed lock per policy
    - Exponential backoff retry
    - State tracking
    """
    import asyncio

    async def _execute():
        job_id = self.request.id

        # Transition to RUNNING
        await JobStateManager.transition(
            job_id,
            JobStatus.QUEUED,
            JobStatus.RUNNING,
            metadata={'policy_id': policy_id, 'dataset_id': dataset_id}
        )

        try:
            # Acquire distributed lock
            async with DistributedLock(f"policy:{policy_id}"):
                logger.info(f"Training policy {policy_id} with dataset {dataset_id}")

                # Simulate training
                # In production: call offline_policy_learning module
                import time
                time.sleep(5)  # Simulate work

                result = {
                    'policy_id': policy_id,
                    'status': 'completed',
                    'metrics': {'auc': 0.85}
                }

                # Transition to SUCCEEDED
                await JobStateManager.transition(
                    job_id,
                    JobStatus.RUNNING,
                    JobStatus.SUCCEEDED,
                    metadata=result
                )

                return result

        except Exception as e:
            # Transition to RETRYING or FAILED
            if self.request.retries < self.max_retries:
                await JobStateManager.transition(
                    job_id,
                    JobStatus.RUNNING,
                    JobStatus.RETRYING,
                    metadata={'error': str(e), 'retry': self.request.retries}
                )
                raise self.retry(exc=e)
            else:
                await JobStateManager.transition(
                    job_id,
                    JobStatus.RUNNING,
                    JobStatus.FAILED,
                    metadata={'error': str(e)}
                )
                raise

    # Run async function
    return asyncio.run(_execute())


@celery_app.task(base=IdempotentTask, bind=True, queue='light', priority=7)
def generate_visualization_task(self,
                                figure_id: str,
                                data: Dict,
                                idempotency_key: Optional[str] = None):
    """
    Light task: Generate visualization

    Higher priority for UI responsiveness
    """
    logger.info(f"Generating visualization {figure_id}")

    # Simulate work
    import time
    time.sleep(1)

    return {
        'figure_id': figure_id,
        'status': 'completed',
        'url': f's3://figures/{figure_id}.png'
    }


@celery_app.task(base=IdempotentTask, bind=True, queue='realtime', priority=10)
def realtime_recommendation_task(self,
                                 user_id: str,
                                 context: Dict,
                                 idempotency_key: Optional[str] = None):
    """
    Realtime task: Generate recommendation for UI

    Highest priority, fastest queue
    """
    logger.info(f"Generating recommendation for user {user_id}")

    return {
        'user_id': user_id,
        'recommendation': 'treatment_a',
        'confidence': 0.92
    }


# Dead Letter Queue handler
@celery_app.task
def handle_failed_task(task_id: str, exception: str, traceback: str):
    """
    Handle tasks that exceeded max retries

    Sends to Dead Letter Queue for manual inspection
    """
    logger.error(f"Task {task_id} failed permanently: {exception}")

    # Store in DLQ
    # In production: send to monitoring, create alert

    return {'task_id': task_id, 'dlq': True}
