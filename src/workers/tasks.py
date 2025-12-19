"""
Celery tasks for executing fine-tuning jobs.

Tasks run in separate worker processes, allowing long-running jobs
to execute without blocking the FastAPI server.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any

from celery import Task
from celery.utils.log import get_task_logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workers.celery_app import celery_app
from db.database import SessionLocal
from db.models import Job
from jobs.logging import log_job_message
from jobs.state_machine import JobState, update_job_status
from mistral_api_finetune import get_job_status

logger = get_task_logger(__name__)


class DatabaseTask(Task):
    """Base task class that provides database session."""

    _db = None

    @property
    def db(self):
        """Get or create database session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Close database session after task completes."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True, name="workers.tasks.execute_mistral_api_job")
def execute_mistral_api_job(self, job_id: str):
    """
    Execute a Mistral API fine-tuning job.
    
    This task:
    1. Polls Mistral API for job status
    2. Updates job status in database
    3. Logs progress to JobLog table
    4. Streams logs via Redis pub/sub (for WebSocket forwarding)
    
    Args:
        job_id: The job ID to execute
    """
    db = self.db
    logger.info(f"Starting Mistral API job: {job_id}")
    
    try:
        # Get job from database
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database")
            return
        
        # Update status to RUNNING
        update_job_status(db, job_id, JobState.RUNNING.value)
        log_job_message(db, job_id, "INFO", f"Job {job_id} started")
        
        # Get Mistral client
        from api.main import get_mistral_client
        client = get_mistral_client()
        
        # Poll for job completion
        log_job_message(db, job_id, "INFO", "Polling Mistral API for job status...")
        
        # Use a simplified polling approach (can be enhanced)
        max_polls = 720  # 1 hour max (5 second intervals)
        poll_count = 0
        
        # Status mapping from Mistral (lowercase) to our states (uppercase)
        status_map = {
            "validated": JobState.QUEUED.value,
            "queued": JobState.QUEUED.value,
            "running": JobState.RUNNING.value,
            "succeeded": JobState.SUCCEEDED.value,
            "failed": JobState.FAILED.value,
            "cancelled": JobState.CANCELLED.value,
        }
        
        while poll_count < max_polls:
            # Check if task was revoked
            if self.is_aborted():
                update_job_status(db, job_id, JobState.CANCELLED.value)
                log_job_message(db, job_id, "WARNING", "Job cancelled by user")
                return
            
            # Get current status from Mistral API
            try:
                status_info = get_job_status(client, job_id)
                mistral_status = status_info["status"].lower()
                current_status = status_map.get(mistral_status, mistral_status.upper())
                
                # Update job in database using state machine
                update_job_status(
                    db,
                    job_id,
                    current_status,
                    error_message=str(status_info.get("error")) if status_info.get("error") else None,
                    model_output_ref=status_info.get("fine_tuned_model"),
                )
                
                # Log status update
                log_job_message(db, job_id, "INFO", f"Status: {current_status}")
                
                # Check if job is complete
                if current_status in [JobState.SUCCEEDED.value, JobState.FAILED.value, JobState.CANCELLED.value]:
                    job = db.query(Job).filter(Job.id == job_id).first()
                    if current_status == JobState.SUCCEEDED.value:
                        log_job_message(db, job_id, "INFO", f"Job completed successfully. Model: {job.model_output_ref}")
                    elif current_status == JobState.FAILED.value:
                        log_job_message(db, job_id, "ERROR", f"Job failed: {job.error_message}")
                    else:
                        log_job_message(db, job_id, "WARNING", "Job was cancelled")
                    
                    return
                
                poll_count += 1
                time.sleep(5)  # Poll every 5 seconds
                
            except Exception as e:
                logger.error(f"Error polling job {job_id}: {e}")
                log_job_message(db, job_id, "ERROR", f"Error polling status: {str(e)}")
                time.sleep(5)
                poll_count += 1
        
        # Timeout
        update_job_status(
            db,
            job_id,
            JobState.FAILED.value,
            error_message="Job polling timeout (exceeded 1 hour)",
        )
        log_job_message(db, job_id, "ERROR", "Job polling timeout")
        
    except Exception as e:
        logger.error(f"Error executing job {job_id}: {e}")
        # Update job status to failed
        try:
            update_job_status(
                db,
                job_id,
                JobState.FAILED.value,
                error_message=str(e),
            )
            log_job_message(db, job_id, "ERROR", f"Job execution failed: {str(e)}")
        except Exception as update_error:
            logger.error(f"Failed to update job status: {update_error}")
        raise


@celery_app.task(base=DatabaseTask, bind=True, name="workers.tasks.execute_qlora_job")
def execute_qlora_job(self, job_id: str):
    """
    Execute a local QLoRA fine-tuning job.
    
    This task:
    1. Runs QLoRA training script
    2. Captures logs and saves to JobLog table
    3. Saves adapters to storage (S3 in Phase C)
    4. Updates job status
    
    Args:
        job_id: The job ID to execute
    """
    db = self.db
    logger.info(f"Starting QLoRA job: {job_id}")
    
    try:
        # Get job from database
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database")
            return
        
        # Update status to RUNNING
        job.status = "RUNNING"
        job.started_at = int(time.time())
        db.commit()
        log_job_message(db, job_id, "INFO", f"QLoRA job {job_id} started")
        
        # TODO: Implement QLoRA execution
        # This will be implemented in Phase B completion
        # For now, mark as not implemented
        update_job_status(
            db,
            job_id,
            JobState.FAILED.value,
            error_message="QLoRA local execution not yet implemented in worker",
        )
        log_job_message(db, job_id, "ERROR", "QLoRA execution not implemented")
        
    except Exception as e:
        logger.error(f"Error executing QLoRA job {job_id}: {e}")
        try:
            update_job_status(
                db,
                job_id,
                JobState.FAILED.value,
                error_message=str(e),
            )
            log_job_message(db, job_id, "ERROR", f"QLoRA job execution failed: {str(e)}")
        except Exception as update_error:
            logger.error(f"Failed to update job status: {update_error}")
        raise

