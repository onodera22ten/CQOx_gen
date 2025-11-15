"""
Celery application configuration
"""
from celery import Celery
from cqox.config import settings

app = Celery(
    'cqox',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['cqox.tasks.causal_tasks', 'cqox.tasks.policy_tasks']
)

# Configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
)

if __name__ == '__main__':
    app.start()
