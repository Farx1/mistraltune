"""
S3-compatible storage client for MistralTune.

Supports AWS S3, MinIO, and local filesystem fallback.
"""

import os
import hashlib
from pathlib import Path
from typing import Optional, BinaryIO
from io import BytesIO

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from .config import StorageConfig, get_storage_config


class StorageClient:
    """Storage client for datasets, artifacts, and logs."""
    
    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or get_storage_config()
        self.s3_client = None
        
        if self.config.use_s3 and BOTO3_AVAILABLE:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    endpoint_url=self.config.s3_endpoint_url,
                    aws_access_key_id=self.config.s3_access_key_id,
                    aws_secret_access_key=self.config.s3_secret_access_key,
                    region_name=self.config.s3_region,
                )
                # Ensure buckets exist
                self._ensure_buckets()
            except Exception as e:
                print(f"Warning: Failed to initialize S3 client: {e}. Using local filesystem.")
                self.s3_client = None
    
    def _ensure_buckets(self):
        """Ensure S3 buckets exist."""
        if not self.s3_client:
            return
        
        buckets = [
            self.config.s3_bucket_datasets,
            self.config.s3_bucket_artifacts,
            self.config.s3_bucket_logs,
        ]
        
        for bucket in buckets:
            try:
                self.s3_client.head_bucket(Bucket=bucket)
            except ClientError:
                # Bucket doesn't exist, create it
                try:
                    self.s3_client.create_bucket(Bucket=bucket)
                except Exception as e:
                    print(f"Warning: Failed to create bucket {bucket}: {e}")
    
    def upload_file(self, file_path: Path, s3_key: str, bucket_type: str = "datasets") -> str:
        """
        Upload a file to storage.
        
        Args:
            file_path: Local file path
            s3_key: S3 object key (path in bucket)
            bucket_type: Type of bucket (datasets, artifacts, logs)
            
        Returns:
            Storage key/path for the uploaded file
        """
        if self.s3_client:
            bucket = {
                "datasets": self.config.s3_bucket_datasets,
                "artifacts": self.config.s3_bucket_artifacts,
                "logs": self.config.s3_bucket_logs,
            }.get(bucket_type, self.config.s3_bucket_datasets)
            
            try:
                self.s3_client.upload_file(str(file_path), bucket, s3_key)
                return f"s3://{bucket}/{s3_key}"
            except Exception as e:
                raise Exception(f"Failed to upload to S3: {e}")
        else:
            # Local filesystem fallback
            local_path = {
                "datasets": self.config.local_datasets_path,
                "artifacts": self.config.local_artifacts_path,
                "logs": self.config.local_logs_path,
            }.get(bucket_type, self.config.local_datasets_path)
            
            target_path = local_path / s3_key
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(file_path, target_path)
            # Return absolute path or relative path depending on context
            try:
                return str(target_path.relative_to(Path.cwd()))
            except ValueError:
                return str(target_path)
    
    def upload_bytes(self, data: bytes, s3_key: str, bucket_type: str = "datasets") -> str:
        """
        Upload bytes data to storage.
        
        Args:
            data: Bytes data to upload
            s3_key: S3 object key
            bucket_type: Type of bucket
            
        Returns:
            Storage key/path
        """
        if self.s3_client:
            bucket = {
                "datasets": self.config.s3_bucket_datasets,
                "artifacts": self.config.s3_bucket_artifacts,
                "logs": self.config.s3_bucket_logs,
            }.get(bucket_type, self.config.s3_bucket_datasets)
            
            try:
                self.s3_client.put_object(Bucket=bucket, Key=s3_key, Body=data)
                return f"s3://{bucket}/{s3_key}"
            except Exception as e:
                raise Exception(f"Failed to upload to S3: {e}")
        else:
            # Local filesystem fallback
            local_path = {
                "datasets": self.config.local_datasets_path,
                "artifacts": self.config.local_artifacts_path,
                "logs": self.config.local_logs_path,
            }.get(bucket_type, self.config.local_datasets_path)
            
            target_path = local_path / s3_key
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_path, "wb") as f:
                f.write(data)
            
            # Return absolute path or relative path depending on context
            try:
                return str(target_path.relative_to(Path.cwd()))
            except ValueError:
                return str(target_path)
    
    def download_file(self, s3_key: str, local_path: Path, bucket_type: str = "datasets") -> Path:
        """
        Download a file from storage.
        
        Args:
            s3_key: S3 object key or local path
            local_path: Where to save the file locally
            bucket_type: Type of bucket
            
        Returns:
            Path to downloaded file
        """
        if s3_key.startswith("s3://"):
            # Parse S3 URI
            parts = s3_key.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else ""
            
            if self.s3_client:
                try:
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    self.s3_client.download_file(bucket, key, str(local_path))
                    return local_path
                except Exception as e:
                    raise Exception(f"Failed to download from S3: {e}")
        
        # Local filesystem path
        source_path = Path(s3_key)
        if source_path.exists():
            import shutil
            local_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, local_path)
            return local_path
        else:
            raise FileNotFoundError(f"File not found: {s3_key}")
    
    def delete_file(self, s3_key: str, bucket_type: str = "datasets") -> bool:
        """
        Delete a file from storage.
        
        Args:
            s3_key: S3 object key or local path
            bucket_type: Type of bucket
            
        Returns:
            True if deleted, False otherwise
        """
        if s3_key.startswith("s3://"):
            parts = s3_key.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else ""
            
            if self.s3_client:
                try:
                    self.s3_client.delete_object(Bucket=bucket, Key=key)
                    return True
                except Exception as e:
                    print(f"Failed to delete from S3: {e}")
                    return False
        
        # Local filesystem
        file_path = Path(s3_key)
        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except Exception as e:
                print(f"Failed to delete local file: {e}")
                return False
        
        return False
    
    def compute_file_hash(self, file_path: Path) -> str:
        """
        Compute SHA256 hash of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 hash as hex string
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def compute_bytes_hash(self, data: bytes) -> str:
        """
        Compute SHA256 hash of bytes data.
        
        Args:
            data: Bytes data
            
        Returns:
            SHA256 hash as hex string
        """
        return hashlib.sha256(data).hexdigest()


# Global storage client instance
_storage_client: Optional[StorageClient] = None


def get_storage_client() -> StorageClient:
    """Get or create storage client."""
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient()
    return _storage_client

