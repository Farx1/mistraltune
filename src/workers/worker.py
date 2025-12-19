#!/usr/bin/env python3
"""
Celery worker entry point for MistralTune.

Run this script to start a Celery worker that will process fine-tuning jobs.

Usage:
    python -m workers.worker
    # or
    celery -A workers.celery_app worker --loglevel=info
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workers.celery_app import celery_app

if __name__ == "__main__":
    # Start Celery worker
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--concurrency=2",  # Number of worker processes
        "--queues=mistral_api,qlora_local,default",  # Listen to all queues
    ])

