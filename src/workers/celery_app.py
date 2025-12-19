"""
Celery application configuration for MistralTune.

Handles job queue management with Redis as broker and result backend.
"""

import os
from pathlib import Path
import sys

from celery import Celery
from celery.schedules import crontab

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Get Redis URL from environment or use default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Create Celery app
celery_app = Celery(
    "mistraltune",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["workers.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600 * 24,  # 24 hours max per task
    task_soft_time_limit=3600 * 23,  # 23 hours soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
    task_routes={
        "workers.tasks.execute_mistral_api_job": {"queue": "mistral_api"},
        "workers.tasks.execute_qlora_job": {"queue": "qlora_local"},
    },
    task_default_queue="default",
    task_default_exchange="tasks",
    task_default_exchange_type="direct",
    task_default_routing_key="default",
    result_expires=3600,  # Results expire after 1 hour
    task_ignore_result=False,  # Store task results
)

# Beat schedule for periodic tasks (if needed in future)
celery_app.conf.beat_schedule = {
    # Example: Clean up old jobs daily at 2 AM
    # "cleanup-old-jobs": {
    #     "task": "workers.tasks.cleanup_old_jobs",
    #     "schedule": crontab(hour=2, minute=0),
    # },
}

