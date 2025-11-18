"""
Celery Application Configuration

分散ジョブ実行のためのCelery設定
"""
from celery import Celery
import os

# Celery app初期化
celery_app = Celery(
    "cqox",
    broker=os.getenv("CELERY_BROKER_URL", "amqp://cqox:cqox_dev_password@rabbitmq:5672//"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2"),
    include=[
        "cqox.tasks.analysis_tasks",  # Added for causal analysis
        "cqox.tasks.causal_tasks",
        "cqox.tasks.policy_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tokyo",
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    
    # Result backend
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster"
    },
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Task routing - all tasks go to default "celery" queue for now
    task_routes={
        "cqox.tasks.*": {"queue": "celery"},
    },
    
    # Idempotency - task deduplication
    task_default_retry_delay=30,  # 30 seconds
    task_max_retries=3,
    
    # Beat schedule (periodic tasks)
    beat_schedule={
        "cleanup-old-tasks": {
            "task": "cqox.tasks.maintenance.cleanup_old_tasks",
            "schedule": 3600.0,  # Every hour
        },
    },
)

# Task annotations for better monitoring
celery_app.conf.task_annotations = {
    "*": {
        "rate_limit": "100/m",  # 100 tasks per minute
    }
}
