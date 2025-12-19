"""
Tests for storage functionality.
"""

import pytest
from pathlib import Path
from src.storage.s3_client import StorageClient, get_storage_client
from src.storage.config import StorageConfig


def test_storage_config():
    """Test storage configuration."""
    config = StorageConfig()
    assert config.s3_bucket_datasets == "mistraltune-datasets"
    assert config.s3_bucket_artifacts == "mistraltune-artifacts"
    # Should use local filesystem if S3 not configured
    assert isinstance(config.local_datasets_path, Path)


def test_storage_client_initialization():
    """Test storage client initialization."""
    client = get_storage_client()
    assert client is not None
    assert isinstance(client, StorageClient)


def test_compute_file_hash(temp_data_dir):
    """Test computing file hash."""
    # Create test file
    test_file = temp_data_dir / "test.txt"
    test_file.write_text("Hello, World!")
    
    client = get_storage_client()
    hash_value = client.compute_file_hash(test_file)
    
    assert hash_value is not None
    assert len(hash_value) == 64  # SHA256 hex string length


def test_compute_bytes_hash():
    """Test computing bytes hash."""
    client = get_storage_client()
    data = b"Hello, World!"
    hash_value = client.compute_bytes_hash(data)
    
    assert hash_value is not None
    assert len(hash_value) == 64


def test_upload_and_download_file(temp_data_dir):
    """Test uploading and downloading a file."""
    # Create test file
    test_file = temp_data_dir / "test_upload.txt"
    test_file.write_text("Test content for upload")
    
    client = get_storage_client()
    
    # Upload (will use local filesystem in test)
    storage_key = "test/test_upload.txt"
    stored_path = client.upload_file(test_file, storage_key, bucket_type="datasets")
    
    assert stored_path is not None
    
    # Download
    download_path = temp_data_dir / "downloaded.txt"
    downloaded = client.download_file(stored_path, download_path, bucket_type="datasets")
    
    assert downloaded.exists()
    assert downloaded.read_text() == "Test content for upload"


def test_upload_bytes(temp_data_dir):
    """Test uploading bytes data."""
    client = get_storage_client()
    data = b"Test bytes data"
    storage_key = "test/test_bytes.txt"
    
    stored_path = client.upload_bytes(data, storage_key, bucket_type="datasets")
    assert stored_path is not None
    
    # Verify can download
    download_path = temp_data_dir / "downloaded_bytes.txt"
    downloaded = client.download_file(stored_path, download_path, bucket_type="datasets")
    assert downloaded.read_text() == "Test bytes data"

