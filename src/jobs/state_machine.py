"""
Job state machine for MistralTune.

Defines valid job states and transitions.
"""

from enum import Enum
from typing import Optional
from sqlalchemy.orm import Session

from db.models import Job


class JobState(str, Enum):
    """Valid job states."""
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


TERMINAL_STATES = {JobState.SUCCEEDED.value, JobState.FAILED.value, JobState.CANCELLED.value}

# Mistral SDK 1.x job statuses -> JobState (lowercase legacy names kept for old rows/mocks)
_MISTRAL_STATUS = {
    "QUEUED": JobState.QUEUED,
    "STARTED": JobState.QUEUED,
    "VALIDATING": JobState.QUEUED,
    "VALIDATED": JobState.QUEUED,
    "RUNNING": JobState.RUNNING,
    "CANCELLATION_REQUESTED": JobState.RUNNING,  # not terminal until Mistral reports CANCELLED
    "SUCCESS": JobState.SUCCEEDED,
    "SUCCEEDED": JobState.SUCCEEDED,
    "FAILED": JobState.FAILED,
    "FAILED_VALIDATION": JobState.FAILED,
    "CANCELLED": JobState.CANCELLED,
}


def from_mistral_status(status: str) -> str:
    """Map a Mistral job status to a JobState value. Unknown statuses count as RUNNING (non-terminal)."""
    return _MISTRAL_STATUS.get(str(status).upper(), JobState.RUNNING).value


# Valid state transitions
VALID_TRANSITIONS = {
    JobState.PENDING: [JobState.QUEUED, JobState.CANCELLED],
    JobState.QUEUED: [JobState.RUNNING, JobState.CANCELLED],
    JobState.RUNNING: [JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED],
    JobState.SUCCEEDED: [],  # Terminal state
    JobState.FAILED: [],  # Terminal state
    JobState.CANCELLED: [],  # Terminal state
}


def validate_state_transition(current_state: str, new_state: str) -> bool:
    """
    Validate if a state transition is allowed.
    
    Args:
        current_state: Current job state
        new_state: Desired new state
        
    Returns:
        True if transition is valid, False otherwise
    """
    try:
        current = JobState(current_state.upper())
        new = JobState(new_state.upper())
    except ValueError:
        return False
    
    # Polling reports the same state many times; that is not a transition
    return new == current or new in VALID_TRANSITIONS.get(current, [])


def update_job_status(
    db: Session,
    job_id: str,
    new_status: str,
    error_message: Optional[str] = None,
    progress: Optional[float] = None,
    model_output_ref: Optional[str] = None,
) -> Job:
    """
    Update job status with validation.
    
    Args:
        db: Database session
        job_id: Job ID
        new_status: New status to set
        error_message: Optional error message
        progress: Optional progress (0.0 to 1.0)
        model_output_ref: Optional model output reference
        
    Returns:
        Updated Job object
        
    Raises:
        ValueError: If state transition is invalid
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError(f"Job {job_id} not found")
    
    # Validate transition
    if not validate_state_transition(job.status, new_status):
        raise ValueError(
            f"Invalid state transition from {job.status} to {new_status}"
        )
    
    # Update job
    job.status = new_status.upper()
    if error_message is not None:
        job.error_message = error_message
    if progress is not None:
        job.progress = progress
    if model_output_ref is not None:
        job.model_output_ref = model_output_ref
    
    # Set timestamps
    import time
    if new_status.upper() == JobState.RUNNING and job.started_at is None:
        job.started_at = int(time.time())
    if new_status.upper() in [JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED]:
        if job.finished_at is None:
            job.finished_at = int(time.time())
    
    db.commit()
    return job

