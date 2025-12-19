"""Celery workers package for MistralTune."""

from .celery_app import celery_app

__all__ = ["celery_app"]

