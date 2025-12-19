"""
Storage configuration for MistralTune.

Supports S3-compatible storage (AWS S3, MinIO) with local filesystem fallback.
"""

import os
from pathlib import Path
from typing import Optional


class StorageConfig:
    """Storage configuration."""
    
    def __init__(self):
        # S3/MinIO configuration
        self.s3_endpoint_url = os.getenv("S3_ENDPOINT_URL") or os.getenv("MINIO_ENDPOINT_URL")
        self.s3_access_key_id = os.getenv("S3_ACCESS_KEY_ID") or os.getenv("MINIO_ACCESS_KEY_ID", "minioadmin")
        self.s3_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY") or os.getenv("MINIO_SECRET_ACCESS_KEY", "minioadmin")
        self.s3_region = os.getenv("S3_REGION", "us-east-1")
        self.s3_bucket_datasets = os.getenv("S3_BUCKET_DATASETS", "mistraltune-datasets")
        self.s3_bucket_artifacts = os.getenv("S3_BUCKET_ARTIFACTS", "mistraltune-artifacts")
        self.s3_bucket_logs = os.getenv("S3_BUCKET_LOGS", "mistraltune-logs")
        
        # Use S3 if endpoint is configured, otherwise use local filesystem
        self.use_s3 = bool(self.s3_endpoint_url or os.getenv("AWS_S3_ENDPOINT_URL"))
        
        # Local storage paths (fallback)
        self.local_datasets_path = Path("data/storage/datasets")
        self.local_artifacts_path = Path("data/storage/artifacts")
        self.local_logs_path = Path("data/storage/logs")


def get_storage_config() -> StorageConfig:
    """Get storage configuration."""
    return StorageConfig()

