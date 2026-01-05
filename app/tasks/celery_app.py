"""Celery application configuration."""
from celery import Celery
from app.config import settings

# Create Celery app
celery_app = Celery(
    "payment_gateway",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.transaction_tasks",
        "app.tasks.webhook_tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=5,
)

# Task routing disabled - using default queue for simplicity
# Enable this when you need separate queues for scaling
# celery_app.conf.task_routes = {
#     "app.tasks.transaction_tasks.*": {"queue": "transactions"},
#     "app.tasks.webhook_tasks.*": {"queue": "webhooks"},
# }
