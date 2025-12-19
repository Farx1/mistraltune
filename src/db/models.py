"""
SQLAlchemy models for MistralTune.

Defines database schema for jobs, datasets, versions, logs, and users.
"""

from datetime import datetime
from typing import Optional
import json

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Job(Base):
    """Job model for fine-tuning runs."""

    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    job_type = Column(String, nullable=False, index=True)  # mistral_api or qlora_local
    model = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)  # PENDING, QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED
    created_at = Column(Integer, nullable=False, index=True)  # Unix timestamp
    started_at = Column(Integer, nullable=True)  # Unix timestamp
    finished_at = Column(Integer, nullable=True)  # Unix timestamp
    progress = Column(Float, nullable=True)  # 0.0 to 1.0
    error_message = Column(Text, nullable=True)
    config_json = Column(JSON, nullable=True)  # Training config as JSON
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"), nullable=True)
    model_output_ref = Column(String, nullable=True)  # S3 key or path to model artifacts
    metrics_json = Column(JSON, nullable=True)  # Training metrics as JSON
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)  # For Phase E

    # Relationships
    dataset_version = relationship("DatasetVersion", back_populates="jobs")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")
    user = relationship("User", back_populates="jobs")

    def to_dict(self) -> dict:
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "job_type": self.job_type,
            "model": self.model,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.created_at,  # For backward compatibility
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "progress": self.progress,
            "fine_tuned_model": self.model_output_ref,  # For backward compatibility
            "error": self.error_message,  # Return as string, not JSON
            "config": self.config_json,
            "metadata": self.metrics_json,
        }


class Dataset(Base):
    """Dataset model for uploaded training files."""

    __tablename__ = "datasets"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_hash = Column(String, nullable=True, index=True)  # SHA256 hash
    size_bytes = Column(Integer, nullable=True)
    uploaded_at = Column(Integer, nullable=False, index=True)  # Unix timestamp
    metadata_json = Column(JSON, nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)  # For Phase E

    # Relationships
    versions = relationship("DatasetVersion", back_populates="dataset", cascade="all, delete-orphan")
    user = relationship("User", back_populates="datasets")

    def to_dict(self) -> dict:
        """Convert model to dictionary for API responses."""
        result = {
            "id": self.id,
            "filename": self.filename,
            "file_id": self.id,  # For backward compatibility
            "uploaded_at": self.uploaded_at,
            "created_at": self.uploaded_at,  # For backward compatibility
            "size_bytes": self.size_bytes,
        }
        # Add metadata fields if they exist
        if self.metadata_json:
            result["metadata"] = self.metadata_json
            if "num_samples" in self.metadata_json:
                result["num_samples"] = self.metadata_json["num_samples"]
        # Add name field for frontend compatibility
        result["name"] = self.filename
        return result


class DatasetVersion(Base):
    """Dataset version model for immutable dataset versions."""

    __tablename__ = "dataset_versions"

    id = Column(String, primary_key=True, index=True)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)  # Version number
    file_hash = Column(String, nullable=False, index=True)  # SHA256 hash
    s3_key = Column(String, nullable=True)  # S3 object key (for Phase C)
    created_at = Column(Integer, nullable=False, index=True)  # Unix timestamp

    # Relationships
    dataset = relationship("Dataset", back_populates="versions")
    jobs = relationship("Job", back_populates="dataset_version")

    __table_args__ = (
        Index("ix_dataset_versions_dataset_version", "dataset_id", "version", unique=True),
    )


class JobLog(Base):
    """Job log model for structured logging."""

    __tablename__ = "job_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    timestamp = Column(Integer, nullable=False, index=True)  # Unix timestamp
    level = Column(String, nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    line_number = Column(Integer, nullable=True)  # For log ordering

    # Relationships
    job = relationship("Job", back_populates="logs")

    __table_args__ = (
        Index("ix_job_logs_job_timestamp", "job_id", "timestamp"),
    )


class User(Base):
    """User model for authentication (Phase E)."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="member")  # admin or member
    created_at = Column(Integer, nullable=False, index=True)  # Unix timestamp

    # Relationships
    jobs = relationship("Job", back_populates="user")
    datasets = relationship("Dataset", back_populates="user")

