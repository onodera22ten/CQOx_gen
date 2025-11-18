"""
Prometheus metrics instrumentation

RED Metrics (Rate, Errors, Duration):
- Request rate
- Error rate
- Request duration

Business Metrics:
- Model training duration
- Policy evaluation success rate
- Cache hit rate
"""
from prometheus_client import Counter, Histogram, Gauge, Summary, Info
from prometheus_client import generate_latest, REGISTRY, CONTENT_TYPE_LATEST
from functools import wraps
import time
from typing import Callable
from loguru import logger


# HTTP Metrics (RED)
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint']
)

# Model Training Metrics
model_training_duration_seconds = Histogram(
    'model_training_duration_seconds',
    'Model training duration in seconds',
    ['estimator', 'dataset'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1200, 1800)
)

model_training_total = Counter(
    'model_training_total',
    'Total model training jobs',
    ['estimator', 'status']
)

model_training_in_progress = Gauge(
    'model_training_in_progress',
    'Model training jobs currently in progress',
    ['estimator']
)

# Causal Inference Metrics
cate_estimation_duration_seconds = Histogram(
    'cate_estimation_duration_seconds',
    'CATE estimation duration in seconds',
    ['estimator'],
    buckets=(.1, .5, 1, 2.5, 5, 10, 30, 60)
)

ate_estimation_value = Gauge(
    'ate_estimation_value',
    'Average Treatment Effect estimation value',
    ['estimator', 'dataset']
)

# Diagnostic Metrics
diagnostic_execution_duration_seconds = Histogram(
    'diagnostic_execution_duration_seconds',
    'Diagnostic execution duration in seconds',
    ['diagnostic_type'],
    buckets=(.01, .05, .1, .5, 1, 2.5, 5, 10)
)

diagnostic_score = Gauge(
    'diagnostic_score',
    'Diagnostic test score',
    ['diagnostic_type', 'model_run_id']
)

cas_score = Gauge(
    'cas_score',
    'Causal Assurance Score (CAS)',
    ['model_run_id']
)

# Policy Metrics
policy_evaluation_duration_seconds = Histogram(
    'policy_evaluation_duration_seconds',
    'Policy evaluation duration in seconds',
    ['policy_id', 'method'],
    buckets=(.1, .5, 1, 2.5, 5, 10, 30, 60)
)

policy_value = Gauge(
    'policy_value',
    'Estimated policy value',
    ['policy_id']
)

policy_roi = Gauge(
    'policy_roi',
    'Policy ROI',
    ['policy_id']
)

# Cache Metrics
cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'status']
)

cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate (0-1)'
)

# Database Metrics
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=(.001, .005, .01, .025, .05, .1, .25, .5, 1.0)
)

db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

# Celery Metrics
celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1200, 1800, 3600)
)

celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)

celery_queue_length = Gauge(
    'celery_queue_length',
    'Celery queue length',
    ['queue_name']
)

# System Info
app_info = Info(
    'cqox_app',
    'CQOx application information'
)

# Set app info
app_info.info({
    'version': '1.0.0',
    'estimators': '7',
    'diagnostics': '14',
    'visualizations': '7'
})

# Aliases for backward compatibility
REQUEST_COUNT = http_requests_total
REQUEST_DURATION = http_request_duration_seconds
REQUEST_IN_PROGRESS = http_requests_in_progress


# Helper function for metrics endpoint
def get_metrics_handler():
    """Get metrics handler for FastAPI"""
    return get_metrics, get_metrics_content_type


# Decorators for automatic instrumentation
def track_http_request(endpoint: str):
    """Decorator to track HTTP requests"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            method = kwargs.get('request').method if 'request' in kwargs else 'UNKNOWN'

            http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

            start = time.time()
            status = 200

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start

                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)

                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()

                http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

        return wrapper
    return decorator


def track_model_training(estimator: str, dataset: str):
    """Decorator to track model training"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            model_training_in_progress.labels(estimator=estimator).inc()

            start = time.time()
            status = 'success'

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'failure'
                raise
            finally:
                duration = time.time() - start

                model_training_duration_seconds.labels(
                    estimator=estimator,
                    dataset=dataset
                ).observe(duration)

                model_training_total.labels(
                    estimator=estimator,
                    status=status
                ).inc()

                model_training_in_progress.labels(estimator=estimator).dec()

        return wrapper
    return decorator


def track_diagnostic(diagnostic_type: str):
    """Decorator to track diagnostic execution"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start

                diagnostic_execution_duration_seconds.labels(
                    diagnostic_type=diagnostic_type
                ).observe(duration)

        return wrapper
    return decorator


def track_celery_task(task_name: str):
    """Decorator to track Celery task execution"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            status = 'success'

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'failure'
                raise
            finally:
                duration = time.time() - start

                celery_task_duration_seconds.labels(
                    task_name=task_name
                ).observe(duration)

                celery_tasks_total.labels(
                    task_name=task_name,
                    status=status
                ).inc()

        return wrapper
    return decorator


# Metrics endpoint for Prometheus scraping
def get_metrics() -> bytes:
    """Get Prometheus metrics in text format"""
    return generate_latest(REGISTRY)


def get_metrics_content_type() -> str:
    """Get content type for Prometheus metrics"""
    return CONTENT_TYPE_LATEST
