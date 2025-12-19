"""
Dataset versioning for MistralTune.

Handles immutable dataset versions with SHA256 hashing.
"""

import hashlib
import time
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from db.models import Dataset, DatasetVersion
from storage.s3_client import get_storage_client


def compute_dataset_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of a dataset file.
    
    Args:
        file_path: Path to dataset file
        
    Returns:
        SHA256 hash as hex string
    """
    storage_client = get_storage_client()
    return storage_client.compute_file_hash(file_path)


def create_dataset_version(
    db: Session,
    dataset_id: str,
    file_path: Path,
    s3_key: Optional[str] = None,
) -> DatasetVersion:
    """
    Create a new dataset version.
    
    Args:
        db: Database session
        dataset_id: Dataset ID
        file_path: Path to dataset file
        s3_key: Optional S3 key if already uploaded
        
    Returns:
        Created DatasetVersion object
    """
    # Compute hash
    file_hash = compute_dataset_hash(file_path)
    
    # Get current max version for this dataset
    max_version = db.query(DatasetVersion.version).filter(
        DatasetVersion.dataset_id == dataset_id
    ).order_by(DatasetVersion.version.desc()).first()
    
    new_version = (max_version[0] + 1) if max_version else 1
    
    # Upload to storage if not already uploaded
    if not s3_key:
        storage_client = get_storage_client()
        version_key = f"{dataset_id}/v{new_version}/{file_path.name}"
        s3_key = storage_client.upload_file(file_path, version_key, bucket_type="datasets")
    
    # Create version record
    version = DatasetVersion(
        id=f"{dataset_id}_v{new_version}",
        dataset_id=dataset_id,
        version=new_version,
        file_hash=file_hash,
        s3_key=s3_key,
        created_at=int(time.time()),
    )
    db.add(version)
    db.commit()
    
    return version


def get_dataset_versions(
    db: Session,
    dataset_id: str,
    limit: int = 100,
) -> list:
    """
    Get versions for a dataset.
    
    Args:
        db: Database session
        dataset_id: Dataset ID
        limit: Maximum number of versions to return
        
    Returns:
        List of DatasetVersion objects
    """
    versions = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id
    ).order_by(DatasetVersion.version.desc()).limit(limit).all()
    
    return [
        {
            "id": v.id,
            "dataset_id": v.dataset_id,
            "version": v.version,
            "file_hash": v.file_hash,
            "s3_key": v.s3_key,
            "created_at": v.created_at,
        }
        for v in versions
    ]

