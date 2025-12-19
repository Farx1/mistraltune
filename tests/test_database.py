"""
Tests for database models and operations.
"""

import pytest
import time
from src.db.models import Job, Dataset, DatasetVersion, JobLog, User
from src.jobs.state_machine import JobState, validate_state_transition, update_job_status


def test_job_model_creation(test_db):
    """Test creating a Job model."""
    job = Job(
        id="test_job_1",
        job_type="mistral_api",
        model="open-mistral-7b",
        status=JobState.PENDING.value,
        created_at=int(time.time()),
    )
    test_db.add(job)
    test_db.commit()
    
    # Retrieve and verify
    retrieved = test_db.query(Job).filter(Job.id == "test_job_1").first()
    assert retrieved is not None
    assert retrieved.job_type == "mistral_api"
    assert retrieved.model == "open-mistral-7b"
    assert retrieved.status == JobState.PENDING.value


def test_dataset_model_creation(test_db):
    """Test creating a Dataset model."""
    dataset = Dataset(
        id="test_dataset_1",
        filename="test.jsonl",
        file_hash="abc123",
        size_bytes=1024,
        uploaded_at=int(time.time()),
        metadata_json={"num_samples": 10},
    )
    test_db.add(dataset)
    test_db.commit()
    
    # Retrieve and verify
    retrieved = test_db.query(Dataset).filter(Dataset.id == "test_dataset_1").first()
    assert retrieved is not None
    assert retrieved.filename == "test.jsonl"
    assert retrieved.file_hash == "abc123"
    assert retrieved.metadata_json["num_samples"] == 10


def test_dataset_version_creation(test_db):
    """Test creating a DatasetVersion."""
    # First create a dataset
    dataset = Dataset(
        id="test_dataset_1",
        filename="test.jsonl",
        uploaded_at=int(time.time()),
    )
    test_db.add(dataset)
    test_db.commit()
    
    # Create version
    version = DatasetVersion(
        id="test_dataset_1_v1",
        dataset_id="test_dataset_1",
        version=1,
        file_hash="abc123",
        created_at=int(time.time()),
    )
    test_db.add(version)
    test_db.commit()
    
    # Verify relationship
    retrieved = test_db.query(DatasetVersion).filter(DatasetVersion.id == "test_dataset_1_v1").first()
    assert retrieved is not None
    assert retrieved.dataset.filename == "test.jsonl"


def test_job_log_creation(test_db):
    """Test creating a JobLog."""
    # First create a job
    job = Job(
        id="test_job_1",
        job_type="mistral_api",
        model="open-mistral-7b",
        status=JobState.PENDING.value,
        created_at=int(time.time()),
    )
    test_db.add(job)
    test_db.commit()
    
    # Create log
    log = JobLog(
        job_id="test_job_1",
        timestamp=int(time.time()),
        level="INFO",
        message="Test log message",
    )
    test_db.add(log)
    test_db.commit()
    
    # Verify relationship
    retrieved = test_db.query(JobLog).filter(JobLog.job_id == "test_job_1").first()
    assert retrieved is not None
    assert retrieved.job.id == "test_job_1"
    assert retrieved.message == "Test log message"


def test_job_to_dict(test_db):
    """Test Job.to_dict() method."""
    job = Job(
        id="test_job_1",
        job_type="mistral_api",
        model="open-mistral-7b",
        status=JobState.SUCCEEDED.value,
        created_at=int(time.time()),
        model_output_ref="ft:model:123",
        error_message=None,
        config_json={"learning_rate": 1e-4},
        metrics_json={"loss": 0.5},
    )
    test_db.add(job)
    test_db.commit()
    
    job_dict = job.to_dict()
    assert job_dict["id"] == "test_job_1"
    assert job_dict["status"] == JobState.SUCCEEDED.value
    assert job_dict["fine_tuned_model"] == "ft:model:123"
    assert job_dict["config"] == {"learning_rate": 1e-4}


def test_dataset_to_dict(test_db):
    """Test Dataset.to_dict() method."""
    dataset = Dataset(
        id="test_dataset_1",
        filename="test.jsonl",
        uploaded_at=int(time.time()),
        size_bytes=1024,
        metadata_json={"num_samples": 10},
    )
    test_db.add(dataset)
    test_db.commit()
    
    dataset_dict = dataset.to_dict()
    assert dataset_dict["id"] == "test_dataset_1"
    assert dataset_dict["filename"] == "test.jsonl"
    assert dataset_dict["name"] == "test.jsonl"
    assert dataset_dict["size_bytes"] == 1024


def test_state_transition_validation():
    """Test job state transition validation."""
    # Valid transitions
    assert validate_state_transition(JobState.PENDING.value, JobState.QUEUED.value) is True
    assert validate_state_transition(JobState.QUEUED.value, JobState.RUNNING.value) is True
    assert validate_state_transition(JobState.RUNNING.value, JobState.SUCCEEDED.value) is True
    
    # Invalid transitions
    assert validate_state_transition(JobState.SUCCEEDED.value, JobState.RUNNING.value) is False
    assert validate_state_transition(JobState.PENDING.value, JobState.SUCCEEDED.value) is False


def test_update_job_status(test_db):
    """Test update_job_status function."""
    # Create job
    job = Job(
        id="test_job_1",
        job_type="mistral_api",
        model="open-mistral-7b",
        status=JobState.PENDING.value,
        created_at=int(time.time()),
    )
    test_db.add(job)
    test_db.commit()
    
    # Update to QUEUED
    updated = update_job_status(test_db, "test_job_1", JobState.QUEUED.value)
    assert updated.status == JobState.QUEUED.value
    
    # Update to RUNNING
    updated = update_job_status(test_db, "test_job_1", JobState.RUNNING.value)
    assert updated.status == JobState.RUNNING.value
    assert updated.started_at is not None
    
    # Update to SUCCEEDED
    updated = update_job_status(
        test_db,
        "test_job_1",
        JobState.SUCCEEDED.value,
        model_output_ref="ft:model:123",
    )
    assert updated.status == JobState.SUCCEEDED.value
    assert updated.finished_at is not None
    assert updated.model_output_ref == "ft:model:123"

