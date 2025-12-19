"""
Structured logging for jobs.

Logs are written to both database (JobLog table) and can be published
to Redis pub/sub for real-time streaming via WebSocket.
"""

import os
import time
import json
import logging
from typing import Optional
from sqlalchemy.orm import Session

from db.models import JobLog

# Redis client for pub/sub (optional, for Phase B+)
_redis_client = None


def get_redis_client():
    """Get or create Redis client for pub/sub."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            _redis_client = redis.from_url(redis_url, decode_responses=True)
        except ImportError:
            # Redis not available, pub/sub disabled
            pass
    return _redis_client


def log_job_message(
    db: Session,
    job_id: str,
    level: str,
    message: str,
    publish_to_redis: bool = True,
):
    """
    Log a message for a job.
    
    Args:
        db: Database session
        job_id: Job ID
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        publish_to_redis: Whether to publish to Redis pub/sub
    """
    # Write to database
    log_entry = JobLog(
        job_id=job_id,
        timestamp=int(time.time()),
        level=level.upper(),
        message=message,
        line_number=None,
    )
    db.add(log_entry)
    db.commit()
    
    # Publish to Redis pub/sub for WebSocket streaming
    if publish_to_redis:
        redis_client = get_redis_client()
        if redis_client:
            try:
                channel = f"job_logs:{job_id}"
                payload = {
                    "job_id": job_id,
                    "timestamp": log_entry.timestamp,
                    "level": level.upper(),
                    "message": message,
                }
                redis_client.publish(channel, json.dumps(payload))
            except Exception as e:
                # Fail silently if Redis pub/sub fails
                logging.warning(f"Failed to publish log to Redis: {e}")


def get_job_logs(
    db: Session,
    job_id: str,
    limit: int = 100,
    offset: int = 0,
    level: Optional[str] = None,
) -> list:
    """
    Get logs for a job.
    
    Args:
        db: Database session
        job_id: Job ID
        limit: Maximum number of logs to return
        offset: Offset for pagination
        level: Filter by log level (optional)
        
    Returns:
        List of log entries as dictionaries
    """
    query = db.query(JobLog).filter(JobLog.job_id == job_id)
    
    if level:
        query = query.filter(JobLog.level == level.upper())
    
    logs = query.order_by(JobLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "job_id": log.job_id,
            "timestamp": log.timestamp,
            "level": log.level,
            "message": log.message,
            "line_number": log.line_number,
        }
        for log in logs
    ]

